#!/usr/bin/env python3
"""
Reasoning-depth rubric (Fellows Tier 1). Schema v2026-04-17-a.
Four components 0-2; composite = sum (max 8).

Excerpted from the production self_improve module for portfolio review.
Imports `config` and (optionally) `ab_shadow_twin` from sibling modules
not included in this excerpt — read for architecture and approach, not
for standalone execution.
"""
from __future__ import annotations

SCHEMA_VERSION = "2026-04-17-a"

import argparse
import json
import re
from pathlib import Path
from typing import Any

import requests

import config

RUBRIC_PROMPT = f"""You are a strict grader for reasoning DEPTH in a single assistant completion (not fluency).
Schema: {SCHEMA_VERSION}
Score EACH dimension 0, 1, or 2 only:
- decomposition: breaks the problem into clear steps / sub-questions?
- causal_linkage: explains WHY steps follow (not just WHAT)?
- edge_cases: notes ambiguity, failure modes, or boundary conditions?
- actionability: concrete enough to execute without further clarification?

Return ONLY JSON:
{{"decomposition":0,"causal_linkage":0,"edge_cases":0,"actionability":0,"reason":"<one short sentence>"}}
"""


def _repair_numeric_key_glue(chunk: str) -> str:
    """Twin sometimes emits `\"actionability\":0\",\"reason\"` — repair to valid JSON."""
    return re.sub(r'(\d+)","([a-zA-Z_][a-zA-Z0-9_]*)"', r'\1,"\2"', chunk)


def _parse_grade(text: str) -> dict[str, Any] | None:
    t = (text or "").strip()
    if t.startswith("```"):
        lines = t.split("\n")
        t = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        i, j = t.find("{"), t.rfind("}")
        if i < 0 or j <= i:
            return None
        chunk = t[i : j + 1]
        try:
            o = json.loads(chunk)
        except json.JSONDecodeError:
            o = json.loads(_repair_numeric_key_glue(chunk))
    except json.JSONDecodeError:
        return None
    if not isinstance(o, dict):
        return None
    out: dict[str, Any] = {}
    for k in ("decomposition", "causal_linkage", "edge_cases", "actionability"):
        try:
            v = int(o.get(k, 0))
        except (TypeError, ValueError):
            v = 0
        out[k] = max(0, min(2, v))
    out["reason"] = str(o.get("reason", ""))[:300]
    out["schema_version"] = SCHEMA_VERSION
    return out


def grade_pair(
    instruction: str,
    completion: str,
    grader_model: str,
    *,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    """grader_model: 'pattern' (twin LoRA) or 'qwen3.5-35b-a3b' (35B)."""
    url = config.get_twin_url() if grader_model == "pattern" else config.THINKER
    user = (
        f"INSTRUCTION:\n{instruction[:4000]}\n\nCOMPLETION:\n{completion[:6000]}\n/no_think"
        if grader_model != "pattern"
        else f"INSTRUCTION:\n{instruction[:4000]}\n\nCOMPLETION:\n{completion[:6000]}"
    )
    # Twin: enable_thinking false via chat_template_kwargs. 35B: /no_think in user only — mutually exclusive per Qwen stack quirks.
    payload: dict[str, Any] = {
        "model": grader_model,
        "messages": [
            {"role": "system", "content": RUBRIC_PROMPT},
            {"role": "user", "content": user},
        ],
        "max_tokens": 220,
        "temperature": 0.1,
    }
    if grader_model == "pattern":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    try:
        r = requests.post(url, json=payload, timeout=timeout_s)
        r.raise_for_status()
        pt = r.text
        if grader_model == "pattern":
            try:
                import ab_shadow_twin

                ab_shadow_twin.schedule_shadow_post(
                    url=url,
                    request_json=payload,
                    decision_point="reasoning_depth_grader_pattern",
                    pattern_response_text=pt,
                    timeout=float(timeout_s),
                )
            except Exception:
                pass
        raw = json.loads(pt)["choices"][0]["message"].get("content") or ""
        parsed = _parse_grade(raw)
        if not parsed:
            return {
                "error": "parse_fail",
                "raw": raw[:500],
                "grader_model": grader_model,
                "schema_version": SCHEMA_VERSION,
            }
        parsed["composite"] = sum(int(parsed[k]) for k in ("decomposition", "causal_linkage", "edge_cases", "actionability"))
        parsed["grader_model"] = grader_model
        return parsed
    except Exception as exc:
        return {
            "error": str(exc),
            "grader_model": grader_model,
            "schema_version": SCHEMA_VERSION,
        }


def inter_grader_agreement(g1: dict[str, Any], g2: dict[str, Any]) -> dict[str, Any]:
    """Mean absolute diff per component; agreement if mean < 0.5."""
    keys = ("decomposition", "causal_linkage", "edge_cases", "actionability")
    diffs = []
    for k in keys:
        if k not in g1 or k not in g2 or "error" in g1 or "error" in g2:
            continue
        try:
            diffs.append(abs(int(g1[k]) - int(g2[k])))
        except (TypeError, ValueError):
            continue
    mean_diff = sum(diffs) / len(diffs) if diffs else 999.0
    return {
        "mean_abs_diff": mean_diff,
        "agreement": bool(mean_diff < 0.5),
        "per_component": {k: abs(int(g1.get(k, 0)) - int(g2.get(k, 0))) for k in keys if k in g1 and k in g2},
    }


def grade_two_graders(instruction: str, completion: str) -> dict[str, Any]:
    g1 = grade_pair(instruction, completion, "pattern")
    g2 = grade_pair(instruction, completion, config.THINKER_MODEL)
    return {"pattern": g1, "thinker": g2, "agreement": inter_grader_agreement(g1, g2)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.input.open(encoding="utf-8") as inf, args.output.open("w", encoding="utf-8") as outf:
        for line in inf:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            inst = str(rec.get("instruction", ""))
            comp = str(rec.get("completion", ""))
            both = grade_two_graders(inst, comp)
            rec["reasoning_depth_grades"] = both
            outf.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
