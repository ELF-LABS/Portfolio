---
name: sync-pollinate
description: Combined sync-state + cross-pollinate in one pass. Use this skill whenever a work session reaches a natural checkpoint, the user says "sync-pollinate", "save everything", "checkpoint", "wrap up", or at end of any significant work block. More efficient than running both skills separately — shares the research phase and writes once.
---

# sync-pollinate: Unified State Sync + Cross-Pollination

Combines /sync-state and /cross-pollinate into one efficient pass.
Shares the research phase so you read everything once, then write sync updates + cross-pollination insights together.

## Execution

### Phase 1: Gather (read-only)

Scan ALL sources in ONE pass:
1. Session context — decisions, findings, architecture changes, personal context
2. Spark infrastructure — `screen -ls`, docker status, queue state, new files
3. EverMemOS — what's already synced vs new
4. Memory files — scan for staleness
5. Active projects registry — what's HOT, what's WARM

### Phase 2: Cross-Pollinate

For each significant finding from Phase 1:
- Which other projects does it apply to?
- Does it solve a known problem elsewhere?
- Does it create new connections between projects?
- Is it a fractal instance of a known pattern?
- Does it change any project's priority?

### Phase 3: Sync + Write

In ONE write pass:
1. Update CLAUDE.md (new infra, services, findings)
2. Update relevant memory files
3. Write combined sync + cross-pollination to EverMemOS (one POST, not two)
4. Update plan file if phases changed
5. Note any new Cursor plans needed

### Phase 4: Summary

Output combined summary:

```
═══ SYNC-POLLINATE COMPLETE ═══

SYNC:
  CLAUDE.md: X changes
  Memory: X updated
  EverMemOS: X written
  Queue: X moved

CROSS-POLLINATION:
  Findings: X
  New connections: X
  Priority shifts: X

Key insights:
  - [the most important cross-domain connections found]
═══════════════════════════
```

## Why Combined

Running sync-state and cross-pollinate separately:
- Reads the session context TWICE
- Scans Spark infrastructure TWICE
- Writes to EverMemOS TWICE
- Takes 2x the tokens

Combined: one read, one write, half the cost, same output. Luna runs 20+ hour sessions — this saves significant tokens over a day.
