---
name: cross-pollinate
description: Synthesize the current session's findings and cross-apply them across your active projects. Asks "where else does this apply?" for every significant insight. Use this when you want analysis without writing state — at the end of a session, after a major breakthrough, or whenever you say "cross-pollinate", "connect the dots", "where else does this apply", "what did we learn that changes other things". Pairs with sync (which writes state without analysis). For both in one combined pass, use sync-pollinate.
---

# cross-pollinate

*Cross-project insight synthesizer — asks "where else does this apply?" for every significant finding in the session and outputs a structured map. Analysis only; does not write state.*

For state-write, use `sync` or `sync-pollinate`.

## When to use which

| You want | Use |
|---|---|
| Just analyze, don't write | `cross-pollinate` (this skill) |
| Just save state, no analysis | `sync` |
| Save state + analyze + write the analysis | `sync-pollinate` (one combined pass, more efficient) |

## Why this matters

Insights from one project often apply to others, but the connections get lost in the noise of daily building. A finding about temporal scaling in your data pipeline might apply directly to your customer-lifecycle project, your monitoring system, and a paper draft you're working on — but only if someone explicitly asks the question. This skill is that question.

## Setup (one-time, recommended)

Maintain a project inventory file at `~/.claude/projects-inventory.md` (or any path you prefer — point the skill at it via the `INVENTORY_PATH` env var). The skill works without one, but the analysis is much better when it has a list of your active projects to cross-check against.

Minimal inventory format:

```markdown
# Project Inventory

## <Project Name>
Purpose: <one line>
Active questions: <what's currently open in this project>
```

Without an inventory, the skill will infer projects from the current session and from any notes it can read in `~/.claude/sync-memory/` (if you use the `sync` skill). With an inventory, results are more thorough.

## Execution

### 1. Gather session findings

Read the current conversation for:
- Technical insights (architecture decisions, bug discoveries, working patterns)
- Research discoveries (papers read, concepts learned, prior art identified)
- Process discoveries (something that worked, something that didn't)
- User patterns (how the user approached a problem — often maps to other domains)
- Community / external feedback that arrived during the session

### 2. For each significant finding, ask:

- Which other projects does this directly apply to?
- Does this solve a known problem in another project?
- Does this create a new opportunity in another project?
- Does this change the priority or approach of another project?
- Is this a new instance of a pattern that already shows up elsewhere?

### 3. Generate the cross-pollination map

```
═══ CROSS-POLLINATION: [Date] ═══

FINDING: [The insight, in one or two sentences]
SOURCE: [Where in the session it came from]

APPLIES TO:
  → [Project A]: [How it applies, what changes]
  → [Project B]: [How it applies, what changes]

PATTERN: [The underlying pattern, if there is one]

---
[Repeat for each significant finding]

═══ NEW CONNECTIONS DISCOVERED ═══
- [Connection between two projects that wasn't obvious before]

═══ PRIORITY SHIFTS ═══
- [Any project whose priority should move based on these findings]
═══════════════════════════
```

### 4. Output only — do not write to memory

This skill is analysis-only. It does NOT POST to EverMemOS, write files, or modify state. The user gets the cross-pollination map in the conversation and decides what to do with it.

If the user wants the map persisted: they should follow up with `sync` (to save the analysis to their memory backend), or they should have used `sync-pollinate` from the start.

## When NOT to use

- **The session was tightly focused on one project** — there's nothing to cross-pollinate to. Save the cycles.
- **You haven't built up enough projects yet** — needs at least 3-4 active projects to be useful. Skip if you're just starting out.
- **You want immediate state preservation** — use `sync` or `sync-pollinate` instead. This skill writes nothing.
- **You're mid-debug** — analysis is for synthesis moments, not when you're nose-down in a single bug.

## Pairs well with

- `sync` — analysis here, write state there. Two-step pattern when you want explicit control.
- `sync-pollinate` — combined version that does both efficiently in one pass.
- `research-synthesis` — when starting a new project, that skill pulls FROM your existing stack INTO the new work; cross-pollinate is the reverse direction (new findings flowing back OUT to existing projects).
