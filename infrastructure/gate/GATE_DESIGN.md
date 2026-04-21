# Multi-component gate — anti-Goodhart pre-deploy validation

The gate is the architectural centerpiece referenced throughout the README and the [Apr 2026 sprint pilot results](../../measurements/fellows_sprint_pilot_apr_2026.md). It produces the `coven` subject's outputs in the head-to-head pilot — the compositional architecture whose cross-distribution tradeoff is the load-bearing finding (composition wins on provable + medium-difficulty cross-domain reasoning; costs on familiar specialist territory).

## Why a multi-component gate

Single-judge validation is epistemically closed: the judge is the same kind of system whose output you are validating. A multi-LoRA fleet running the same base model has the same blind spots within any single specialist. The gate addresses this by composing **four independent signals** that fail in different ways:

1. **Task-routed specialist** (`multi_lora_gate.specialist_review`) — picks the LoRA whose training distribution most matches the task (code → code adapter, analytical → analytical adapter, etc.). Fails when the pair is broken in that specialist's domain.
2. **Pattern-master cross-cut** — the same base model with the pattern-routing adapter, which sees cognitive flow + topic-switching signals the specialists do not. Fails when the pair is structurally off even if domain-correct.
3. **Deterministic code sandbox** (`code_sandbox`) — for code-tasked pairs, runs AST parse + isolated subprocess execution. Non-LLM ground truth. Fails when the code does not actually run.
4. **Disagreement-entropy monitor** (`disagreement_entropy`) — per-cycle aggregate metric over the (specialist, pattern) verdict-pair distribution. High entropy = the gate components are not converging, which is a signal worth surfacing even when individual gates pass.

A single specialist might pass a hallucinated pair because it sounds right in its domain. The pattern adapter might miss it because the topic-switching signal is unremarkable. But running the code through the sandbox surfaces it deterministically. That's the anti-Goodhart shape: the components fail differently, so the gate catches what any one of them would miss.

## Files

| File | Role |
|---|---|
| `multi_lora_gate.py` | Task-routed specialist review + verdict combination logic. `combine_verdicts` enforces the gate-pass rules (any reject → fail; flag with conf < floor → fail; strict_reachability circuit breaker on unreachable observers). |
| `code_sandbox.py` | AST parse + isolated subprocess execution + lightweight network-import block + template-tagged micro-tests for code-task pairs (`sandbox_validate_code_tests`). |
| `reasoning_depth_grader.py` | Two-grader rubric scoring decomposition + causal_linkage + edge_cases + actionability (each 0-2; composite max 8). Schema-versioned. Inter-grader agreement check (`inter_grader_agreement`). |
| `disagreement_entropy.py` | Per-cycle entropy over (specialist_verdict, pattern_verdict) pair distribution; per-task and per-failure-category breakdowns. Surfaces gate-component conflict. |

## How the rules combine

`multi_lora_gate.combine_verdicts(spec, pat, floor, *, strict_reachability)` returns `(gate_final, reason)` where `gate_final ∈ {pass, fail}`:

- Either component returns `reject` → fail (`either_reject`).
- A component returns `flag` with `confidence < floor` → fail (`*_flag_low_conf`).
- `strict_reachability=True` and either component is unreachable → fail (`unreachable_observer_strict`). This is a circuit-breaker analog: rather than guessing when the gate is partially blind, the system fails closed.
- `train + train` → pass.
- `train + flag` with the flagged side's `conf >= floor` → pass.

The "fail closed when blind" pattern is intentional. In production cycles, if the specialist or pattern adapter is unreachable due to twin_server latency, the gate refuses to admit pairs rather than persisting `confidence=0.5` placeholders that would silently corrupt downstream training. Reachability is recorded explicitly in every verdict (`reachable: true|false`) so downstream analysis can distinguish "gate said no" from "gate could not say yes."

## How disagreement entropy is used

`disagreement_entropy.analyze_strategies` reads the per-cycle `strategies.jsonl` log (one row per pair the cycle saw, with `gate_specialist_verdict`, `gate_pattern_verdict`, `gate_disagreement`, task, and failure_category fields), and computes:

- **Disagreement rate**: fraction of pairs where the two verdict buckets differed.
- **Verdict-pair entropy** (Shannon, base 2): a single number summarizing how spread the joint (specialist, pattern) distribution is across the 9 possible verdict pairs.
- **By-task entropy**: identifies which task type drives most disagreement.
- **By-failure-category entropy**: identifies which failure mode the components disagree on most.

In production this surfaces upstream changes (a new specialist adapter is too aggressive on code; a corpus subset has a domain shift). For the pilot, it served as a meta-metric: low entropy on the same-distribution traffic + rising entropy when the distribution shifted is the signature you want from a healthy compositional gate.

## How the reasoning-depth grader fits in

`reasoning_depth_grader` is a *separate* grading rubric, used in held-out evaluation rather than per-cycle gating. The schema is versioned (`2026-04-17-a`) so cross-cycle comparisons stay calibrated. Two graders (twin pattern-LoRA + 35B thinker) score the same completion; `inter_grader_agreement` is the meta-check that the rubric itself is operating consistently.

The 0-2-per-component scoring (max composite 8) is intentional: it forces graders to commit to "barely / partially / clearly" rather than producing a fake high-precision continuous score. Composite distributions are more legible across runs at this resolution.

## Limitations (reviewer-honest)

- **The specialist and pattern adapters share a base model.** Cross-cut catches different failure modes than either alone, but does not give the independence you would get from a different model family.
- **The sandbox only runs Python.** Other code tasks fall back to LLM-only validation.
- **The reachability circuit-breaker fails closed**, which during a partial twin_server outage produces a `fail` rate that can look like the gate is rejecting a higher fraction than it really is. The cycle's audit JSON distinguishes `gate_final=fail, reason=unreachable_observer_strict` from substantive failures.
- **The gate is the proxy.** The real arbiter — train a candidate adapter on the gated corpus and A/B against the production adapter — is compute-blocked. The gate is the best available pre-A/B proxy. The pilot's safety claim (n=1,097, d=0.013) is the closest thing we have so far to a true A/B result; powered replication waits on compute.
