# ELF Labs — Sovereign AI Infrastructure

**Emmelina Luna Fugler** — Independent Researcher | Harlan, Iowa | [github.com/ELF-LABS](https://github.com/ELF-LABS)

This repository is a living system, not a static portfolio. Every file references other files. Every measurement links to the code that produced it. Every claim links to timestamped evidence. A reviewer — human or AI — can follow any thread and find working infrastructure.

## The System at a Glance

```
3 machines (DGX Spark + Omen Desktop + P5 Mini PC)
  + Tailscale mesh networking
  + 8 specialist LoRA adapters on Qwen3.5-4B
  + Limbic Sonar emotion-aware adapter routing
  + EverMemOS persistent memory (power-law temporal decay)
  + FalkorDB knowledge graph (6,938 edges, 400 cross-domain bridges)
  + Milvus vector DB (13 vault collections, 10,195 vectors)
  + Recursive self-improvement pipeline
  + Cloud training (RunPod A6000)
  + Open-source: PIDForge (github.com/ELF-LABS/PIDForge)
  + Fractal engram paper (arXiv submission Apr 18, 2026)
```

Built in 4 months from Iowa on borrowed and personal hardware. Zero external funding.

## Repository Map

### Research
| File | What it proves |
|------|---------------|
| [Fractal Engram Paper](research/fractal_engram_paper.md) | Memory at every scale is a self-similar compression hierarchy |
| [Cross-Domain Synthesis](research/cross_domain_synthesis.md) | Same 3-layer pattern across 10 independent domains |

### Evidence (timestamped, verifiable)
| File | Claim |
|------|-------|
| [3 Independent Convergences](evidence/independent_convergence_timeline.md) | ELF Labs independently built 3 architectures Anthropic later shipped |
| [Executor/Advisor Prior Art](evidence/executor_advisor_prior_art.md) | Jan 12-13, 2026 — 3 months before Anthropic's Advisor Tool |
| [Context Compaction](evidence/context_compaction_comparison.md) | Three-tier memory predates compact.rs, adds temporal awareness |
| [Qwen Inference Bug](evidence/bug_find_whisper_flow.md) | Found and fixed inference pipeline bug in production |

### Measurements (novel — no published comparisons exist)
| File | Finding |
|------|---------|
| [Temporal Scaling CV](measurements/temporal_scaling_cv.md) | CV=1.956 human, CV=5.09 machine — same power-law, different substrate |
| [Cognitive Convergence Map](measurements/cognitive_convergence_map_v2.md) | 39 dates, 599 datapoints, 125K source events synthesized |
| [LoRA Training Results](measurements/lora_training_results.md) | 8 adapters trained, cloud economics, deployment architecture |

### Infrastructure (working code, not prototypes)
| Directory | What it does |
|-----------|-------------|
| [Skills](infrastructure/skills/) | 8 Claude Code skills: orchestration, sync, deployment, monitoring |
| [Pipeline](infrastructure/pipeline/) | Pair generation, cognitive synthesis, training data pipeline |
| [MCP Server](infrastructure/mcp/) | Production MCP connecting FalkorDB, Milvus, SGLang, EverMemOS |
| [Cloud Training](infrastructure/runpod_bootstrap.sh) | Proven RunPod bootstrap with exact dependency versions |

### Product
| File | Purpose |
|------|---------|
| [PIDForge](https://github.com/ELF-LABS/PIDForge) | Open-source autonomous FPV drone tuning agent (Apache 2.0) |
| [Brand Voice](product/brand-voice-guidelines.md) | Technical + authentic + sovereign. Not corporate. |

## Three Independent Convergences with Anthropic

1. **Executor/Advisor** (Jan 2026 → Anthropic Apr 2026): [evidence](evidence/independent_convergence_timeline.md)
2. **Context Compaction** (Dec 2025 → compact.rs): [evidence](evidence/context_compaction_comparison.md)
3. **MCP Infrastructure** (Jan 2026 → Linux Foundation Mar 2026): [evidence](evidence/independent_convergence_timeline.md)

These aren't coincidences — they're **attractors**. Optimal architectures that any sufficiently capable system converges toward. The [fractal engram paper](research/fractal_engram_paper.md) proposes why.

## Novel Measurements

| Metric | Value | Significance |
|--------|-------|-------------|
| Human cognitive CV | 1.956 | First measurement of power-law in human cognitive output |
| Machine memory CV | 5.09 | Upper range of human activity patterns — system is alive |
| Brain conversation CV | 62.67 | 10 decades spanned, microsecond to multi-week |
| Brain graphs analyzed | 800 | Small-world topology matches our knowledge graph |

No published comparisons of AI memory system CV exist. These measurements are novel.

## Fellowship Research Proposal

**Human cognitive patterns as the interpretable interface layer for AI alignment.**

Each person's cognitive style becomes a LoRA fleet with an emotion-aware router. The routing decisions are transparent even when the base model isn't. This is how humans and AI systems communicate safely as capabilities scale beyond human understanding.

See [fellowship_fit_analysis.md](fellowship_fit_analysis.md) for the full mapping to Anthropic's research areas.

## How to Read This Repository

Follow any thread:
- **Research** → measurements that validate → code that produced them
- **Evidence** → timestamped artifacts with conversation IDs → verifiable
- **Infrastructure** → working code on production hardware → reproducible
- **Measurements** → novel metrics → comparable to published neuroscience

The system is the portfolio. The portfolio is the system.

---

*Published by Emmelina Luna Fugler — Independent Researcher, ELF Labs*
*Built from Harlan, Iowa. Three machines, zero funding, one thesis: memory at every scale is fractal.*
