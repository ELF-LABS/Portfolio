"""Black-box cycle records → per-cycle file + master.jsonl (Fellows trace spine).

Standalone module — pure stdlib + dataclasses. Records the three Black Box
streams (setpoint, actual, predicted) per cycle and computes gap_exec
(actual − setpoint) and gap_model (actual − predicted). Atomic writes via
tmp + rename; master.jsonl auto-rotates at the configured size.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BlackBoxRecord:
    cycle: int
    ts_start_iso: str
    ts_end_iso: str
    setpoint: dict[str, Any] | None = None
    actual: dict[str, Any] | None = None
    predicted: dict[str, Any] | None = None
    gap_exec: float | None = None
    gap_model: float | None = None
    notes: list[str] = field(default_factory=list)


def compute_gaps(rec: BlackBoxRecord) -> BlackBoxRecord:
    try:
        if rec.actual and rec.setpoint:
            a = rec.actual.get("fail_rate")
            s = rec.setpoint.get("fail_rate_target")
            if a is not None and s is not None:
                rec.gap_exec = float(a) - float(s)
    except Exception as exc:
        rec.notes.append(f"gap_exec error: {exc}")
    try:
        if rec.actual and rec.predicted:
            a = rec.actual.get("fail_rate")
            p = rec.predicted.get("fail_rate_hat")
            if a is not None and p is not None:
                rec.gap_model = float(a) - float(p)
    except Exception as exc:
        rec.notes.append(f"gap_model error: {exc}")
    return rec


def write_record(cycle_dir: Path, rec: BlackBoxRecord) -> Path:
    cycle_dir.mkdir(parents=True, exist_ok=True)
    out = cycle_dir / f"cycle_{rec.cycle:03d}.bbx.jsonl"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(rec), ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(out)
    return out


def append_to_master(master_path: Path, rec: BlackBoxRecord, rotate_mb: int = 10) -> None:
    master_path.parent.mkdir(parents=True, exist_ok=True)
    if master_path.is_file() and master_path.stat().st_size > rotate_mb * 1024 * 1024:
        i = 1
        while (master_path.parent / f"master.{i:03d}.jsonl").exists():
            i += 1
        master_path.rename(master_path.parent / f"master.{i:03d}.jsonl")
    line = json.dumps(asdict(rec), ensure_ascii=False) + "\n"
    tmp = master_path.with_suffix(".jsonl.master_append.tmp")
    prev = master_path.read_text(encoding="utf-8") if master_path.is_file() else ""
    tmp.write_text(prev + line, encoding="utf-8")
    tmp.replace(master_path)
