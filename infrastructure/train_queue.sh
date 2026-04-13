#!/bin/bash
export HF_HOME=/workspace/.hf_cache
mkdir -p /workspace/output

echo "=== ELF LABS ADAPTER TRAINING QUEUE ==="
echo "Started: $(date)"

train_adapter() {
    local name=$1
    local data=$2
    local epochs=$3

    if [ ! -f "/workspace/data/${data}" ]; then
        echo "[SKIP] ${name} -- data file ${data} not found"
        return
    fi

    local count=$(wc -l < "/workspace/data/${data}")
    echo ""
    echo "=== TRAINING: ${name} (${count} pairs, ${epochs} epochs) ==="
    echo "Started: $(date)"

    python3 /workspace/train_lora_v4.py \
        --profile identity \
        --data_path "/workspace/data/${data}" \
        --output_dir "/workspace/output/elf-${name}-lora" \
        --epochs ${epochs} \
        --use_dora \
        --lora_rank 48 \
        --lora_alpha 96 \
        --loraplus_ratio 16 2>&1

    echo "Completed ${name}: $(date)"
    ls -lh "/workspace/output/elf-${name}-lora/adapter/adapter_model.safetensors" 2>/dev/null
}

# ROUND 1: Train what we have NOW
train_adapter "identity" "identity_existing.jsonl" 3
train_adapter "code" "code_existing.jsonl" 3
train_adapter "writer" "writer_existing.jsonl" 3
train_adapter "analytical" "analytical_existing.jsonl" 3

# ROUND 2: Check for new pairs that arrived during round 1
echo ""
echo "=== ROUND 2: CHECKING FOR NEW ARRIVALS ==="
train_adapter "ops" "ops_pairs.jsonl" 3
train_adapter "sales" "sales_pairs.jsonl" 3
train_adapter "observer" "observer_pairs.jsonl" 5

echo ""
echo "=== ALL TRAINING COMPLETE ==="
echo "Finished: $(date)"
echo ""
echo "Outputs:"
ls -lh /workspace/output/*/adapter/adapter_model.safetensors 2>/dev/null
