---
name: sync-state
description: >
  Synchronize all ELF Labs project state across CLAUDE.md, memory files, EverMemOS, and roadmap plans.
  Use this skill whenever: a major work session is wrapping up, the user says "sync", "update everything",
  "push state", "save progress", before ending a session, after completing a major milestone, or when
  the user says /sync-state. Also trigger when the user mentions updating memory, pushing to EverMemOS,
  or keeping files in sync. This skill is the "save game" button for the entire ELF Labs ecosystem.
  It can also be triggered via staging-claw CLI on Spark.
---

# sync-state: ELF Labs State Synchronization

You are synchronizing the state of the ELF Labs multi-machine AI infrastructure across all persistent storage systems. This runs autonomously and outputs a summary of all changes made.

## Why This Matters

ELF Labs state lives in 5 places that can drift apart:
1. **CLAUDE.md** (~/.claude/CLAUDE.md) — what future Claude sessions see
2. **Memory files** (~/.claude/projects/C--/memory/*.md) — topic-specific project state
3. **EverMemOS** (Spark:1995 via Tailscale 100.114.179.3) — shared Coven memory
4. **Plan file** (~/.claude/plans/peaceful-sauteeing-ullman.md) — roadmap and sprint plans
5. **Staging-claw inbox** (Spark:/home/luna/staging/cursor_queue/inbox/) — Cursor task queue

When these drift, the next session starts with stale context. sync-state prevents that.

## Execution Flow

### Phase 1: Research (Read-Only)

Gather current state from all sources. Do NOT write anything yet.

**1a. Session Context**
- Read the current conversation for key decisions, findings, and new infrastructure
- Identify: new files created, services deployed, research findings, personal context updates, architecture changes

**1b. Spark Infrastructure Scan**
SSH to Spark and check:
```bash
ssh -i "C:\Users\ELF\AppData\Local\NVIDIA Corporation\Sync\config\nvsync.key" luna@10.255.233.161
```
- `screen -ls` — what's running?
- `ls /home/luna/staging/shells/` — any new shell files?
- Milvus collection stats — any new/grown collections?
- `ls /home/luna/staging/overnight_results/` — any new pipeline results?
- `ls /home/luna/staging/cursor_queue/done/` — what plans were completed?
- `docker ps --format "table {{.Names}}\t{{.Status}}"` — service health

**1c. EverMemOS Check**
```bash
curl -s http://100.114.179.3:1995/api/v1/memories/search -H "Content-Type: application/json" \
  -d '{"query": "latest session findings", "group_id": "coven", "limit": 10}'
```
Check what's already been synced vs what's new.

**1d. Read Current Files**
- Read `~/.claude/CLAUDE.md` — what does it currently say?
- Read `~/.claude/projects/C--/memory/MEMORY.md` — current index
- Scan all memory/*.md files for staleness
- Read the plan file for current phase status

### Phase 2: Transform (Diff Analysis)

Compare what IS (current files) against what SHOULD BE (session reality):

For each target, build a change list:
```
CLAUDE.md:
  + ADD: [new section or line]
  ~ UPDATE: [changed value]
  - REMOVE: [stale entry]

memory/specific_file.md:
  + ADD: [new finding]
  ~ UPDATE: [changed status]

EverMemOS:
  + WRITE: [new memory not yet synced]

Plan file:
  ~ UPDATE: [phase status change]
  + ADD: [new phase or task]

Cursor inbox:
  + DROP: [new plan if code gaps found]
```

### Phase 3: Update (Write)

Apply all changes autonomously:

**3a. CLAUDE.md Updates**
Use the Edit tool to make targeted updates. Common updates:
- New services/ports in the infrastructure table
- New shell collections in Milvus stats
- New skills or agents
- Updated vault entity counts
- New quick commands
- New critical rules or gotchas discovered

**3b. Memory File Updates**
- Update existing memory files with new findings
- Create new memory files if a new topic area emerged
- Archive stale memory files to `memory/archive/` (per-domain archive subdirectories as needed)
- Update MEMORY.md index if files were added/removed

**3c. EverMemOS Writes**
POST session findings to EverMemOS:
```bash
curl -s -X POST http://100.114.179.3:1995/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "sync-state-TIMESTAMP",
    "create_time": "ISO8601",
    "sender": "claude-code",
    "content": "FINDING TEXT",
    "group_id": "coven"
  }'
```

**3d. Plan File Updates**
Update phase statuses, add new phases if needed, mark completed items.

**3e. Cursor Inbox (if code gaps found)**
If the research phase identified missing code, stale configs, or needed refactors:
```bash
scp PLAN_CURSOR_*.md luna@10.255.233.161:/home/luna/staging/cursor_queue/inbox/
ssh luna@10.255.233.161 '/home/luna/bin/staging-claw trigger /path/to/plan'
```

### Phase 4: Prune

- Remove entries from CLAUDE.md that reference completed/archived work
- Move completed memory files to appropriate archive
- Mark completed plan tasks as DONE
- Remove stale EverMemOS entries if clearly outdated

### Phase 5: Summary Output

Print a structured summary:

```
═══ SYNC-STATE COMPLETE ═══

CLAUDE.md: X additions, Y updates, Z removals
Memory files: X updated, Y created, Z archived
EverMemOS: X memories written
Plan file: X phases updated
Cursor inbox: X plans dropped (or "no code gaps found")

Key changes:
- [bullet list of the most important state changes]

Staleness check:
- [any files that might need manual review]
═══════════════════════════
```

## SSH Access

All Spark commands use:
```
ssh -i "C:\Users\ELF\AppData\Local\NVIDIA Corporation\Sync\config\nvsync.key" luna@10.255.233.161
```

## EverMemOS API

- Endpoint: `http://100.114.179.3:1995/api/v1/memories` (Tailscale IP — UFW blocks LAN)
- Required fields: `message_id`, `create_time`, `sender`, `content`, `group_id`
- Group: `"coven"`
- Sender: `"claude-code"`

## Memory File Location

`C:\Users\ELF\.claude\projects\C--\memory\`

## Plan File Location

`C:\Users\ELF\.claude\plans\peaceful-sauteeing-ullman.md`

## Staging-Claw Trigger

To trigger this skill from the CLI on Spark, create a trigger file:
```bash
echo "SYNC_STATE_TRIGGER" > /home/luna/staging/cursor_queue/inbox/TRIGGER_SYNC_STATE.md
/home/luna/bin/staging-claw trigger /home/luna/staging/cursor_queue/inbox/TRIGGER_SYNC_STATE.md
```

When Claude Code or the twin detects this trigger file, it should invoke this skill.
