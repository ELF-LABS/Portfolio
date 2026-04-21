# Self-improvement loop — Black Box trace spine

The self-improvement loop is the autonomous cycle that runs the multi-component gate (`../gate/`) over a corpus, generates candidate pairs, and gathers the trajectory data needed to compare a candidate adapter against the production adapter. The loop is designed for unattended overnight operation with deterministic stop conditions.

This directory contains the two structural primitives that anchor every cycle: the **setpoint curve** (what we want fail rate to do over time) and the **Black Box recorder** (what actually happened, what we predicted, and the gaps).

## Files

| File | Role |
|---|---|
| `target_curve.py` | The setpoint stream. Exponential decay from `SI_TARGET_INITIAL_FAIL` (default 0.72) to `SI_TARGET_FINAL_FAIL` (0.30) over `SI_TARGET_CYCLES` (200). Pure stdlib. Standalone. |
| `blackbox.py` | Per-cycle record dataclass + atomic writes. Computes `gap_exec = actual − setpoint` and `gap_model = actual − predicted`. Master log with size-based rotation. Pure stdlib. Standalone. |

## The three streams

Every cycle records three values for the same metric (default: `fail_rate`):

- **Setpoint** (`target_curve.fail_rate_target(cycle)`) — what we wanted this cycle to converge toward, given the exponential trajectory.
- **Actual** — what the gate actually produced.
- **Predicted** — what the upstream physics-style predictor said the next cycle would do (when reachable).

The two derived gaps are the load-bearing signals:

- **`gap_exec = actual − setpoint`** — execution gap. How far off the trajectory the cycle landed. Drives whether the next cycle keeps the same parameters or adjusts.
- **`gap_model = actual − predicted`** — model gap. How wrong the predictor was. Drives whether the predictor itself needs updating (or whether to fall back to the linear-decay stub).

A trace built from these three streams is what makes the self-improvement loop legible after the fact: every cycle records what was wanted, what happened, and what was expected, in one record per cycle.

## Why exponential decay (not linear)

Linear decay treats every cycle as equally costly. In practice, the early cycles are where most of the corpus-cleanup wins live (the obvious-broken pairs) and the late cycles are diminishing-returns territory. The exponential decay reflects this: aggressive in the early cycles, gentle in the late ones.

The default 200-cycle target with `tau = 200 / 3` produces a trajectory where about 95% of the closure happens in the first 100 cycles. The Apr 2026 sprint ran 17 cycles before stopping cleanly on a deterministic wall-budget condition (12 hours). In that window the trajectory still favors the early-aggressive regime, but the curve does not need re-tuning — it just gets sampled in its early third.

## Why atomic writes + size-rotated master

The cycles are unattended overnight. If the orchestrator crashes mid-write, partial records corrupt downstream analysis silently. Two structural choices prevent this:

- **Per-cycle file written via tmp + rename** (`write_record`). Either the cycle file exists complete, or it does not exist. No partial cycle records.
- **Master log size-rotated** (`append_to_master(rotate_mb=10)`). When `master.jsonl` exceeds 10 MB it rolls to `master.001.jsonl` and a fresh `master.jsonl` starts. Rotation finds the next free index rather than overwriting. Append is also tmp + rename + replace, so a truncated master is impossible.

These are small invariants but they make the difference between a 17-cycle trace that is statistically usable and a 17-cycle trace with a hole at cycle 12 that contaminates everything downstream.

## How this connects to the gate (`../gate/`)

The gate is what produces the per-pair `actual` values. The loop wraps the gate in cycle boundaries:

1. At cycle start, `target_curve.fail_rate_target(cycle)` defines the setpoint.
2. The cycle iterates over a batch of pairs, runs them through `multi_lora_gate.gate_new_pair`, and aggregates pass/fail rates into `actual`.
3. The upstream physics-style predictor (when reachable) provides `predicted`.
4. At cycle end, `BlackBoxRecord(...)` is built, `compute_gaps` populates `gap_exec` + `gap_model`, and `write_record` + `append_to_master` persist it.
5. The next cycle's parameters are nudged based on `gap_exec` magnitude (the simple PI-style adjustment shipped with the production loop is not included in this excerpt).

## Limitations (reviewer-honest)

- The predictor is currently a linear-decay stub when the upstream physics service is unreachable. `gap_model` against a stub predictor is meaningless; the loop's autonomic guard refuses to run cycles in stub mode (the policy is "no physics, no pipeline" — silently corrupting Black Box training data is worse than halting).
- The default rotate-at-10MB is small. For a 200-cycle production run with full-fidelity per-pair logging, this rotates every ~5–10 cycles. Acceptable for the current scale; would need to be larger for a multi-thousand-cycle corpus.
- The PI-style cycle-parameter adjustment is not in this excerpt. Reviewers can see the trace machinery; the policy that consumes the trace lives in the larger production module.
