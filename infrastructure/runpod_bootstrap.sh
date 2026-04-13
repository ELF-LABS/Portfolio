#!/bin/bash
# RunPod A4500 Bootstrap — Run ONCE after pod creation
# Installs exact dependency versions proven on A4000 pattern LoRA training
# Then downloads Qwen3.5-4B model to cache
#
# Usage: scp this to pod, then: bash runpod_bootstrap.sh

set -e
echo "=== ELF Labs RunPod Bootstrap ==="
echo "Started: $(date)"

# Move HF cache to /workspace (50GB volume) to avoid filling container disk (20GB)
mkdir -p /workspace/.hf_cache
export HF_HOME=/workspace/.hf_cache
echo "export HF_HOME=/workspace/.hf_cache" >> /root/.bashrc

# ============================================
# EXACT VERSIONS — proven on A4000 pod that trained pattern LoRA successfully
# DO NOT CHANGE THESE without testing
# ============================================

echo "Installing dependencies..."

# Torch 2.6.0 + CUDA 12.4 (matches RunPod driver 550.54.15)
pip install torch==2.6.0+cu124 --index-url https://download.pytorch.org/whl/cu124 -q 2>&1 | tail -1
# Torchvision MUST match torch 2.6.0 — mismatched ABI causes Qwen3_5ForCausalLM import failure
pip install torchvision==0.21.0+cu124 --index-url https://download.pytorch.org/whl/cu124 -q 2>&1 | tail -1

# Transformers 5.5.0 — supports Qwen3.5 model_type
# NOT 5.5.3 (import error), NOT <4.51 (doesn't know qwen3_5)
pip install transformers==5.5.0 -q 2>&1 | tail -1

# PEFT, bitsandbytes, training libs
pip install peft==0.18.1 bitsandbytes==0.49.2 accelerate==1.13.0 trl==1.1.0 -q 2>&1 | tail -1

# Clean pip cache to save disk
pip cache purge 2>/dev/null

echo ""
echo "=== VERIFICATION ==="
python3 -c "
import torch; print(f'torch: {torch.__version__} (expect 2.6.0+cu124)')
import torchvision; print(f'torchvision: {torchvision.__version__} (expect 0.21.0+cu124)')
import transformers; print(f'transformers: {transformers.__version__} (expect 5.5.0)')
import peft; print(f'peft: {peft.__version__} (expect 0.18.1)')
import bitsandbytes; print(f'bitsandbytes: {bitsandbytes.__version__} (expect 0.49.2)')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'bf16 supported: {torch.cuda.is_bf16_supported()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'VRAM: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB')
"

echo ""
echo "=== DOWNLOADING MODEL ==="
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
print('Downloading Qwen3.5-4B...')
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen3.5-4B')
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen3.5-4B', quantization_config=bnb, device_map='auto')
print(f'Model loaded. VRAM: {torch.cuda.memory_allocated()/1024**3:.2f} GB')
del model
torch.cuda.empty_cache()
print('Model cached and ready.')
"

# Setup workspace structure
mkdir -p /workspace/data /workspace/output /workspace/scripts

echo ""
echo "=== BOOTSTRAP COMPLETE ==="
echo "Finished: $(date)"
echo ""
echo "Next steps:"
echo "  1. Upload training data to /workspace/data/"
echo "  2. Upload train_lora_v4.py to /workspace/"
echo "  3. Run training"
