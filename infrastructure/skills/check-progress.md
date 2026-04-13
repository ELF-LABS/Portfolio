---
name: check-progress
description: Check progress of ALL running processes across Spark, Omen, RunPod, and P5. Training jobs, pair generation, screen sessions, Docker containers, GPU utilization. Use whenever user says "status", "check progress", "how are we doing", "what's running", "check machines", "systems check", or any request for infrastructure status.
---

# check-progress: Multi-Machine Status Dashboard

One command, all machines, all running processes.

## Execution

Run these checks IN PARALLEL (multiple Bash calls in one message):

### 1. Spark
```bash
ssh -i "C:\Users\ELF\AppData\Local\NVIDIA Corporation\Sync\config\nvsync.key" luna@10.255.233.161 "
echo '=== SCREENS ===' && screen -ls
echo '=== DOCKER ===' && docker ps --format '{{.Names}} {{.Status}}' | head -15
echo '=== MEMORY ===' && free -h | head -2
echo '=== QUEUE ===' && echo 'inbox:' && ls /home/luna/staging/cursor_queue/inbox/ 2>/dev/null && echo 'done:' && ls /home/luna/staging/cursor_queue/done/ | wc -l
echo '=== PAIRS ===' && wc -l /home/luna/staging/new_pairs/*.jsonl 2>/dev/null | tail -1
echo '=== ACTIVE LOGS ===' && for log in /home/luna/staging/*_log.txt /home/luna/staging/*.log; do [ -f \"\$log\" ] && echo \"\$(basename \$log): \$(tail -1 \$log 2>/dev/null | head -c 80)\"; done
"
```

### 2. Omen (if reachable)
```bash
ssh -i "C:/Users/ELF/.ssh/minipc_key" -o ConnectTimeout=5 "elf labs@10.255.230.168" "
nvidia-smi | findstr \"MiB Util\"
echo ---
tasklist | findstr python
"
```

### 3. RunPod (if active — check known IPs)
```bash
# Try last known RunPod SSH
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@<RUNPOD_IP> -p <PORT> -i ~/.ssh/id_ed25519 "
nvidia-smi | grep -E 'MiB|Util' | head -2
echo ---
tail -3 /workspace/train_*.log 2>/dev/null | tail -5
echo ---
ls /workspace/output/*/adapter/adapter_model.safetensors 2>/dev/null
"
```

### 4. P5 (local)
```bash
echo "=== P5 DOCKER ===" && wsl -d Ubuntu-22.04 -e bash -c "docker ps 2>/dev/null | head -5"
echo "=== TAILSCALE ===" && tailscale status 2>/dev/null | head -5
```

## Output Format

```
═══ SYSTEMS CHECK ═══

SPARK (100.114.179.3):
  Screens: X active
  Docker: X containers healthy
  Memory: X/121GB
  Queue: X inbox, Y done
  Pairs: X total

OMEN (100.84.249.94):
  GPU: X% util, X/8GB VRAM, X°C
  Python: X processes

RUNPOD (if active):
  GPU: X% util, X/XGB VRAM
  Training: adapter X, step Y/Z
  Completed: [list of done adapters]

P5 (100.120.184.62):
  Docker: X containers
  Tailscale: all nodes connected
═══════════════════════════
```
