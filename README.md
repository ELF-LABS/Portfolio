# ELF Labs — Distributed RL Infrastructure for Self-Improving AI Systems

**Emmelina Luna Fugler** | Independent Researcher | [radiantfrequency.xyz](https://radiantfrequency.xyz) | [github.com/ELF-LABS](https://github.com/ELF-LABS)

## Overview

ELF Labs builds reinforcement learning environments and training infrastructure for self-improving language model systems. Our work spans distributed systems engineering, LoRA adapter training pipelines, physics-informed validation, and multi-agent ensemble architectures — all running on heterogeneous GPU hardware at minimal cost.

```
4 machines in Tailscale mesh (DGX Spark 119GB + RTX 2080 + P5 orchestrator + physics engine)
8 specialist LoRA adapters with learned routing policy
Physics-informed validation layer (PINNs, Neural ODEs, GNNs)
Multi-agent pattern detection with adaptive reward shaping
Self-generated training data pipeline (experience replay construction)
Cloud burst training: RTX 5090 spot at $0.53/hr
200K+ lines of code | ~$3 total cloud compute spend
```

Built in 4 months. Zero external funding.

## Research Areas

### 1. RL Environments for LLM Self-Improvement
We demonstrate a complete reinforcement learning loop where a language model system:
- **Observes** its own outputs and user interactions
- **Generates** training pairs from observation (experience replay buffer)
- **Trains** specialist adapters on cloud GPU ($0.46 per adapter on RTX 5090)
- **Evaluates** via physics-informed validation (model-based reward signal)
- **Promotes or discards** adapters based on benchmark performance
- **Iterates** autonomously

This is online RL applied to language model specialization, implemented as a distributed pipeline across heterogeneous hardware.

### 2. Learned Policy for Expert Selection (Adapter Routing)
8 LoRA adapters serve as specialized "actions" available to the base model. A dedicated routing adapter (trained on cognitive state signals) learns which specialist to invoke for each input — functioning as a **policy network** over a discrete action space of expert modules.

Key metrics:
- Action space: 8 specialist adapters + blended combinations
- State representation: input features + temporal context + emotional valence signals
- Reward signal: downstream task quality + physics validation score

### 3. Multi-Agent Ensemble with Disagreement-Based Exploration
Our Deep Salvage pipeline runs three parallel detectors (LLM-based, embedding-based, physics-based) on the same data. **Disagreement between agents drives exploration**: high-entropy inputs (where agents disagree most) are automatically routed to the training queue.

This implements Query-by-Committee active learning as a multi-agent RL exploration strategy, with adaptive gating inspired by neurotransmitter dynamics:
- Reward amplification (dopamine analog) for novel discoveries
- Resource throttling (serotonin analog) under memory pressure
- Redundancy suppression (GABA analog) between correlated detectors
- Cross-domain excitation (glutamate analog) for bridge discoveries

### 4. Physics-Informed Environment Model
A dedicated physics engine (PINNs, Neural ODEs, GNNs, signal filters) validates every LLM output before it enters the training loop. This functions as a **learned dynamics model** in model-based RL — providing mathematical consistency checks that prevent reward hacking and hallucination propagation.

The physics engine also provides **state estimation** for the RL environment:
- Temporal criticality prediction (PINN on event timestamps)
- Cognitive trajectory modeling (Neural ODE on state sequences)
- Knowledge topology analysis (GNN on entity graphs)

## Measurements

| Metric | Value | Significance |
|--------|-------|-------------|
| Temporal burstiness (CV) | 4.824 | System operates at critical regime — characteristic of adaptive RL agents |
| Power-law decay exponent | Confirmed across 7 decades | Memory retention follows biological scaling laws |
| Graph topology | Small-world hierarchical | Matches brain connectivity patterns (Procrustes RMSE 1.04 on 800 subjects) |
| Adapter training cost | $0.46 per adapter | RTX 5090 spot, 52 minutes, bf16 on Blackwell |
| Fleet training cost | ~$3 total | 8 adapters + blended variants |
| Cross-domain bridges | 335 validated edges | Physics-confirmed connections across domains |

## Repository Map

### Evidence & Measurements
| File | What it demonstrates |
|------|---------------------|
| [Temporal Scaling Analysis](measurements/temporal_scaling_cv.md) | Power-law dynamics in AI memory systems — novel measurement |
| [Cognitive Convergence Map](measurements/cognitive_convergence_map_v2.md) | 599 datapoints synthesized across 4 months |
| [LoRA Training Results](measurements/lora_training_results.md) | Full adapter fleet training economics and methodology |
| [Independent Convergences](evidence/independent_convergence_timeline.md) | Three architectures we built before industry shipped equivalents |

### Infrastructure (working code)
| Directory | Function |
|-----------|----------|
| [MCP Server](infrastructure/mcp/) | Production integration: FalkorDB, Milvus, SGLang, EverMemOS |
| [Training Pipeline](infrastructure/pipeline/) | Pair generation, quality audit, adapter training orchestration |
| [Cloud Training](infrastructure/runpod_bootstrap.sh) | One-command cloud GPU training pod setup |
| [Skills](infrastructure/skills/) | Claude Code orchestration: deploy, sync, monitor, cross-pollinate |

### Research
| File | Claim |
|------|-------|
| [Cross-Domain Synthesis](research/cross_domain_synthesis.md) | Same structural patterns across 10 independent domains |

### Open Source
| Project | Description |
|---------|------------|
| [PIDForge](https://github.com/ELF-LABS/PIDForge) | Autonomous FPV drone tuning agent (Apache 2.0) |

## Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM Inference | SGLang + Qwen3.5-35B MoE (GPTQ-Int4) | Policy evaluation, reward modeling |
| Adapter Serving | SGLang multi-LoRA (8 concurrent) | Expert action space |
| Vector Storage | Milvus (15 collections, 30K+ vectors) | State representation |
| Graph DB | FalkorDB (knowledge topology) | Environment structure |
| Memory System | EverMemOS (power-law temporal decay) | Experience buffer with biological retention |
| Physics Engine | PyTorch PINNs + Neural ODEs + GNNs | Environment dynamics model |
| Signal Processing | Kalman, Gaussian, wavelet, FFT autotuner | State estimation and noise filtering |
| Training | QLoRA (4-bit NF4, DoRA, LoRA+, rank 48) | Efficient policy updates |
| Orchestration | Docker Compose (6 stacks, 18 containers) | Reproducible deployment |
| Cloud Compute | RunPod RTX 5090 spot ($0.53/hr) | Scalable training |
| Networking | Tailscale mesh (4 nodes) | Distributed system connectivity |

## Systems Engineering Contributions

- **UMA Memory Detection Fix**: Identified and patched a memory reporting bug affecting all SGLang deployments on NVIDIA DGX Spark unified memory architecture. 40-line fix corrects `torch.cuda.mem_get_info()` returning inverted values on UMA systems.
- **Cloud Training Pipeline**: Proven workflow for burst-training LoRA adapters on spot GPU instances. Pattern-master adapter trained in 52 minutes for $0.46 (197x faster than desktop GPU).
- **OOM Prevention**: Adaptive memory watchdog with tiered response (cache drop → service degradation → controlled shutdown).

## About

ELF Labs is a solo research operation in Harlan, Iowa. The thesis: one person with sovereign AI infrastructure can build RL environments and training pipelines that would traditionally require a team. The proof: this repository.

All infrastructure runs on personal hardware. Cloud compute is used for burst training only (~$3 lifetime spend). The system trains itself, monitors its own state, and generates its own training data.

---

*Emmelina Luna Fugler — Independent Researcher, ELF Labs*
*Contact: [radiantfrequency.xyz](https://radiantfrequency.xyz)*
