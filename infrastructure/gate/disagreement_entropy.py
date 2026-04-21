"""Per-cycle disagreement rate + entropy over (specialist, pattern) verdict buckets.

Excerpted from the production self_improve module for portfolio review.
Imports `config` from a sibling module not included in this excerpt —
read for architecture and approach, not for standalone execution.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import config


def _entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c <= 0:
            continue
        p = c / total
        h -= p * math.log(p + 1e-12, 2)
    return h


def analyze_strategies(path: Path, *, cycle: int | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if cycle is not None and int(r.get("cycle", -1)) != cycle:
                continue
            if r.get("gate_specialist_verdict") is None:
                continue
            rows.append(r)

    pair_buckets: Counter[str] = Counter()
    by_task: dict[str, Counter[str]] = {}
    by_cat: dict[str, Counter[str]] = {}

    for r in rows:
        sv = str(r.get("gate_specialist_verdict", "?"))
        pv = str(r.get("gate_pattern_verdict", "?"))
        key = f"{sv}|{pv}"
        pair_buckets[key] += 1
        task = str(r.get("task", "unknown"))
        by_task.setdefault(task, Counter())[key] += 1
        cat = str(r.get("failure_category", "unknown"))
        by_cat.setdefault(cat, Counter())[key] += 1

    disagree_n = sum(1 for r in rows if r.get("gate_disagreement"))
    rate = disagree_n / len(rows) if rows else 0.0

    return {
        "rows": len(rows),
        "disagreement_rate": rate,
        "verdict_pair_entropy": _entropy(pair_buckets),
        "top_pairs": pair_buckets.most_common(12),
        "by_task_entropy": {t: _entropy(c) for t, c in by_task.items()},
        "by_failure_category_entropy": {c: _entropy(v) for c, v in by_cat.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategies", type=Path, default=config.OUT / "strategies.jsonl")
    ap.add_argument("--cycle", type=int, default=None)
    args = ap.parse_args()
    if not args.strategies.is_file():
        print(f"[disagreement_entropy] no file {args.strategies}", file=sys.stderr)
        sys.exit(1)
    out = analyze_strategies(args.strategies, cycle=args.cycle)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
