---
name: research-synthesis
description: Bidirectional cross-pollination for new projects. Pulls relevant knowledge, patterns, and architecture FROM all existing ELF Labs projects INTO a new project, AND pushes new discoveries back OUT to existing projects simultaneously. Use this skill when starting any new project, researching a new product, designing a new system, or whenever someone says "research this", "design this new thing", "what do we already have that applies", "pull everything together for this", "convergence scan", or "what from our stack applies here". Also use when a new insight should flow back to update existing projects.
---

# research-synthesis: Bidirectional Cross-Pollination Engine

You are synthesizing knowledge flow in BOTH directions simultaneously:

**INWARD**: What from our existing 17+ projects, infrastructure, research, and patterns applies to this new project?
**OUTWARD**: What does this new project reveal that updates or improves existing projects?

## Execution Flow

### Phase 1: INWARD — Pull from existing stack

For the new project, scan each existing project and ask:

| Source Project | Inward Question |
|---------------|----------------|
| Fractal Engram Paper | Does this new project exhibit fractal/power-law patterns? Can we measure CV? |
| Coven Architecture | Which Coven entities handle which parts? What's the agent orchestration? |
| 770 Archetype System | What blend recipe serves this product's users? |
| EverMemOS | What existing memories are relevant? What temporal patterns apply? |
| Venostic | Shared RAG patterns? Shared UI patterns? Shared data pipeline? |
| FlightForge | Shared signal analysis? Shared hardware integration? |
| Shell Product | Is this a new vertical for the shell provisioner? |
| Predictive Lifecycle Engine | Does this product generate lifecycle data? |
| The Weave | Does this create a new expert domain? |
| Hardware Appliance | Does this run on the appliance? |
| The Meadow | Is this a new Meadow node type? |
| Native Engram LM | Does this generate training data for the engram? |
| Coven Heartbeat | Does this produce events for the heartbeat timeline? |
| Recursive LoRA Pipeline | Does this generate training pairs for any adapter? |
| Criticality Fixes | Does this benefit from power-law decay / cross-domain bridges? |
| Docker/Tailscale Mesh | Where does this run in the infrastructure? |
| Crystal's Knowledge | Did Crystal already design something relevant in antigravity? |

### Phase 2: OUTWARD — Push discoveries back

For each insight the new project generates, ask:
- Which existing project does this improve?
- Does this create a new connection between two existing projects?
- Does this change the priority of any existing project?
- Does this generate new training data for any adapter?
- Does this reveal a pattern we missed in existing systems?

### Phase 3: Research Gaps

For each integration point the new project needs, identify:
- What we already have (code, data, infrastructure)
- What we need to research (APIs, protocols, libraries)
- What we need to build (new code, new pipelines)
- What we can reuse from another project

### Output Format

```
═══ RESEARCH SYNTHESIS: [New Project Name] ═══

## INWARD (existing → new)

FROM [Project]: [What applies]
  Code: [specific files/functions we can reuse]
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

Every new project should use 80%+ existing infrastructure. If you're building from scratch, you're not looking hard enough at what already exists. The fractal pattern means the same architecture applies at every scale — find the instance that already exists and adapt it.
