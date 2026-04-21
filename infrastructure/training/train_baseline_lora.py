#!/usr/bin/env python3
"""
Baseline LoRA on full twin_train (uncleaned) — paper "before" reference.
QLoRA + OLoRA + DoRA + LoRA+; 4-bit NF4, bf16 on SM80+.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
# Arrow / temp on volume: fewer surprises on container root; speeds dataset map cache reuse.
_hf = os.environ.get("HF_HOME", "/workspace/hf_cache")
os.environ.setdefault("HF_DATASETS_CACHE", os.path.join(_hf, "datasets"))
os.environ.setdefault("TMPDIR", "/workspace/tmp")

import torch

try:
    import torch._dynamo as _dynamo

    _dynamo.config.disable = True
except Exception:
    pass

# System prompts by task (matches specialist profiles; unknown → identity)
TASK_SYSTEM = {
    "code": "You are a code assistant specializing in Python, Rust, Docker, and AI infrastructure. Write clean, documented code following the project's conventions.",
    "analytical": "You are an analytical reasoning specialist. Provide structured analysis, research synthesis, and strategic recommendations.",
    "identity": "You are Luna (Emmelina Fugler), an AI infrastructure engineer. Respond in Luna's voice — direct, technical, creative, with dry humor.",
    "docs": "You are a technical writer and conversationalist. Write clear documentation and engaging responses.",
    "convo": "You are a technical writer and conversationalist. Write clear documentation and engaging responses.",
}


def default_system(task: str) -> str:
    t = (task or "identity").strip().lower()
    return TASK_SYSTEM.get(t, TASK_SYSTEM["identity"])


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data_path", type=str, default="/workspace/corpus/twin_train_baseline.jsonl")
    p.add_argument("--base_model", type=str, default="/workspace/models/qwen35-4b")
    p.add_argument("--output_dir", type=str, default="/workspace/output/elf-baseline-lora")
    p.add_argument("--metrics_path", type=str, default="/workspace/logs/baseline_metrics.json")
    p.add_argument("--lora_rank", type=int, default=48)
    p.add_argument("--lora_alpha", type=int, default=96)
    p.add_argument("--batch_size", type=int, default=1)
    p.add_argument("--grad_accum", type=int, default=16)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--loraplus_ratio", type=float, default=8.0)
    p.add_argument("--max_seq_length", type=int, default=512)
    p.add_argument("--max_steps", type=int, default=470, help="Full run target steps (pattern-master parity)")
    p.add_argument("--dry-run", action="store_true", dest="dry_run", help="1%% data, 10 steps, print step times")
    p.add_argument(
        "--dataloader_workers",
        type=int,
        default=-1,
        help="DataLoader worker processes (-1: 0 if dry-run else 4)",
    )
    return p.parse_args()


def detect_gpu():
    if not torch.cuda.is_available():
        print("[ERROR] No CUDA GPU.")
        sys.exit(1)
    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    cc_major = torch.cuda.get_device_properties(0).major
    cc_minor = torch.cuda.get_device_properties(0).minor
    sm = cc_major * 10 + cc_minor
    compute_dtype = torch.float16 if sm < 80 else torch.bfloat16
    print(f"[INFO] GPU: {gpu_name} (SM{sm}, {vram_gb:.1f} GB)")
    print(f"[INFO] Compute dtype: {compute_dtype}")
    return compute_dtype, sm, vram_gb


def load_jsonl_rows(path: str):
    rows = []
    skipped = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            instruction = (record.get("instruction") or "").strip()
            completion = (record.get("completion") or "").strip()
            if not instruction or not completion:
                skipped += 1
                continue
            task = record.get("task") or "identity"
            rows.append({"instruction": instruction, "completion": completion, "task": task})
    print(f"[INFO] Loaded {len(rows)} rows (skipped {skipped})")
    if not rows:
        print("[ERROR] No training rows.")
        sys.exit(1)
    return rows


def rows_to_dataset(rows, tokenizer):
    from datasets import Dataset

    examples = []
    for r in rows:
        sp = default_system(r["task"])
        messages = [
            {"role": "system", "content": sp},
            {"role": "user", "content": r["instruction"]},
            {"role": "assistant", "content": r["completion"]},
        ]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        examples.append({"text": text})
    return Dataset.from_list(examples)


def setup_loraplus_optimizer(model, lr: float, loraplus_ratio: float):
    param_groups = []
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if "lora_B" in name:
            param_groups.append({"params": [param], "lr": lr * loraplus_ratio, "name": name})
        else:
            param_groups.append({"params": [param], "lr": lr, "name": name})
    print(f"[INFO] LoRA+ base_lr={lr} B_lr={lr * loraplus_ratio} ratio={loraplus_ratio}")
    return param_groups


def main():
    args = parse_args()
    os.makedirs(os.environ.get("TMPDIR", "/workspace/tmp"), exist_ok=True)
    os.makedirs(os.environ.get("HF_DATASETS_CACHE", "/workspace/hf_cache/datasets"), exist_ok=True)
    compute_dtype, sm, vram_gb = detect_gpu()
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.benchmark = True
    torch.set_float32_matmul_precision("high")

    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainerCallback
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTConfig, SFTTrainer

    class StepTimerCallback(TrainerCallback):
        """Log wall time per training step (first steps only for dry-run diagnosis)."""

        def __init__(self, log_first_n: int = 12):
            super().__init__()
            self.log_first_n = log_first_n
            self._t0 = None
            self.step_times: list[float] = []

        def on_step_begin(self, args, state, control, **kwargs):
            self._t0 = time.perf_counter()

        def on_step_end(self, args, state, control, **kwargs):
            if self._t0 is None:
                return
            dt = time.perf_counter() - self._t0
            if state.global_step <= self.log_first_n:
                self.step_times.append(dt)
                print(f"[INFO] step {state.global_step} wall_s={dt:.2f}")
                if state.global_step == self.log_first_n and dt > 25.0:
                    print(
                        f"[WARN] Step time {dt:.2f}s > 25s — check TORCHDYNAMO_DISABLE and TOKENIZERS_PARALLELISM before import torch"
                    )

    class DivergenceTripwireCallback(TrainerCallback):
        """Abort if train loss blows up vs first logged loss (mixed-task stability)."""

        def __init__(self):
            super().__init__()
            self._initial_loss: float | None = None

        def on_log(self, args, state, control, logs=None, **kwargs):
            logs = logs or {}
            raw = logs.get("loss")
            if raw is None:
                return
            loss = float(raw)
            if self._initial_loss is None:
                self._initial_loss = loss
                print(f"[INFO] divergence_tripwire baseline_loss={self._initial_loss:.4f}", flush=True)
                return
            if state.global_step >= 20 and loss > self._initial_loss * 1.5:
                thr = self._initial_loss * 1.5
                print(
                    f"[DIVERGENCE_DETECTED] step={state.global_step} loss={loss:.4f} "
                    f"baseline={self._initial_loss:.4f} threshold={thr:.4f}",
                    flush=True,
                )
                sys.exit(1)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )

    print(f"[INFO] Loading tokenizer/model from {args.base_model}")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map={"": 0},
        trust_remote_code=True,
        dtype=compute_dtype,
    )
    model.config.torch_dtype = compute_dtype

    # Let SFTTrainer own gradient checkpointing (avoid stacking with manual enable).
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)

    lora_config = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        use_dora=True,
        init_lora_weights="olora",
    )
    model = get_peft_model(model, lora_config)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"[INFO] Trainable: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")

    if compute_dtype == torch.float16:
        bf16_count = 0
        for _, param in model.named_parameters():
            if param.dtype == torch.bfloat16:
                param.data = param.data.to(torch.float16)
                bf16_count += 1
        if bf16_count:
            print(f"[INFO] Cast {bf16_count} bf16 params → fp16")

    rows = load_jsonl_rows(args.data_path)
    if args.dry_run:
        random.seed(42)
        n = max(50, int(0.01 * len(rows)))
        rows = random.sample(rows, min(n, len(rows)))
        print(f"[INFO] Dry-run: using {len(rows)} rows (~1% sample cap)")

    full_ds = rows_to_dataset(rows, tokenizer)
    split = full_ds.train_test_split(test_size=0.1, seed=42)
    train_ds, eval_ds = split["train"], split["test"]
    print(f"[INFO] Train {len(train_ds)} | Eval {len(eval_ds)}")

    param_groups = setup_loraplus_optimizer(model, args.lr, args.loraplus_ratio)
    optimizer = torch.optim.AdamW(param_groups)

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.metrics_path) or ".", exist_ok=True)

    use_fp16 = compute_dtype == torch.float16
    use_bf16 = compute_dtype == torch.bfloat16

    max_steps = 10 if args.dry_run else args.max_steps
    eval_steps = 5 if args.dry_run else max(47, max_steps // 10)
    logging_steps = 1 if args.dry_run else 5

    if args.dataloader_workers < 0:
        dl_workers = 0 if args.dry_run else 4
    else:
        dl_workers = args.dataloader_workers
    dl_prefetch = 2 if dl_workers > 0 else None
    dl_persistent = dl_workers > 0

    training_args = SFTConfig(
        output_dir=args.output_dir,
        max_steps=max_steps,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        weight_decay=0.01,
        fp16=use_fp16,
        bf16=use_bf16,
        logging_steps=logging_steps,
        save_strategy="no",
        eval_strategy="steps",
        eval_steps=eval_steps,
        seed=42,
        max_grad_norm=1.0,
        report_to="none",
        # 32GB 5090: GC off matches proven pattern-master recipe (v4); GC on pushes ~50s/step with grad_accum 16.
        gradient_checkpointing=False,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        dataset_text_field="text",
        max_length=args.max_seq_length,
        packing=False,
        dataloader_num_workers=dl_workers,
        dataloader_prefetch_factor=dl_prefetch,
        dataloader_pin_memory=True,
        dataloader_persistent_workers=dl_persistent,
    )

    timer_cb = StepTimerCallback(log_first_n=12)
    tripwire_cb = DivergenceTripwireCallback()
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=training_args,
        optimizers=(optimizer, None),
        callbacks=[timer_cb, tripwire_cb],
    )

    print(f"[INFO] Starting train max_steps={max_steps} dry_run={args.dry_run}")
    wall0 = time.time()
    result = trainer.train()
    wall = time.time() - wall0

    if args.dry_run and timer_cb.step_times:
        avg = sum(timer_cb.step_times) / len(timer_cb.step_times)
        print(f"[INFO] Dry-run mean step time (first {len(timer_cb.step_times)}): {avg:.2f}s")
        if avg > 25.0:
            print("[ERROR] Mean step > 25s — abort full run until 5090 env is fixed.")
            sys.exit(2)

    lora_path = os.path.join(args.output_dir, "adapter")
    os.makedirs(lora_path, exist_ok=True)
    model.save_pretrained(lora_path)
    tokenizer.save_pretrained(lora_path)

    log_history = trainer.state.log_history
    metrics = {
        "mode": "dry_run" if args.dry_run else "full",
        "base_model": args.base_model,
        "data_path": args.data_path,
        "train_rows": len(train_ds),
        "eval_rows": len(eval_ds),
        "max_steps": max_steps,
        "final_train_loss": result.training_loss,
        "global_step": result.global_step,
        "wall_time_seconds": wall,
        "peak_gpu_gb": torch.cuda.max_memory_allocated() / 1024**3,
        "gpu": torch.cuda.get_device_name(0),
        "compute_dtype": str(compute_dtype),
        "lora_rank": args.lora_rank,
        "lora_alpha": args.lora_alpha,
        "loraplus_ratio": args.loraplus_ratio,
        "dry_run_step_times_sample": timer_cb.step_times[:12],
        "log_history": log_history,
        "env_TORCHDYNAMO_DISABLE": os.environ.get("TORCHDYNAMO_DISABLE"),
        "env_TOKENIZERS_PARALLELISM": os.environ.get("TOKENIZERS_PARALLELISM"),
    }
    with open(args.metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[INFO] Metrics written {args.metrics_path}")
    print(f"[INFO] Adapter {lora_path}")
    print("[INFO] Done.")


if __name__ == "__main__":
    main()
