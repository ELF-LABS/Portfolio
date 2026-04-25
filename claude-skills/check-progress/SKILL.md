---
name: check-progress
description: Multi-machine status dashboard. Parallel health check across your hosts (SSH, Docker containers, GPU utilization, screen/tmux sessions, training jobs, queues, logs). Use whenever the user says "status", "check progress", "how are we doing", "what's running", "check machines", or "systems check". Customize the host list and check commands for your own infrastructure.
---

# check-progress: Multi-Machine Status Dashboard

*Parallel health-check across your fleet — one command, all machines, all running processes.*

> ⚠️ **THIS IS A TEMPLATE. CUSTOMIZE BEFORE FIRST USE.**
>
> The host blocks below contain `<PLACEHOLDER>` values (in angle brackets, ALL CAPS). You **must** replace every placeholder with your actual values — host addresses, SSH key paths, queue paths, log directories — or the skill will fail with connection errors and unhelpful output. Do not copy-paste and run as-is.
>
> Read the entire **Setup** section below before running anything. If you commit this skill to a public repo after customizing it, move real host details into a local override file and keep placeholders in the committed version.

## Setup (one-time, required)

Before this skill is useful, fill in your own host inventory. The template below assumes 3–4 hosts with SSH access; your fleet may be larger, smaller, or shaped differently.

**Placeholder convention:** every customizable value is `<ALL_CAPS_IN_ANGLE_BRACKETS>`. Replace all of them before first use. If you see any remaining in the rendered output, that block still needs filling in.

**What to replace:**
- `<HOST_X_ALIAS>` → your friendly host name (e.g. `prod-gpu`, `dev-workstation`)
- `<HOST_X_USER@HOST_X_ADDR>` → SSH target (user@ip, user@mesh-hostname, or an alias from `~/.ssh/config`)
- `<HOST_X_KEY_PATH>` → path to the private SSH key on your local machine
- `<QUEUE_INBOX_PATH>`, `<LOG_DIR>`, `<TRAINING_LOG_DIR>`, `<ADAPTER_OUTPUT_DIR>` → actual directories on that host
- The check commands inside each block — tune to what's actually running on that host

**Fleet-shape adjustments:**
- **Single-machine setup (no SSH):** delete all the SSH-wrapped blocks, keep only the local block (Host 4). Replace `ssh ... "<cmd>"` with direct Bash.
- **More than 4 hosts:** copy the Host 1 template block and customize it for each additional host. Naming convention: `Host 5`, `Host 6`, etc.
- **Mixed OS fleet** (Linux + Mac + Windows): use `uname` at the start of each SSH payload to branch commands, or maintain separate host blocks per OS. The Linux commands below (`free`, `nvidia-smi`, `docker ps`) work on Mac mostly as-is; Windows hosts need WSL2 or separate PowerShell payloads.
- **Windows hosts without WSL:** adapt to PowerShell Remoting or skip — native Windows SSH has rough edges with GPU queries.
- **Ephemeral cloud hosts** (RunPod, Vast.ai, Lambda): keep the block commented out when pods are idle; uncomment and fill the IP/port when you spin one up.

**Secrets discipline:**
- Never commit this skill with real SSH key paths if the repo is public — keep those paths in a local override that isn't tracked.
- Use SSH config aliases (`Host my-server` in `~/.ssh/config`) to avoid hardcoding IPs in the skill body; the skill can then use `ssh my-server "..."` instead of full connection strings.
- If a host uses a VPN / mesh network (Tailscale, WireGuard, etc.), prefer the mesh hostname over raw IPs.
- This skill does not persist or log output by default — runs are ephemeral. If you want history, pipe the output to a file yourself.

## Execution

Run all host checks **in parallel** (multiple Bash calls in a single message) — serial runs defeat the whole point of the skill.

### Host 1 template — GPU inference server

```bash
ssh -i "<HOST_1_KEY_PATH>" <HOST_1_USER@HOST_1_ADDR> "
echo '=== SCREENS / TMUX ===' && screen -ls 2>/dev/null || tmux ls 2>/dev/null
echo '=== DOCKER ===' && docker ps --format '{{.Names}} {{.Status}}' | head -15
echo '=== MEMORY ===' && free -h | head -2
echo '=== GPU ===' && nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv
echo '=== QUEUE ===' && ls <QUEUE_INBOX_PATH> 2>/dev/null | wc -l
echo '=== ACTIVE LOGS ===' && for log in <LOG_DIR>/*.log; do [ -f \"\$log\" ] && echo \"\$(basename \$log): \$(tail -1 \$log 2>/dev/null | head -c 80)\"; done
"
```

### Host 2 template — GPU workstation (e.g., desktop or secondary inference)

```bash
ssh -i "<HOST_2_KEY_PATH>" -o ConnectTimeout=5 <HOST_2_USER@HOST_2_ADDR> "
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
echo ---
ps aux | grep -E 'python|torch' | head -5
"
```

### Host 3 template — Cloud GPU pod (e.g., RunPod, Vast.ai, Lambda)

```bash
# Only runs if cloud pod is active — fill in current IP/port when you spin one up
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@<POD_IP> -p <POD_PORT> -i <POD_KEY_PATH> "
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
echo ---
tail -3 <TRAINING_LOG_DIR>/train_*.log 2>/dev/null | tail -5
echo ---
ls <ADAPTER_OUTPUT_DIR>/*/adapter_model.safetensors 2>/dev/null
"
```

### Host 4 template — local machine

```bash
echo "=== LOCAL DOCKER ===" && docker ps 2>/dev/null | head -5
echo "=== VPN / MESH ===" && tailscale status 2>/dev/null | head -5
```

## Output Format

```
═══ SYSTEMS CHECK ═══

<HOST_1_ALIAS> (<hostname/ip>):
  Screens/tmux: X active
  Docker: X containers healthy
  Memory: X/YGB
  GPU: X% util, Y/ZGB VRAM, T°C
  Queue: X inbox items
  Active logs: [brief summaries of latest log lines]

<HOST_2_ALIAS>:
  GPU: X% util, Y/ZGB VRAM, T°C
  Running processes: <list>

<HOST_3_ALIAS> (cloud, if active):
  GPU: X% util, Y/ZGB VRAM
  Training: <progress snapshot>
  Completed artifacts: <list>

LOCAL:
  Docker: X containers
  VPN/mesh: all nodes connected / issues noted
═══════════════════════════
```

## Operating notes

- **Keep it parallel.** Serial runs defeat the skill. All SSH calls dispatched in one message.
- **Use short timeouts.** `-o ConnectTimeout=5` on every SSH call — if a host is down, you want to know in 5 seconds, not after 30.
- **Graceful degradation.** If a host isn't reachable, report it clearly and continue with the others. Don't fail the whole check because one node is offline.
- **Adapt the check blocks.** The per-host commands above are starting points. A training host might add `wc -l new_pairs/*.jsonl` to track pair generation; a database host might add `psql -c "SELECT COUNT(*) FROM ..."`. Make the checks match what you actually care about on each machine.
- **Public-repo safety.** If this skill is committed to a public repo, keep real keys/IPs/hostnames in a local override file that isn't tracked. The template stays generic.
