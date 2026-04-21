# Training pipeline — RTX 5090 spot QLoRA on Vast.ai

This directory contains the actual training scripts used to produce baseline and candidate adapters for the Apr 9–19, 2026 Fellows sprint pilot. The pipeline targets RTX 5090 spot instances on Vast.ai for cost-efficient burst training (~$0.028/hr on the AMD EPYC 7R32 + 5090 + 96 GB RAM + PCIe 4.0 instance the sprint settled on).

## Files

| File | Role |
|---|---|
| `vast_bootstrap_5090.sh` | One-time pod bootstrap. Installs the proven stack and sets the four critical env vars + worker-kill that determine step time on sm_120. |
| `train_baseline_lora.py` | The QLoRA training script. NF4 4-bit + DoRA + LoRA+ + OLoRA init, with a divergence tripwire that kills the run if loss explodes. |
| `start_baseline_train.sh` | Launcher: sources the bootstrap env, activates the venv, runs the training script unbuffered with logs tee'd. |

## The four critical fixes for RTX 5090 (sm_120)

Without these in place before `import torch`, step time is **~88 s/step**. With them, **~18 s/step** — the difference between a $0.46 adapter and a $2.30 adapter on a 470-step run.

1. `TORCHDYNAMO_DISABLE=1` — set in the env before any torch import. The script also re-asserts via `torch._dynamo.config.disable = True` for belt-and-suspenders.
2. `TOKENIZERS_PARALLELISM=false` — same. Prevents fork-related stalls in HF datasets `map`.
3. `dataloader_pin_memory=True` in `SFTConfig` — pins CPU staging buffers so transfer-to-GPU doesn't block.
4. `pkill -f torch.compile` / `pkill -f triton_autotune` in bootstrap — prevents stale compile workers from stealing CPU during step launches.

These are recorded as `env_TORCHDYNAMO_DISABLE` and `env_TOKENIZERS_PARALLELISM` in the metrics JSON written at the end of every run, so the run log carries proof it was set correctly.

## The divergence tripwire (`DivergenceTripwireCallback`)

QLoRA on a mixed-task corpus is sensitive to the LoRA+ B-matrix learning rate. The first sprint pod ran with `--loraplus_ratio 16.0` and **loss climbed 2.5 → 9.5 in 100 steps**, with token accuracy crashing 51% → 5%. Classic catastrophic forgetting from a too-hot B-matrix LR on heterogeneous training data.

The tripwire catches this without operator intervention:

- Records the first logged loss as `_initial_loss` baseline.
- After step ≥ 20, if loss exceeds `baseline × 1.5`, emits `[DIVERGENCE_DETECTED]` and `sys.exit(1)`.
- Dry-run mode (`--dry-run`, max_steps=10) bypasses the tripwire so quick smoke tests don't trigger it.

After this incident the defaults were changed to `--lr 1e-4 --loraplus_ratio 8.0` (half-strength), and subsequent runs were stable.

## The `StepTimerCallback`

Logs wall time per step for the first 12 steps. If step 12 wall time exceeds 25 s, prints a warning pointing at the env-var fixes. Dry-run mode also gates the full run on this: if mean step time of the dry-run sample exceeds 25 s, the script exits with code 2 before launching the real 470-step run. This prevents committing $0.30+ to a misconfigured pod.

## Cost story (Apr 2026 sprint)

- Pod 1 (initial): RunPod RTX 5090 on-demand at $0.348/hr. Diverged at step ~105 (caught by the tripwire). Killed.
- Pod 2 (sprint): Vast.ai EPYC 7R32 + 5090 spot at **$0.028/hr** with 50 GB persistent volume. 12× cheaper than pod 1, better hardware. Three sequential baseline runs (baseline-dirty + baseline-cleaned + candidate) totaled ~$0.34 of cloud spend.
- Pattern-master single-domain reference (pre-sprint): trained in 52 minutes for $0.46 on the same 5090 stack — 197× faster than the local RTX 2080 baseline.

The persistent volume on pod 2 is the operational key: bootstrap + base model + venv survive stop/start, so re-spool on a new run is instant rather than another 10-minute install.

## Reproducing the recipe

```bash
# On a fresh Vast.ai pod with PyTorch image:
bash vast_bootstrap_5090.sh             # one-time setup
# Place training corpus at /workspace/corpus/twin_train_baseline.jsonl
# Place base model at /workspace/models/qwen35-4b
bash start_baseline_train.sh            # full 470-step run with tripwire
# Or for a sanity check first:
python -u train_baseline_lora.py --dry-run
```

The dry-run takes 2–3 minutes and prints step times. Full run takes ~2.5 hours on the 5090 spot pod.
