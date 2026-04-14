# ELF Labs — Sovereign AI Infrastructure

**Emmelina Luna Fugler** — Independent Researcher | Harlan, Iowa | [github.com/ELF-LABS](https://github.com/ELF-LABS)

This repository is a living system, not a static portfolio. Every file references other files. Every measurement links to the code that produced it. Every claim links to timestamped evidence. A reviewer — human or AI — can follow any thread and find working infrastructure.

## The System at a Glance

```
4 machines (DGX Spark + Omen Desktop + P5 Mini PC + Physics Engine)
  + Tailscale mesh networking (3 nodes, expanding to 5)
  + 8 specialist LoRA adapters on Qwen3.5-4B (pattern-master trained on RTX 5090)
  + Limbic Sonar emotion-aware adapter routing via pattern LoRA
  + EverMemOS persistent memory (power-law temporal decay, 166 episodes, CV=4.82)
  + FalkorDB knowledge graphs (86 nodes, 335 edges, 31 resurrected theories)
  + Milvus vector DB (15 collections, 30K+ vectors)
  + Physics engine: PINNs, Neural ODEs, GNNs, signal filters (RTX 2080)
  + Deep Salvage: multi-modal pattern detection with neurobiological gates
  + Cloud burst training: RTX 5090 spot ($0.53/hr, 197x faster than desktop GPU)
  + Docker Compose infrastructure (6 stacks, 18+ containers, one-command deploy)
  + 200K+ lines of code across distributed system
  + Open-source: PIDForge (github.com/ELF-LABS/PIDForge)
  + Fractal engram paper (arXiv submission Apr 18, 2026)
```

Built in 4 months from Iowa on personal hardware. Zero external funding. ~$3 total cloud compute spend.

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
| Coven system CV | 4.824 | Live criticality measurement — system operates at edge of chaos |
| Machine memory CV | 5.09 | Upper range of human activity patterns — system is alive |
| Brain conversation CV | 62.67 | 10 decades spanned, microsecond to multi-week |
| Brain graphs analyzed | 800 | Small-world topology matches our knowledge graph |
| Resurrected theories | 31 | Deep Salvage engine: abandoned science validated against modern evidence |
| LoRA adapters deployed | 8 | Pattern-master (bf16 Blackwell), 7 specialists, DARE-TIES blending |
| Cross-domain bridges | 335 | FalkorDB edges connecting research across physics, biology, CS, cognition |
| Training cost (full fleet) | ~$3 | RTX 5090 spot at $0.53/hr — pattern-master in 52 min for $0.46 |
| December grimoire match | 135 | Geometric references from Dec 2025 independently converged with Apr 2026 architecture |

No published comparisons of AI memory system CV exist. These measurements are novel.

## Physics Engine — Neural Networks for Mathematical Validation

Language models guess at math. Physics doesn't. Every claim in the system gets a physics check before it becomes permanent.

| Model | Purpose | Params |
|-------|---------|--------|
| PINN (temporal) | Power-law criticality prediction from event timestamps | ~200K |
| Neural ODE | Cognitive state trajectory — predict phase transitions | ~100K |
| GNN (topology) | Knowledge graph analysis — link prediction, symmetry detection | ~500K |
| Spatial Bridge | Cross-model communication via fractal coordinate encoding | ~50K |

Plus: 7 signal filters (Kalman, Gaussian, wavelet, Butterworth, MAD, Savitzky-Golay, Isolation Forest) with an autotuner ported from FlightForge's FPV gyro filter math.

The physics engine runs on a separate GPU and validates every output from every LLM in the system. It's the immune system — language hallucinations don't survive physics checks.

## Deep Salvage — Multi-Modal Pattern Detection

Three parallel detectors process the same data through different lenses:

1. **Pattern LoRA** (intuitive): LLM-based pattern recognition trained on Luna's cognitive patterns
2. **Semantic Embeddings**: Vector similarity — what's textually related across 18K+ conversations
3. **Physics Engine**: Topological/geometric structure — what's mathematically isomorphic

Where all three agree = validated pattern. Where they disagree = the most interesting signal (active learning target for next training round).

Neurobiological gate system controls pipeline flow: dopamine (reward), serotonin (system load), GABA (redundancy suppression), glutamate (cross-domain excitation), acetylcholine (attention routing).

## Fractal Steering — Beyond Next Token Prediction

**Hypothesis**: Standard transformers predict the next token linearly. LoRA-steered MoE architectures can generate tokens that follow fractal paths through the latent space — the way thought actually works.

Each LoRA is not a personality switch but a **geometric observer position**. Multiple experts viewing the same input from different angles, cross-checking gradients, following the path of least resistance through the engram landscape. The resultant token generation moves fractally (multi-scale coherence) rather than linearly (one-step prediction).

**Testable**: Compare MFDFA singularity spectrum of base model vs pattern-LoRA-steered model outputs. Fractal steering should produce wider multifractal spectrum (complex dynamics) vs narrow spectrum (linear prediction).

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
