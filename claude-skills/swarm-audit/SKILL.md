---
name: swarm-audit
description: Parallel multi-agent audit for complex multi-file pipelines, followed by a single synthesis pass that extracts ROOT CAUSES and emits a numbered fix plan with per-task smoke gates. Use before running a newly-built pipeline end-to-end, before production cutover, before a paper submission or demo, or whenever serial smoke-debug has entered a fix → rerun → fix loop. Also triggers on "swarm audit", "parallel audit", "check interconnections", "cross-component bugs". Saves hours on any system with 8+ files and tight cross-file dependencies.
---

# swarm-audit

Parallel agent swarm + single-agent synthesis for interconnection audits on complex multi-file systems. The pattern has consistently surfaced dozens of static bugs in a few minutes where serial smoke-debug would take hours.

## When to use

- Pipeline or system with 8+ files and tight cross-file dependencies
- Before running a newly-built pipeline end-to-end (static preflight)
- Before production cutover
- Before a paper submission, demo, or release
- When serial smoke-debug has entered a fix → rerun → fix loop — parallelize instead
- After major refactors where the blast radius spans many files
- When the user says: "swarm audit", "parallel audit", "check interconnections", "cross-component bugs", "audit pipeline"

## When NOT to use

- Single-file bug hunt (direct inspection is faster)
- When the root cause is already known
- Runtime-only bugs that only appear under load (observability is still needed)
- Small, simple changes that don't span multiple files

## The pattern

1. **N-way parallel slice audits** (typically 4–5 agents, one per interconnection family)
2. **One synthesis pass** that distills many surface findings into 2–5 root causes
3. **Output: a numbered fix plan** with per-task smoke gates + a pre-launch smoke matrix
4. **Implementer** (the operator, or a handoff agent) works through the plan with verification at each step

The synthesis step is the most important — don't just aggregate bugs, extract the causal drivers that produce the long surface bug list. Fix causes, not symptoms.

### What to do when the pattern doesn't cleanly fit

