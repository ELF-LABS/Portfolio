# Anthropic Fellows Program — Fit Analysis

**Application deadline:** April 26, 2026
**Target cohort:** July 20, 2026
**Workstream:** Reinforcement Learning Fellows — RL environments, multi-component validation, training-data quality under self-improvement

## Why RL specifically

The ELF Labs self-improvement loop is an RL system: a policy (specialist LoRA fleet + cross-cut pattern adapter) acts on a corpus, a multi-component proxy provides the reward signal (until compute unlocks true A/B-LoRA arbitration), and trajectory data is logged for later analysis. The Apr 9–19, 2026 sprint produced the first statistically significant pilot data on this loop — see `measurements/fellows_sprint_pilot_apr_2026.md`.

## Three independent convergences with Anthropic

These are technical patterns that ELF Labs implemented before the corresponding Anthropic-shipped or -published version, with timestamps available in private logs.

### 1. Executor / Advisor pattern
- **ELF Labs:** Jan 12–13, 2026 — multi-agent system with ML-optimized model selection, designed for cost-bounded routing across a heterogeneous model fleet.
- **Anthropic:** April 2026 — Advisor Tool (public beta).
- **Evidence:** internal `implementation_plan.md` revisions 4 through 18, timestamped in research logs.

### 2. Context compaction
- **ELF Labs:** Three-tier memory architecture (HOT in-cache / WARM in-Redis / COLD in EverMemOS) with adaptive boundary detection driven by Bayesian surprise + entity-coherence + time gaps.
- **Anthropic:** `compact.rs` context-window management in claw-code.
- **Evidence:** `evidence/context_compaction_comparison.md` — full architectural comparison with empirical temporal-scaling data.

### 3. MCP infrastructure
- **ELF Labs:** Production MCP server (private, NDA), deployed prior to MCP standardization.
- **Anthropic:** Model Context Protocol contributed to Linux Foundation (10K+ servers as of Apr 2026).
- **Evidence:** Private deployment logs available on request.

## Pilot data (the load-bearing claim)

The Apr 9–19, 2026 sprint produced three statistically significant findings on a 1,500-row evaluation set across 26 reasoning domains. Headlines:

- **Compositional architecture wins on provable-answer regime:** Δ = +3.17, **p = 0.007**, n = 300, d = 0.316.
- **Compositional architecture wins on medium-difficulty cross-domain reasoning:** Δ = +4.27, **p = 0.005**, n = 322, d = 0.313.
- **Compositional architecture loses on familiar specialist territory (held-out):** Δ = −11.46, **p = 0.022**, n = 198, d = 0.327.
- **Self-improvement loop preserves baseline:** pattern vs. candidate adapter pooled n = 1,097, Δ = +0.32, p = 0.83, d = 0.013 (negligible).

Full methodology, per-domain results, and known caveats are documented in `measurements/fellows_sprint_pilot_apr_2026.md`. Total cloud compute spend for the sprint: ~$8 USD direct (RunPod / Vast 5090 spot); ~$80 total including AI tool subscriptions and utilities for the 10-day window; all on top of owned local hardware.

## Production infrastructure (not prototypes)

- **DGX Spark Blackwell:** Qwen3.5-35B production inference + Qwen3.5-4B twin with 7 trained QLoRA adapters via SGLang multi-LoRA serving.
- **EverMemOS:** Persistent four-tier memory pyramid (events → episodes → memcells → foresight), measured power-law temporal decay across 7 collections (CV ranging 1.78 to 3.28; see `measurements/temporal_scaling_cv.md`).
- **FalkorDB:** Knowledge graph with cross-domain bridges (count varies by snapshot; current scope ~400 edges across vault and research collections).
- **Milvus:** Hybrid retrieval substrate, 13 vault collections.
- **Self-improvement loop:** Observe → generate pairs → train candidate → benchmark → promote/discard → loop. Ran 17 autonomous cycles unattended in April 2026 (1,572 / 6,204 pairs processed before the planned wall-budget stop).

## Cross-disciplinary depth

- **Cross-domain synthesis** (`research/cross_domain_synthesis.md`): the Shell 1-2-3 lattice pattern observed across 10 independent literatures (anthropology, complex systems, ecology, economics, psychology, mathematics, transformer memory, sociology, ancient wisdom traditions).
- **Fractal Memory Engrams paper** (`research/fractal_engram_paper.md`): theoretical framework connecting AI memory architecture to neuroscience (Tononi IIT, Friston FEP, Josselyn–Tonegawa engram biology, Beggs–Plenz criticality).

## Alignment with past Fellow projects

- *Subliminal Learning* — pattern adapter captures cognitive-topology transmission across the LoRA fleet.
- *Open-source circuits* — FalkorDB knowledge graph traces concept connections.
- *Stress-Testing Model Specs* — Pipeline B 24-stress-file regime exercises the multi-component gate across 26 domains.
- *Strengthening Red Teams* — multi-component gate is a structural anti-Goodhart layer; the disagreement-entropy monitor surfaces gate-conflict states.
- *Skill Formation* — internal interaction logs measure knowledge-formation dynamics across the substrate.

## Key differentiator

We have shipped pilot data, not just architecture. The Apr 2026 sprint produced statistically significant cross-distribution findings on a small-model substrate with $80 total spend, executed against the ten-day Fellows-aware deadline. Fellowship compute would convert the underpowered per-domain results (game theory +38pp, n = 6; logic +22pp, n = 12; math +3.3pp, n = 33) into powered replications and enable true A/B-LoRA arbitration where the gate is currently a compute-blocked proxy.
