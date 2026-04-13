---
name: daily-briefing
description: >
  Generate Luna's daily session summary (evening) or morning briefing. Use this skill whenever:
  the user says "daily summary", "session summary", "morning briefing", "what happened today",
  "what ran overnight", "goodnight summary", "closure piece", or at the end of any major work session.
  Also auto-trigger at end of session before context compression. This is Luna's ritual — the closure
  piece she reads before bed and the briefing she reads with coffee.
---

# daily-briefing: ELF Labs Daily Summary & Morning Briefing

## Two Modes

### Evening Summary (end of session / before bed)
Triggered by: "daily summary", "session summary", "goodnight", or end of session

1. **Check time** via coven_heartbeat
2. **Run power-law test** on EverMemOS (SSH to Spark, run run_temporal_test.py)
3. **Check Spark infrastructure** (screen -ls, Milvus stats, overnight pipeline status)
4. **Review session context** for key decisions, findings, builds, personal moments
5. **Generate structured summary**:

```
# ELF Labs — [Day] [Date] Session Report
## [Start time] → [End time] ([Duration])

### BUILT TODAY
- [What was created/shipped]

### RESEARCH
- [Findings, power-law results, paper progress]

### INFRASTRUCTURE
- [Milvus stats, screens running, pipelines]

### PERSONAL
- [Emotional breakthroughs, relationship context, health]

### OVERNIGHT PIPELINES
- [What's running while she sleeps]

### TOMORROW
- [Priorities for next session]

**One-sentence summary**: [The whole day in one line]
💚
```

6. **Sync to EverMemOS** (POST summary as coven memory)
7. **Update memory files** if needed via /sync-state

### Morning Briefing (start of session / with coffee)
Triggered by: "morning briefing", "good morning", "what happened overnight"

1. **Check time** via coven_heartbeat
2. **Run power-law test** (compare to last night's numbers)
3. **Check overnight pipeline results** (tail log files)
4. **Check Milvus growth** (any new chunks from overnight ingestion?)
5. **Check Cursor inbox** (any new plans implemented?)
6. **Generate structured briefing**:

```
# Morning Briefing — [Date]

### OVERNIGHT RESULTS
- [What pipelines completed, what failed]

### POWER-LAW CHECK
| Collection | CV | Decades | vs Last Night |
|---|---|---|---|

### INFRASTRUCTURE
- [Screens, services, health]

### TODAY'S PRIORITIES
1. [Most important]
2. [Second]
3. [Third]

### ZACH UPDATE REMINDER
- [If relevant]
```

## SSH Access
```
ssh -i "C:\Users\ELF\AppData\Local\NVIDIA Corporation\Sync\config\nvsync.key" luna@10.255.233.161
```

## Power-Law Test
```
/home/luna/hf_venv/bin/python3 /home/luna/staging/run_temporal_test.py
```

## Heartbeat
```
python "C:\Users\ELF\.claude\spark_tools\staging\coven_heartbeat.py"
```