- **Fewer than 4 meaningful slices:** run with 2–3. The synthesis step is still worth doing. Don't force artificial slices just to hit the number.
- **More than 6 slices:** the coordination cost eats the parallelism benefit. Group tightly-coupled slices together and re-slice.
- **Synthesis finds 0 or 1 root causes and 47 independent surface bugs:** promote the top 5–7 surface bugs to "blockers" directly and keep the rest as a deferred list. Not everything clusters.
- **Audit surfaces circular dependencies** (root cause #2 needs #3's fix undone first): call it out explicitly in the synthesis — mark as "requires coordinated fix" and note the dependency. Linear ordering isn't always possible.
- **Implementer authority is ambiguous:** the implementer can reorder tasks, merge related fixes, or defer LOW severity items with operator approval. They should NOT skip CRITICAL items or change success criteria without going back to the operator. Hand-off block should state explicit stop-rules.

## Workflow

### Step 1: Slice the system

Group files into 4–6 slices by interconnection family. Each slice covers 2–5 files with a coherent theme. Typical families (adapt to domain):

- Data path (adapters + pipeline + transforms + dedup)
- Gate / validation core (gate logic + ensemble + thresholds + schema)
- Evaluation (eval curator + grader + benchmark harness)
- Sandbox / execution (deterministic checks + subprocess + test harness)
- Schema / orchestration (trace checks + writers + CI hooks + smoke harness)

Design principles:
- Each slice has a coherent theme agents can stay focused on
- Overlap 1–2 files across slices for redundancy — same file audited twice catches more
- 4–5 slices is the sweet spot; 6+ diminishes returns from parallelism

### Step 2: Dispatch parallel audit agents

Dispatch N fast agents in a single message so they run concurrently. Each agent gets this prompt template:

```
Audit interconnections in the <SLICE_NAME> of a <SYSTEM_DESCRIPTION>. Static bug hunt — find bugs WITHOUT running the code.

Files to examine:
- <full absolute paths, 3-5 files>

Specific interconnections to verify:
- <list 5-10 specific cross-file checks>

Output format — one line per issue:
`[SEVERITY] file:line — issue description — specific fix`
Severities: CRITICAL (breaks pipeline), HIGH (silent incorrect behavior), MEDIUM (future bug waiting), LOW (style/cleanup).

Summary at end: count per severity + most critical theme + cross-cutting issue.

File-not-found = CRITICAL. Audit only — do NOT implement fixes.
```

### Step 3: Common checks to ask agents to look for

Adapt to domain, but these are generalizable across most pipelines:

- Import mismatches (caller imports symbol not exported from target)
- Function signature drift between definition and call sites
- Schema field produced in one file but not consumed downstream
- API contract violations (HTTP method, auth, payload shape, return type)
- Env var name inconsistency (defined in config vs referenced in code)
- Dead code paths / unused parameters
- Ensemble/combine logic divergence (same logic duplicated slightly differently across files)
- Feature-flag coupling (flag default-off silently disables whole subsystem)
- Silent fallbacks that mask errors (try/except swallowing)
- Atomicity on shared writes (append without tmp+rename)
- Threshold / calibration drift across files (hardcoded 0.5 here, 0.6 there)
- Race conditions on concurrent writes to shared state
- Shell control-flow bugs (set -e / set +e / PIPESTATUS interaction — commonly masks real failures)
- Model-server quirk violations (e.g., incompatible parameter combinations specific to your LLM runtime)
- Python-specific: `__init__.py` missing from new packages, relative-vs-absolute import drift, module shadowing (same name in multiple parent dirs)
- JavaScript/TypeScript-specific: default-export vs. named-export mismatch, `strict: false` silently masking type errors in one file and breaking callers, `tsconfig` path aliases resolving differently under build vs. test
- Java/JVM-specific: classpath ordering, SPI/ServiceLoader registration file drift, Gradle/Maven version conflicts that compile but fail at runtime
- Go-specific: package rename without go.mod update, interface satisfaction checks that pass locally but fail in CI due to build tags

### Step 4: Synthesize to ROOT CAUSES

After all N agents return, read all reports. Do NOT just aggregate bugs — extract root causes.

Target output: 2–5 causal drivers that explain 50–80% of surface findings.

Example synthesis from a typical run: a 4-agent swarm surfaced dozens of individual bugs; synthesis distilled them to three root causes:

1. **External service unreachable** — short timeout + fake-default fallback produced invented scores
2. **Feedback loop severed** — nothing emitted to the persistent memory layer at cycle boundaries
3. **Dead code path** — a patch existed but was never imported

Three causes explained most of the observed pathologies. The fix plan addressed the causes; the symptom-level bugs resolved as byproducts.

### Step 5: Emit numbered fix plan

Write to `PLAN_AUDIT_FIXES.md` (or similar):

```markdown
# PLAN: <System> audit fixes → smoke test → relaunch

## Context
<brief description of what the audit found + root causes>

## Environment
<relevant service endpoints, keys, paths>

## TASK 1 — <fix for root cause 1>
**Files**: <list>
### 1a. <subtask>
<code-level instruction>
### 1b. Smoke test for task 1
<command + expected output>

## TASK 2 — <fix for root cause 2>
...

## Pre-launch smoke matrix
Run ALL of these before relaunch. Each must PASS:
1. <service health check>
2. <model availability check>
3. <integration roundtrip>
4. <ingest sanity>
...

## Task-by-task record template
| Task | Status | Files touched | LOC | Smoke |
|---|---|---|---|---|
| 1 | Complete/Partial/Failed | ... | ~N | PASS/FAIL |
```

### Step 6: Hand to implementer

Copy-paste block for the implementer (could be you, another agent, a teammate):
- Reference to the audit plan file
- Stop-rules (don't skip tasks, run smoke between tasks, record the task-by-task table)
- Don't-touch list (services currently running, files mid-write, etc.)
- Completion criteria (pre-launch smoke matrix all PASS)

## Two variants of the pattern

**A. Fast swarm + synthesis agent (cheapest)**
- 4 fast agents in parallel
- 1 synthesis agent consolidates
- Best when scope is clear and you want maximum parallelism at minimum cost

**B. Swarm + self-synthesis (orchestrator holds the map)**
- N fast agents in parallel
- Synthesis done by the orchestrating Claude (not a separate agent)
- Best when you want the orchestrator to hold the full picture and reason across slices directly
- Fewer handoffs, richer cross-slice correlation

Both work. Use A when the scope is well-defined; use B when you want tighter orchestrator context for the synthesis.

## Output format for the synthesis report

```markdown
## Total issues surfaced

| Slice | CRITICAL | HIGH | MEDIUM | LOW |
|---|---|---|---|---|
| <slice 1> | N | N | N | N |
| <slice 2> | N | N | N | N |
...
| **TOTAL** | **N** | **N** | **N** | **N** |

## Root causes (synthesis — NOT surface bug list)

### 1. <Root cause title>
**Cause**: <what's actually broken>
**Surface symptoms**: <the N bugs that trace back to this>
**Fix**: <the single change that resolves this class of bugs>

### 2. <Root cause title>
...

## The N BLOCKERS (ordered — fix in sequence)

### 1. <TITLE>
File: <path:line>
Root cause: <1–3 above>
Fix: <specific change>
Smoke to verify: <command + expected>

...

## Cross-cutting themes
1. <theme> — affects <N> slices, <M> surface bugs, root cause #<K>
...

## Implementer copy-paste block
<block for the person/agent doing the fixes>
```

## Why the pattern works

- **Parallel discovery** — N agents in parallel surface all static bugs in minutes instead of hours of serial debug
- **Synthesis reduces cognitive load** — implementer gets 3–5 causes, not 70 bugs
- **Smoke gates enforce progress** — each task's fix is verified before moving on; bugs don't compound
- **Pre-launch matrix validates the whole** — final relaunch happens only when every integration point is healthy

## Operating notes

- Don't over-slice. 4–5 slices is right; 7+ adds coordination cost without improving coverage
- Don't skip synthesis. A raw bug list without root causes makes the implementer serial-debug again
- Don't wait for perfect slice boundaries — 20-minute fuzzy slices beat 2-hour perfect slicing
- The synthesis is worth doing yourself rather than via a sub-agent when you're about to hand off to an implementer — you need the mental model of the whole picture to write the fix plan correctly
- Severity is a gradient; the "blocker threshold" is context-dependent (tight deadline = tight threshold; general maintenance = looser)

## Evidence — representative runs

The pattern has been used on multi-file pipelines ranging from 10-file services to 20K-line codebases. Representative outcomes:

- **Small pipeline (~10 files):** 4 parallel agents surfaced ~70 issues (13 CRITICAL / 19 HIGH / 22 MEDIUM / 16 LOW) in about 5 minutes. 7 blockers extracted by synthesis, implemented in a single fix pass. Critical find: a shell control-flow bug that had masked real smoke failures for hours of serial debug.
- **Mid pipeline (~15 files):** 4 agents surfaced dozens of bugs, synthesis extracted 3 root causes. Implementer fixed all 10 tasks from the plan, post-fix system ran autonomously for 17 cycles.
- **Large codebase (~20K lines):** swarm audit across 6 modules identified plugin/skill gaps and service-integration defects in a single pass.
