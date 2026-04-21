#!/usr/bin/env bash
# vast_bootstrap_5090.sh — run on the Vast pod as root.
# Proven recipe for QLoRA training on RTX 5090 spot ($0.028/hr on Vast EPYC 7R32 + 5090 + 96GB RAM + PCIe 4.0).
set -euo pipefail
LOG=/workspace/bootstrap.log
exec > >(tee -a "$LOG") 2>&1
echo "[BOOTSTRAP] start $(date -u +%FT%TZ)"

# 1. apt essentials
apt-get update -qq
apt-get install -y -qq git tmux screen htop nvtop wget curl rsync jq python3-pip python3-venv

# 2. Env vars — make them inherited by every shell.
# Critical for RTX 5090 / sm_120: without TORCHDYNAMO_DISABLE + TOKENIZERS_PARALLELISM set
# BEFORE `import torch`, step time is ~88s/step (vs 18s with these set). dataloader_pin_memory
# also matters; killing torch.compile + triton_autotune workers prevents stale state.
cat > /etc/profile.d/elf_5090.sh << 'ENV'
export TORCHDYNAMO_DISABLE=1
export TOKENIZERS_PARALLELISM=false
export HF_HOME=/workspace/hf_cache
export TRANSFORMERS_CACHE=/workspace/hf_cache
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
ENV
source /etc/profile.d/elf_5090.sh
echo "[BOOTSTRAP] env vars installed"

# 3. Workspace scaffold
mkdir -p /workspace/{training,models,corpus,output,logs,hf_cache}

# 4. Python venv + proven stack (bitwise-stable for RTX 5090 sm_120)
python3 -m venv /workspace/venv
source /workspace/venv/bin/activate
pip install --upgrade pip wheel
pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.8.0
pip install bitsandbytes==0.49.2 peft==0.18.1 transformers==5.5.0 accelerate trl datasets sentencepiece safetensors protobuf hf_transfer
echo "[BOOTSTRAP] python stack installed"

# 5. Kill any lingering torch compile workers (prevents step-time regression)
pkill -f 'torch.compile' 2>/dev/null || true
pkill -f 'triton_autotune' 2>/dev/null || true

# 6. Smoke test
python3 << 'PY'
import os, sys
assert os.environ.get("TORCHDYNAMO_DISABLE") == "1", "env not set"
assert os.environ.get("TOKENIZERS_PARALLELISM") == "false", "env not set"
import torch
print(f"torch {torch.__version__}")
assert torch.cuda.is_available(), "CUDA not available"
dev = torch.cuda.get_device_properties(0)
print(f"GPU: {dev.name} | SM{dev.major}{dev.minor} | {dev.total_memory/1e9:.1f}GB")
assert dev.major >= 12, f"expected sm_120+, got sm_{dev.major}{dev.minor}"
import bitsandbytes as bnb
print(f"bnb {bnb.__version__}")
import peft, transformers
print(f"peft {peft.__version__} transformers {transformers.__version__}")
# Quick bnb sanity
x = torch.randn(128, 128, device='cuda', dtype=torch.bfloat16)
q = bnb.functional.quantize_nf4(x)
print(f"bnb quantize_nf4 OK, shape {q[0].shape}")
print("SMOKE PASS")
PY

echo "[BOOTSTRAP] smoke complete $(date -u +%FT%TZ)"
