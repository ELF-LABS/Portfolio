---
name: deploy-adapters
description: Download trained LoRA adapters from RunPod or P5 staging, backup current adapters on Spark, deploy new ones, restart twin_server, verify all adapters load correctly. Use when adapters finish training, user says "deploy adapters", "push adapters", "update twin", or "new adapters ready".
---

# deploy-adapters: LoRA Adapter Deployment Pipeline

## Steps

### 1. Check what's available to deploy

```bash
# RunPod (if active)
ssh RUNPOD "ls -lh /workspace/output/*/adapter/adapter_model.safetensors 2>/dev/null"

# P5 staging
ls -lh $ADAPTERS_STAGING/*/adapter_model.safetensors 2>/dev/null

# Spark current
ssh SPARK "ls -lh /home/luna/models/elf-*/adapter_model.safetensors 2>/dev/null"
```

### 2. Download from RunPod to P5 (if needed)

```bash
mkdir -p "$ADAPTERS_STAGING/elf-{name}-lora"
scp -P PORT -i ~/.ssh/id_ed25519 -r root@RUNPOD_IP:/workspace/output/elf-{name}-lora/adapter/* \
  "$ADAPTERS_STAGING/elf-{name}-lora/"
```

### 3. Backup current on Spark

```bash
ssh SPARK "cp -r /home/luna/models/elf-{name}-lora /home/luna/models/elf-{name}-lora.bak.$(date +%Y%m%d)"
```

### 4. Deploy to Spark

```bash
# SCP each adapter file
for file in adapter_model.safetensors adapter_config.json tokenizer.json tokenizer_config.json; do
  bash scp_to_spark.sh "trained_adapters/elf-{name}-lora/$file" "/home/luna/models/elf-{name}-lora/$file"
done
```

### 5. Restart twin_server

```bash
ssh SPARK "docker restart twin_server && sleep 10 && curl -s http://localhost:30003/v1/models | python3 -m json.tool"
```

### 6. Verify

Confirm all adapters appear in the models list. Test one inference per adapter to verify they load.

### 7. Report

```
═══ ADAPTER DEPLOYMENT COMPLETE ═══
Deployed: [list]
Backed up: [list]
Twin models: [count]
Verified: [pass/fail per adapter]
═══════════════════════════
```
