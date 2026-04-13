---
name: fast-ops
description: Fast file manipulation, text processing, and bulk operations across ELF Labs machines. Use this skill whenever you need to do bulk find/replace, grep/sed/awk pipelines, CSV/JSON munging, log analysis, file format conversion, mass renaming, or any text processing task that benefits from lightweight shell tools. Also use when parallelizing the same operation across multiple machines (Spark, P5, Omen). Triggers on phrases like "find and replace across", "bulk rename", "grep all machines", "convert these files", "munge this data", "process these logs", "quick calculation", "search all three machines".
---

# fast-ops: Lightweight Multi-Machine Shell Operations

You have three execution tiers. Pick the lightest one that fits the job.

## Tier 1: Docker Alpine (P5, instant-boot, disposable)

For pure text processing where you don't need persistent state. Alpine containers boot in <1 second, use ~5MB RAM, and die when done. Perfect for grep/sed/awk/jq pipelines.

```bash
# One-shot Alpine container for text processing
docker run --rm -v "C:\Users\ELF:/data" alpine sh -c "
  grep -r 'pattern' /data/target_dir --include='*.py' | 
  sed 's/old/new/g' | 
  sort -u > /data/output.txt
"

# With jq for JSON munging
docker run --rm -v "C:\Users\ELF:/data" alpine sh -c "
  apk add --no-cache jq &&
  cat /data/input.json | jq '.[] | select(.score > 0.5)' > /data/filtered.json
"

# Parallel file processing
docker run --rm -v "C:\Users\ELF:/data" alpine sh -c "
  find /data/target -name '*.md' | xargs -P4 -I{} sh -c 'sed -i s/oldIP/newIP/g {}'
"
```

**When to use**: Text search, find/replace, JSON filtering, CSV transforms, file counting, anything that's pure stdin→stdout processing.

**When NOT to use**: Anything needing Python libraries, network access to Spark/Omen, or persistent state.

## Tier 2: WSL2 Ubuntu (P5, heavier ops)

For operations needing Python, pip packages, or sustained processing. Ubuntu-22.04 is always running on P5.

```bash
wsl -d Ubuntu-22.04 -e bash -c "
  cd /mnt/c/Users/ELF && 
  python3 -c 'import json; ...'
"
```

**When to use**: Python scripts, pip-dependent tasks, operations needing git, compilation, or anything too complex for Alpine one-liners.

## Tier 3: Direct SSH (Spark / Omen)

For operations on remote machine filesystems. Always use the correct SSH patterns.

**Spark:**
```bash
ssh -i "C:\Users\ELF\AppData\Local\NVIDIA Corporation\Sync\config\nvsync.key" luna@10.255.233.161 "COMMAND"
```

**Omen** (username has SPACE, shell is CMD):
```bash
ssh -i "C:/Users/ELF/.ssh/minipc_key" -o StrictHostKeyChecking=no "elf labs@10.255.230.168" "COMMAND"
```

For Omen Windows commands: use `dir` not `ls`, `type` not `cat`, `findstr` not `grep`, backslashes in paths.

**When to use**: File operations on Spark/Omen filesystems, running scripts on remote machines, checking service status.

## Parallelization Patterns

When the same operation needs to run across multiple machines, launch all SSH commands in the same tool call block:

```bash
# Parallel grep across all three machines
echo "=== P5 ===" && grep -r "pattern" /target/path --include="*.py" &
ssh SPARK "grep -r 'pattern' /home/luna/staging/ --include='*.py'" &
ssh OMEN "findstr /s /i \"pattern\" C:\\temp\\*.py" &
wait
```

Or use multiple Bash tool invocations in the same message for true parallelism.

## Common Recipes

### Bulk IP/string replacement across all machines
```bash
# P5 local
find C:/Users/ELF/.claude/ -type f \( -name "*.py" -o -name "*.md" -o -name "*.json" \) -exec sed -i 's/OLD/NEW/g' {} +
# Spark
ssh SPARK "grep -rl 'OLD' /home/luna/staging/ | xargs sed -i 's/OLD/NEW/g'"
# Omen (PowerShell)
ssh OMEN "powershell -Command \"Get-ChildItem -Recurse C:\\temp -Include *.py,*.json | ForEach { (Get-Content \$_) -replace 'OLD','NEW' | Set-Content \$_ }\""
```

### JSON ↔ CSV conversion
```bash
docker run --rm -v "C:\Users\ELF:/data" alpine sh -c "
  apk add --no-cache jq &&
  cat /data/input.json | jq -r '.[] | [.field1, .field2] | @csv' > /data/output.csv
"
```

### Count lines/files across machines
```bash
# All machines in parallel
echo "P5:" && find C:/Users/ELF/Desktop -name "*.md" | wc -l
ssh SPARK "find /home/luna/staging -name '*.py' | wc -l"
ssh OMEN "powershell -Command \"(Get-ChildItem -Recurse C:\\temp -Filter *.py).Count\""
```

### Log analysis with timestamps
```bash
docker run --rm -v "C:\Users\ELF:/data" alpine sh -c "
  grep -h 'ERROR\|WARN' /data/logs/*.log |
  sort -t'[' -k2 |
  uniq -c |
  sort -rn |
  head -20
"
```

### JSONL processing (training data, timelines)
```bash
docker run --rm -v "C:\Users\ELF:/data" alpine sh -c "
  apk add --no-cache jq &&
  cat /data/target.jsonl | 
  jq -s 'group_by(.task) | map({task: .[0].task, count: length})' 
"
```

## Decision Tree

```
Is it pure text processing (grep/sed/awk/jq)?
  → Tier 1: Docker Alpine

Does it need Python or pip packages?
  → Tier 2: WSL2 Ubuntu

Does it need to run on Spark or Omen?
  → Tier 3: SSH

Does it need to run on ALL machines?
  → Parallel: launch all three tiers simultaneously

Is the data on P5 but the processing is heavy?
  → Tier 2: WSL2 Ubuntu with mounted Windows filesystem at /mnt/c/
```

## Tailscale IPs (current)
- Spark: 100.114.179.3
- P5: 100.120.184.62
- Omen: 100.84.249.94
