"""Task-routed specialist + pattern-master ensemble (Fellows Tier 1).

Excerpted from the production self_improve module for portfolio review.
This file imports sibling modules (`config`, `validate_together`,
`twin_config_guard`) that are not included in this excerpt — read for
architecture and approach, not for standalone execution.
"""
from __future__ import annotations

import os
from typing import Any

import requests

import config


def task_to_specialist_lora(task: str) -> str:
    """Twin `model` field for specialist (not 35B)."""
    t = str(task or "default").lower().strip()
    # convo: writer default; override CONVO_SPECIALIST=sales if needed
    convo = os.environ.get("CONVO_SPECIALIST", "writer").lower()
    mapping = {
        "code": "code",
        "analytical": "analytical",
        "identity": "identity",
        "writer": "writer",
        "sales": "sales",
        "ops": "ops",
        "pattern": "pattern",
        "convo": convo,
        "docs": "writer",
        "meta": "pattern",
    }
    return mapping.get(t, "writer")


def specialist_review(
    instruction: str,
    completion: str,
    task: str,
    *,
    timeout_s: float = 60.0,
    specialist_lora: str | None = None,
    twin_url: str | None = None,
) -> dict[str, Any]:
    """Same JSON contract as pattern_master_review; different LoRA.

    On transport/parse failure: ``reachable=False`` and ``confidence=None`` so ingest
    can persist ``None`` in fitness slots (not a fake 0.5).
    """
    from twin_config_guard import check_twin_url_alignment

    if twin_url is None:
        raise ValueError(
            "twin_url is required, no implicit fallback to import-time twin URL snapshot (Round 5c CR2-A)"
        )
    check_twin_url_alignment(twin_url)

    model = specialist_lora or task_to_specialist_lora(task)
    chat_url = twin_url
    system_prompt = (
        "You are a domain specialist reviewing one training pair. Respond with ONLY JSON: "
        '{"verdict":"train|reject|flag","confidence":0-1,"reason":"short sentence"}. '
        "TRAIN: complete, on-task, usable. "
        "REJECT: broken, wrong domain, truncated, or nonsense. "
        "FLAG: borderline."
    )
    user_prompt = (
        f"Task type: {task}\nSpecialist adapter: {model}\n\n"
        f"INSTRUCTION:\n{instruction[:2000]}\n\n"
        f"COMPLETION:\n{completion[:4000]}"
    )
    try:
        from validate_together import _parse_pattern_verdict, _sleep

        _sleep()
        r = requests.post(
            chat_url,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 200,
                "temperature": 0.2,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=float(timeout_s),
        )
        r.raise_for_status()
        data = r.json()
        try:
            raw = data["choices"][0]["message"].get("content", "")
        except (KeyError, IndexError, TypeError) as exc:
            return {
                "verdict": "flag",
                "confidence": None,
                "reason": f"specialist_malformed_response:{type(exc).__name__}",
                "reachable": False,
                "lora": model,
            }
        parsed = _parse_pattern_verdict(raw)
        parsed["reachable"] = True
        parsed["lora"] = model
        return parsed
    except Exception as exc:
        return {
            "verdict": "flag",
            "confidence": None,
            "reason": f"specialist_unreachable:{type(exc).__name__}",
            "reachable": False,
            "lora": model,
        }


def combine_verdicts(
    spec: dict[str, Any],
    pat: dict[str, Any],
    floor: float,
    *,
    strict_reachability: bool,
) -> tuple[str, str]:
    """
    Returns (gate_final, reason) where gate_final in pass|fail.
    Rules: any reject -> fail; flag with conf < floor -> fail.
    If strict_reachability: any unreachable -> fail (physics-style circuit breaker).
    """
    sr = bool(spec.get("reachable", False))
    pr = bool(pat.get("reachable", False))
    sv = str(spec.get("verdict", "flag")).lower()
    pv = str(pat.get("verdict", "flag")).lower()

    def _eff_conf(d: dict[str, Any]) -> float:
        if not d.get("reachable", False):
            return 0.0
        c = d.get("confidence")
        if c is None:
            return 0.0
        try:
            return max(0.0, min(1.0, float(c)))
        except (TypeError, ValueError):
            return 0.0

    sc = _eff_conf(spec)
    pc = _eff_conf(pat)

    if strict_reachability and (not sr or not pr):
        return "fail", "unreachable_observer_strict"

    if sv == "reject" or pv == "reject":
        return "fail", "either_reject"

    if sv == "flag" and sc < floor:
        return "fail", "specialist_flag_low_conf"
    if pv == "flag" and pc < floor:
        return "fail", "pattern_flag_low_conf"

    # train + train, or train + flag with conf>=floor for flagged side
    if sv == "train" and pv == "train":
        return "pass", "both_train"
    if sv == "train" and pv == "flag" and pc >= floor:
        return "pass", "train_and_flag_ok"
    if sv == "flag" and sc >= floor and pv == "train":
        return "pass", "flag_ok_and_train"

    if sv == "train" and pv == "flag" and pc < floor:
        return "fail", "pattern_flag_low_conf"
    if sv == "flag" and sc < floor and pv == "train":
        return "fail", "specialist_flag_low_conf"

    return "fail", "no_pass_rule_matched"


def specialist_pattern_disagree(spec: dict[str, Any], pat: dict[str, Any]) -> bool:
    """True if verdict buckets differ (train vs reject/flag)."""
    if not spec.get("reachable") or not pat.get("reachable"):
        return False
    sv = str(spec.get("verdict", "")).lower()
    pv = str(pat.get("verdict", "")).lower()
    return sv != pv


def gate_new_pair(
    instruction: str,
    completion: str,
    task: str,
    *,
    mode: str = "generation",
    timeout_s: float = 60.0,
    specialist_lora: str | None = None,
    twin_url: str | None = None,
) -> tuple[bool, dict[str, Any], str]:
    """
    Thin wrapper around ``validate_pair(..., mode="ingest")`` so pilots use the same
    sandbox + multi-LoRA path as production (without the 35B / physics composite blend).

    **ingest** mode skips ``blend_verdict`` and related validators; **production**
    ``validate_pair`` runs the full stack then applies the same gate block when
    ``MULTI_LORA_GATE=1``.
    """
    from validate_together import validate_pair

    rec: dict[str, Any] = {
        "instruction": instruction,
        "completion": completion,
        "task": task,
    }
    verdict = validate_pair(
        rec,
        twin_url=twin_url,
        mode="ingest",
        filter_log_ctx=None,
        ingest_specialist_lora=specialist_lora,
        observer_timeout_s=timeout_s,
    )
    combine_reason = str(verdict.get("gate_reason", "") or "")[:300]
    gf = verdict.get("gate_final")
    gate_final = str(gf) if gf is not None else ("fail" if verdict.get("fail") else "pass")
    approved = (not verdict.get("fail", False)) and gate_final == "pass"

    out = {k: v for k, v in verdict.items() if k.startswith("gate_")}
    out["gate_mode"] = mode
    if not out.get("gate_source"):
        out["gate_source"] = "multi_lora_gate_new_pair"
    return approved, out, combine_reason or "ingest_gate"
