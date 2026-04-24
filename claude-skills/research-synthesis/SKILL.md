---
name: research-synthesis
description: Bidirectional cross-pollination engine for new projects. Pulls relevant patterns, code, data, and architecture FROM all of your existing projects INTO a new project, AND pushes new discoveries back OUT to existing projects simultaneously. Use this skill when starting a new project, researching a new product, designing a new system, or whenever someone says "research this", "design this new thing", "what do we already have that applies", "pull everything together for this", "convergence scan", or "what from our stack applies here". Also use when a new insight should flow back to update existing projects.
---

# research-synthesis: Bidirectional Cross-Pollination Engine

Most new projects reinvent things their parent organization already has. This skill prevents that by synthesizing knowledge flow in BOTH directions:

- **INWARD** — what from your existing projects, infrastructure, research, and patterns applies to this new project?
- **OUTWARD** — what does this new project reveal that updates or improves existing projects?

The skill is **project-list agnostic** — it relies on a project inventory you maintain (see setup below). Users are expected to keep their inventory fresh; the skill reads it at run-time.

## Setup (one-time, required)

Maintain a project inventory file at `~/.claude/projects-inventory.md` (default path; override with the `INVENTORY_PATH` env var if you prefer another location). The file should list each project with:

- Project name
- One-line purpose
- Key capabilities (patterns, architectures, data, code worth reusing)
- Relevant inward-questions — the kinds of new-project characteristics that should trigger a pull from this project

Minimal format:

```markdown
# Project Inventory

## <Project Name>
Purpose: <one line>
Provides: <list of reusable patterns, code paths, datasets>
Relevant when a new project: <list of trigger conditions>
```

**Example of a complete entry:**

```markdown
## user-auth-service
Purpose: JWT-based auth with refresh tokens + role-based access control
Provides: JWT signing/verification helpers, login flow, session middleware, role decorator
Relevant when a new project: needs user login, needs role-gated endpoints, needs session management, uses GraphQL or REST with auth
```

The skill reads this file each time it runs. Keep it updated as your stack evolves — usually adding a bullet or two at the end of each project takes under 30 seconds.

**New-project trigger:** Pass the new project's name and a one-line description when invoking the skill, either as an argument or in the trigger message (e.g. *"research-synthesis for new project: realtime-notifications — push notifications with server-sent events to our web clients"*). Without a named new project, the skill has nothing to synthesize against.

### Edge cases

- **Empty or missing inventory file:** Fail fast. Tell the user: *"Your inventory is empty at `<path>`. Add at least one project before running this skill."* Don't silently produce a blank synthesis.
- **Only 1–2 projects in inventory:** The INWARD phase will be small and the OUTWARD phase may find no connections. Focus on reusable patterns and gap identification rather than cross-project linkages.
- **Zero matches between new project and inventory:** Output an honest empty INWARD section ("no existing projects match this new direction") and make the RESEARCH NEEDED section larger. A new project with no inward pull is a sign you're in genuinely new territory — that's fine, flag it explicitly.
- **Project scope too small:** If the new work is under ~2 weeks and doesn't warrant a full synthesis pass, say so and suggest a lighter approach (e.g. a single inward-pull check against the 2–3 most likely source projects).

## Execution Flow

### Phase 1: INWARD — pull from existing stack

Read the project inventory. For the new project, scan each entry and ask:

- Does the new project exhibit patterns this project has already characterized?
- Is there code, data, or infrastructure from this project the new project can reuse?
- Does this project's architecture transfer?
- What's missing that needs research or new build?

Produce an **inward pull map** — for each relevant source project, a line or two about what specifically carries over.

### Phase 2: OUTWARD — push discoveries back

For each insight the new project generates, ask:

- Which existing project does this improve?
- Does this create a new connection between two existing projects?
- Does this change the priority of any existing project?
- Does this generate new training data, test cases, or insights for existing systems?
- Does this reveal a pattern missed in existing projects?

Produce an **outward push list** — for each improvable existing project, what the update is.

### Phase 3: Research gaps

For each integration point the new project needs, identify:

- What you already have (code, data, infrastructure)
- What you need to research (APIs, protocols, libraries, recent papers)
- What you need to build (new code, new pipelines)
- What you can reuse by adapting from another project

### Output Format

```
═══ RESEARCH SYNTHESIS: [New Project Name] ═══

## INWARD (existing → new)

FROM [Project]: [What applies]
  Code: [specific files/functions to reuse]
  Data: [specific datasets/collections]
  Pattern: [architectural pattern that transfers]
  Gap: [what's missing, needs research]

[Repeat for each relevant source project]

## OUTWARD (new → existing)

TO [Project]: [What this reveals/improves]
  Update: [specific change needed]
  New connection: [link between projects that didn't exist]

## RESEARCH NEEDED

| Topic | Why | Priority | Method |
|-------|-----|----------|--------|
| [Topic] | [Why we need it] | P0/P1/P2 | Web search / code review / prototype |

## ARCHITECTURE DECISION

Based on inward pull + research:
[The recommended architecture, using maximum existing infrastructure]

═══════════════════════════
```

## Key Principle

**Every new project should use 80%+ existing infrastructure.** If you're building from scratch, you're not looking hard enough at what already exists. Most codebases reuse the same architectural patterns — find the existing version and adapt it, rather than re-deriving the same architecture.

If 80%+ reuse feels too high for your context: first check whether the new project is genuinely new, or whether it's scope-creep on something that already exists. Sometimes a "new project" is actually the right-sized feature branch of an existing one.

## Why run it in both directions

Inward alone makes new projects cheaper. Outward alone makes existing projects sharper. Running both simultaneously is the only way to keep a portfolio of projects from drifting into unconnected silos where the left hand has built the thing the right hand is about to rebuild.

## Pairs well with

- **sync-pollinate** — runs at the end of each working session and propagates findings across existing projects; research-synthesis runs at the start of a new project and propagates the existing stack into the new work
- A well-maintained project inventory — without it, the skill has nothing to scan
