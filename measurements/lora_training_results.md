# LoRA Adapter Fleet — Training Results

## Training Infrastructure
- **Base model**: Qwen3.5-4B (dense, native VL)
- **Config**: QLoRA 4-bit NF4, OLoRA init, DoRA, LoRA+ (ratio 16)
- **Rank**: 48, Alpha: 96
- **Target modules**: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
- **Hardware**: RTX 2080 (8GB, initial), RunPod A6000 (48GB, current)
- **Duration**: 46.5h autonomous on Omen (Apr 5-8), then cloud training (Apr 13)

## Adapter Fleet

| Adapter | Task | Pairs | Epochs | Size | Training |
|---------|------|-------|--------|------|----------|
| identity | Luna's voice, values, persona | 2,238 + 596 new | 3 | 124MB | ✅ Retrained A6000 |
| code | Python, system scripts | 1,808 + 125 new | 3 | 129MB | 🔄 Training A6000 |
| writer | Narrative, letters, communication | 1,176 + 502 new | 3 | 129MB | ⏳ Queued |
| analytical | Research, data analysis | 982 | 3 | 129MB | ⏳ Queued |
| ops | Infrastructure, DevOps | ~500 (generating) | 3 | 129MB | ⏳ Queued |
| sales | Business, authentic pitching | ~400 (generating) | 3 | 129MB | ⏳ Queued |
| pattern | Cognitive flow, topic switching, Limbic Sonar | 5,115 + 300 neuro + ~200 limbic | 5 | 124MB | ⏳ Master retrain after base |
| flight-tuning | PID tuning, Betaflight analysis | 287 | 5 | 41MB (rank 16) | ✅ Trained A4000 |

## Cloud Training Economics

| GPU | Cost/hr | Pattern LoRA (5K pairs) | All 8 adapters |
|-----|---------|------------------------|----------------|
| RTX 2080 (Omen) | electricity only | ~85 hours | ~240 hours |
| RTX A4000 (RunPod) | $0.25 | ~10 hours | ~28 hours |
| RTX A6000 (RunPod) | $0.64 | ~3 hours | ~8 hours |

Total cloud cost for full fleet retrain: **~$5-8 on A6000**

## Key Training Insights
- PiSSA init incompatible with bitsandbytes 4-bit → auto-fallback to OLoRA
- SM75 (RTX 2080): float16 only, no native bfloat16. SM86+ (A4000/A6000): bfloat16 supported
- DoRA uses ~30% more VRAM but improves adapter quality
- Batch 2 + seq 1024 on A6000 uses 88% VRAM (43/49GB) — optimal utilization
- All adapters use `task: "identity"` to bypass train_lora_v4.py profile filter

## Deployment
- SGLang multi-LoRA: `--enable-lora --lora-paths identity=/path code=/path ...`
- Per-request routing via `model` field in OpenAI-compatible API
- Max 8 LoRAs loaded simultaneously in ~1.2GB VRAM
