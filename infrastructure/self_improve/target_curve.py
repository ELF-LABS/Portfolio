"""Setpoint target curve - what fail_rate trajectory we want.

Exponential decay from baseline to target over N cycles.
This is the SETPOINT stream of the Black Box.

Standalone module — pure stdlib + math. Defaults configurable via env:
- SI_TARGET_INITIAL_FAIL (default 0.72)
- SI_TARGET_FINAL_FAIL   (default 0.30)
- SI_TARGET_CYCLES       (default 200)
"""
from __future__ import annotations

import math
import os

TARGET_INITIAL_FAIL = float(os.environ.get("SI_TARGET_INITIAL_FAIL", "0.72"))
TARGET_FINAL_FAIL = float(os.environ.get("SI_TARGET_FINAL_FAIL", "0.30"))
TARGET_CYCLES = int(os.environ.get("SI_TARGET_CYCLES", "200"))
DECAY_TAU = TARGET_CYCLES / 3.0

TASK_TYPES = ("code", "identity", "docs", "convo", "analytical", "meta")


def fail_rate_target(cycle: int) -> float:
    """Exponential decay from INITIAL to FINAL over TARGET_CYCLES."""
    if cycle <= 0:
        return TARGET_INITIAL_FAIL
    decay = math.exp(-cycle / DECAY_TAU)
    return TARGET_FINAL_FAIL + (TARGET_INITIAL_FAIL - TARGET_FINAL_FAIL) * decay


def task_dist_target(cycle: int) -> dict[str, float]:
    """Uniform distribution initially. Future: shift with task_focus."""
    _ = cycle
    w = 1.0 / len(TASK_TYPES)
    return {t: w for t in TASK_TYPES}


def next_cv_target(cycle: int) -> float:
    """Ideal CV placeholder."""
    _ = cycle
    return 1.0
