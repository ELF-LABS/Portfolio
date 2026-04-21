# ELF Labs — Compositional Multi-LoRA Architecture for Specialist Reasoning Under Compute Constraint

**Emmelina Luna Fugler** | Independent Researcher | [radiantfrequency.xyz](https://radiantfrequency.xyz) | [github.com/ELF-LABS](https://github.com/ELF-LABS)

## Headline finding

A 1,500-row pilot study (Apr 9–19, 2026) demonstrates that a compositional multi-component architecture lifts capability above any single-specialist ceiling — most visibly where the specialist alone cannot solve the task — while exhibiting a measurable cost on familiar specialist territory. Three findings cross conventional significance thresholds, and the self-improvement loop preserves the baseline:

- **Compositional gains on provable-answer regime:** Δ = +3.17, **p = 0.007** (n = 300, d = 0.316).
- **Compositional gains on medium-difficulty cross-domain reasoning:** Δ = +4.27, **p = 0.005** (n = 322, d = 0.313).
- **Compositional cost on familiar held-out specialist territory:** Δ = −11.46, **p = 0.022** (n = 198, d = 0.327).
- **Self-improvement loop preserves baseline:** pattern vs. candidate adapter pooled n = 1,097, p = 0.83, d = 0.013 (negligible). Validates the multi-component gate as anti-reward-hacking architecture.

Underpowered but directionally large per-domain results (n small, future-work anchors): **game theory +38pp** (n = 6, d = −1.20 very large), **logic +22pp** (n = 12, d = −0.78 medium-large), **math +3.3pp** (n = 33).

Total cloud spend for the sprint: **~$8 USD** (RunPod / Vast 5090 spot training); **~$80 total sprint cost** including AI-tool subscriptions and utilities prorated for the 10-day window; on top of owned local hardware.

Full methodology, per-domain results, and known caveats: [`measurements/fellows_sprint_pilot_apr_2026.md`](measurements/fellows_sprint_pilot_apr_2026.md).

## What this is

A reinforcement-learning-style self-improvement loop for specialist reasoning, implemented end-to-end on a small-model substrate (Qwen3.5-4B + 7 task-specialist QLoRA adapters), validated through a multi-component anti-Goodhart gate (task-routed specialist + pattern-master cross-cut + deterministic code sandbox + disagreement-entropy monitor), running over persistent tiered memory (event_log → episodes → memcells → foresight) measured to operate at power-law temporal scaling.

The Apr 9–19 sprint produced the first statistically significant pilot data on this architecture. The system is designed for the regime where compute is constrained and the open question is *how much architectural composition can substitute for scale*.

## Architecture

| Component | Role |
|---|---|
| Base model | Qwen3.5-4B (dense, multimodal) |
| Specialist fleet | 7 trained QLoRA adapters (identity, code, writer, ops, sales, analytical, pattern) + 1 auxiliary (flight-tuning, rank 16) |
| Multi-component gate | Task-routed specialist + pattern-master cross-cut + deterministic code sandbox + disagreement-entropy monitor |
| Self-improvement loop | Observe → generate pairs → train candidate adapter → A/B against production → promote/discard → repeat |
| Memory substrate | EverMemOS — four-tier semantic pyramid (events → episodes → memcells → foresight) mirrored across MongoDB + Elasticsearch + Milvus |
| Inference serving | SGLang multi-LoRA with per-request adapter routing |
| Hardware | 3-machine local stack: DGX Spark Blackwell (119 GB unified) + Omen Desktop (RTX 2080) + P5 mini-PC orchestrator |
| Cloud burst training | RunPod / Vast 5090 spot, ~$0.46 per adapter, ~52 min per adapter |

## Repository map

### Measurements
- [`measurements/fellows_sprint_pilot_apr_2026.md`](measurements/fellows_sprint_pilot_apr_2026.md) — full Apr 9–19 sprint methodology, per-domain raw results across 26 domains, and rigorous statistics.
- [`measurements/temporal_scaling_cv.md`](measurements/temporal_scaling_cv.md) — power-law decay measurement on the EverMemOS memory substrate (CV ranging 1.78 to 3.28 across collections; 5–10 decades spanned).
- [`measurements/lora_training_results.md`](measurements/lora_training_results.md) — adapter fleet training economics, configurations, and operational notes.

### Evidence
- [`evidence/independent_convergence_timeline.md`](evidence/independent_convergence_timeline.md) — chronology of three architectures built before public Anthropic-shipped equivalents (timestamped from internal logs).
- [`evidence/context_compaction_comparison.md`](evidence/context_compaction_comparison.md) — head-to-head with Anthropic's `compact.rs` from claw-code.
- [`evidence/executor_advisor_prior_art.md`](evidence/executor_advisor_prior_art.md) — executor/advisor pattern timeline.
- [`evidence/bug_find_whisper_flow.md`](evidence/bug_find_whisper_flow.md) — production debugging case study.

### Research
- [`research/fractal_engram_paper.md`](research/fractal_engram_paper.md) — working paper bridging neuroscience (Tononi IIT, Friston FEP, Josselyn–Tonegawa engram biology, Beggs–Plenz criticality) to AI memory architecture.
- [`research/cross_domain_synthesis.md`](research/cross_domain_synthesis.md) — Shell 1-2-3 lattice pattern observed across 10 independent literatures, with devil's-advocate critique section.

### Infrastructure

**Training pipeline** ([`infrastructure/training/`](infrastructure/training/) — see [`TRAINING_PIPELINE.md`](infrastructure/training/TRAINING_PIPELINE.md) for narrative)
- [`train_baseline_lora.py`](infrastructure/training/train_baseline_lora.py) — QLoRA training script (NF4 + DoRA + LoRA+ + OLoRA init) with `DivergenceTripwireCallback` that aborts the run when loss explodes (caught the Apr 17 pod-1 catastrophic-forgetting incident at step ~105 without operator intervention).
- [`vast_bootstrap_5090.sh`](infrastructure/training/vast_bootstrap_5090.sh) — proven bootstrap recipe for RTX 5090 spot pods. The four critical fixes (TORCHDYNAMO_DISABLE, TOKENIZERS_PARALLELISM, dataloader_pin_memory, kill compile workers) take step time from 88 s to 18 s.
- [`start_baseline_train.sh`](infrastructure/training/start_baseline_train.sh) — launcher with env+venv source.

**Multi-component gate** ([`infrastructure/gate/`](infrastructure/gate/) — see [`GATE_DESIGN.md`](infrastructure/gate/GATE_DESIGN.md) for narrative)
- [`multi_lora_gate.py`](infrastructure/gate/multi_lora_gate.py) — task-routed specialist + pattern-master cross-cut + verdict-combination logic with strict-reachability circuit breaker.
- [`code_sandbox.py`](infrastructure/gate/code_sandbox.py) — deterministic AST + isolated subprocess execution sandbox for code-task pairs (non-LLM ground truth).
- [`reasoning_depth_grader.py`](infrastructure/gate/reasoning_depth_grader.py) — schema-versioned 4-component rubric (decomposition, causal_linkage, edge_cases, actionability) + inter-grader agreement check.
- [`disagreement_entropy.py`](infrastructure/gate/disagreement_entropy.py) — per-cycle Shannon entropy over (specialist, pattern) verdict-pair distribution; surfaces gate-component conflict.

**Self-improvement loop** ([`infrastructure/self_improve/`](infrastructure/self_improve/) — see [`LOOP_DESIGN.md`](infrastructure/self_improve/LOOP_DESIGN.md) for narrative)
- [`target_curve.py`](infrastructure/self_improve/target_curve.py) — exponential decay setpoint trajectory (the SETPOINT stream of the Black Box).
- [`blackbox.py`](infrastructure/self_improve/blackbox.py) — per-cycle trace recorder with atomic writes + size-rotated master log; computes `gap_exec` and `gap_model`.

**Cloud + deployment**
- [`infrastructure/runpod_bootstrap.sh`](infrastructure/runpod_bootstrap.sh) + [`infrastructure/train_queue.sh`](infrastructure/train_queue.sh) — generic cloud GPU training pod setup and queue management (legacy A6000 path, before the 5090 sprint).
- [`infrastructure/skills/deploy-adapters.md`](infrastructure/skills/deploy-adapters.md) — adapter deployment pipeline (download from cloud, back up, deploy to inference, restart, verify).

### Open source
- [PIDForge](https://github.com/ELF-LABS/PIDForge) — Apache 2.0 signal-processing toolkit for FPV flight-controller PID tuning. Rule-based; no LLM.

## Comparison to prior art

This work sits at the intersection of two recent literatures:

- **MoE scaling laws** (Fedus et al. and successors) characterize how mixture-of-experts models scale, but assume a fixed within-model gating architecture.
- **Multi-agent coordination scaling** (Kim et al., 2025, "Towards a Science of Scaling Agent Systems," arXiv 2512.08296) — mixed-effects regression on agent topology and verification cross-cut, identifying topology-dependent error cascades (Independent 17.2× vs Centralized 4.4×) and capability-matched specialists as load-bearing.
- **Active learning via disagreement** (Query-by-Committee, Seung et al., 1992) treats disagreement between hypothesis ensembles as an exploration signal.
- **Adapter-as-action RL** (Brandfonbrener et al., ScaleRL; Duan et al., latent memories) treats low-rank adapters as a discrete action space.

This architecture differs in three respects: (1) the gate composition is task-routed per request rather than statically wired; (2) the verification cross-cut is multi-component (specialist routing + pattern-master + deterministic sandbox + disagreement-entropy monitor); (3) the self-improvement loop operates as a compute-blocked proxy for true A/B-LoRA arbitration, which becomes the primary arbiter when compute unlocks.

## Methodology footnote

Pilot evaluations used a Qwen3.5-35B local judge as primary, with cloud cross-family judges (Llama 3.3 70B via Groq; GLM-4.7-Flash via Z.ai) where rate-limits permitted. Most cells fell back to single-judge under cloud-judge timeouts. Comparison between subjects within each cell is preserved (same judge, same prompt); absolute scores carry less cross-cell calibration than a triple-judge ensemble would have provided. Significance is reported via Welch *t*-tests with Cohen's *d* effect sizes; per-domain results with small *n* are reported as directional and explicitly flagged. The compositional-subject (`coven`) path queried a Milvus instance that did not contain the research-corpus collection during the run; same-degraded-compositional on both pipelines preserves the comparison. Future work: powered replication with research-corpus enrichment.

## About

ELF Labs is a solo research operation in Harlan, Iowa. The thesis: one researcher with sovereign infrastructure, willing to invest meaningful personal money in compute and AI tooling, can produce empirically grounded pilot data on architectures that would conventionally require a team.

The system runs on owned hardware (3 machines). Cloud compute is used for burst training only. The ~$8 direct cloud spend for the Apr 9–19 pilot sits on top of approximately $120/month in AI-tool subscriptions (Claude Max + Cursor Pro) and ongoing utilities — total ten-day sprint cost ~$80 of personal money. The system trains itself, monitors its own state, and generates its own training data.

Compute funding from a research fellowship would convert the underpowered per-domain results (game theory +38pp, n = 6; logic +22pp, n = 12; math +3.3pp, n = 33) into powered replications, and would unlock the true A/B-LoRA arbitration that the multi-component gate is currently approximating.

---

*Emmelina Luna Fugler — Independent Researcher, ELF Labs*
*Contact: [elf@radiantfrequency.xyz](mailto:elf@radiantfrequency.xyz) · [radiantfrequency.xyz](https://radiantfrequency.xyz)*
