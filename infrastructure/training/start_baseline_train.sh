#!/usr/bin/env bash
# Run on Vast as root — full 470-step baseline (not dry-run). Logs to /workspace/logs/full_baseline_train.log
set -euo pipefail
source /etc/profile.d/elf_5090.sh
source /workspace/venv/bin/activate
mkdir -p /workspace/logs
export PYTHONUNBUFFERED=1
exec python -u /workspace/training/train_baseline_lora.py 2>&1 | tee -a /workspace/logs/full_baseline_train.log
