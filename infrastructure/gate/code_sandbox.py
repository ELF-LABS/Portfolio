"""Deterministic code-task sandbox: AST + subprocess (no network). Linux rlimit AS best-effort.

Excerpted from the production self_improve module for portfolio review.
Imports `_extract_code_block` and `_sanitize_python_source` from a sibling
`validate_together` module not included in this excerpt — read for
architecture and approach, not for standalone execution.
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import tempfile
import textwrap
from typing import Any

from validate_together import _extract_code_block, _sanitize_python_source


def _child_rlimit() -> None:
    try:
        import resource

        cap = int(os.environ.get("SANDBOX_MEMORY_BYTES", str(512 * 1024 * 1024)))
        resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    except Exception:
        pass


def sandbox_validate_code(completion: str, timeout_s: float = 15.0) -> dict[str, Any]:
    """
    Stages: extract Python, AST parse, ensure callable defs, subprocess import check.
    Returns dict with parses, runs_clean, reason, reachable=True.
    """
    out: dict[str, Any] = {
        "parses": False,
        "imports_ok": True,
        "callable_found": False,
        "runs_clean": False,
        "reason": "",
        "reachable": True,
    }
    if not completion or len(completion.strip()) < 10:
        out["reason"] = "empty_completion"
        return out

    code_text = _sanitize_python_source(_extract_code_block(completion))
    try:
        tree = ast.parse(code_text)
    except SyntaxError as e:
        out["reason"] = f"syntax_error:{e}"
        return out
    out["parses"] = True

    callables = [
        n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    if not callables:
        out["reason"] = "no_top_level_callable"
        return out
    out["callable_found"] = True

    # Disallow obvious network imports in source text (lightweight static check)
    banned = re.compile(r"\b(import|from)\s+(socket|urllib|requests|httpx|aiohttp)\b", re.I)
    if banned.search(code_text):
        out["imports_ok"] = False
        out["reason"] = "network_import_blocked"
        return out

    # Run in isolated subprocess: compile + execute in empty __main__
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code_text)
        tmp_path = tmp.name
    try:
        env = {
            **os.environ,
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        # -B no bytecode; -S skip site (may break some snippets — allow without -S if fails)
        cmd = [os.environ.get("SANDBOX_PYTHON", "python3"), "-B", "-c", f"import runpy; runpy.run_path({tmp_path!r}, run_name='__sandbox__')"]
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            preexec_fn=_child_rlimit if os.name != "nt" else None,
        )
        if r.returncode != 0:
            tail = (r.stderr or r.stdout or "")[-500:]
            out["reason"] = f"exec_fail:rc={r.returncode}:{tail!r}"
            return out
        out["runs_clean"] = True
        out["reason"] = "ok"
        return out
    except subprocess.TimeoutExpired:
        out["reason"] = f"timeout>{timeout_s}s"
        return out
    except Exception as exc:
        out["reason"] = f"sandbox_error:{type(exc).__name__}:{exc}"
        return out
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def sandbox_validate_code_tests(
    completion: str,
    task_hint: str,
    template: str | None = None,
    *,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """
    A3-lite: template-tagged micro-tests (soft signal — failures reduce composite elsewhere).
    template: optional override; else inferred from instruction/completion heuristics.
    """
    out: dict[str, Any] = {
        "template_matched": "none",
        "tests_ran": 0,
        "tests_passed": 0,
        "test_output": "",
    }
    code_text = _sanitize_python_source(_extract_code_block(completion))
    try:
        tree = ast.parse(code_text)
    except SyntaxError as e:
        out["test_output"] = f"syntax:{e}"
        return out
    funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not funcs:
        out["test_output"] = "no_function"
        return out
    fn = funcs[0]
    hint = (task_hint or "").lower()
    cl = completion.lower()
    if template:
        tmpl: str = template
    elif any(x in hint for x in ("regex", "parse", "extract", "log file", "read file", "pattern")) or any(
        x in cl for x in ("re.search", "re.findall", "re.match")
    ):
        tmpl = "parse_file"
    elif any(x in hint for x in ("threshold", ">=", "exceed", "greater than", "cutoff", "limit")):
        tmpl = "threshold_check"
    elif any(x in hint for x in ("aggregate", "sum", "mean", "average", "total", "metric")):
        tmpl = "aggregate_metric"
    else:
        tmpl = "generic"
    out["template_matched"] = tmpl

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code_text)
        tmp_path = tmp.name

    def _subrun(py: str) -> tuple[int, str]:
        cmd = [os.environ.get("SANDBOX_PYTHON", "python3"), "-B", "-c", py]
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env={**os.environ, "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"},
            preexec_fn=_child_rlimit if os.name != "nt" else None,
        )
        tail = (r.stderr or r.stdout or "")[-800:]
        return r.returncode, tail

    logs: list[str] = []
    try:
        if tmpl == "parse_file":
            out["tests_ran"] = 2
            fixture = "widget_id: 4242\nother: x\n"
            py1 = f"""
import runpy
m = runpy.run_path({tmp_path!r}, run_name='__ct__')
f = m[{fn!r}]
g = f({fixture!r})
assert '4242' in str(g), (g,)
"""
            rc, tail = _subrun(py1)
            logs.append(f"t1 rc={rc} {tail}")
            if rc == 0:
                out["tests_passed"] += 1
            py2 = f"""
import runpy
m = runpy.run_path({tmp_path!r}, run_name='__ct__')
f = m[{fn!r}]
_ = f({fixture!r})
"""
            rc2, tail2 = _subrun(py2)
            logs.append(f"t2 rc={rc2} {tail2}")
            if rc2 == 0:
                out["tests_passed"] += 1
        elif tmpl == "threshold_check":
            out["tests_ran"] = 2
            py1 = f"""
import runpy
m = runpy.run_path({tmp_path!r}, run_name='__ct__')
f = m[{fn!r}]
assert bool(f(100)) in (True, False)
"""
            rc, tail = _subrun(py1)
            logs.append(f"t1 rc={rc} {tail}")
            if rc == 0:
                out["tests_passed"] += 1
            py2 = f"""
import runpy
m = runpy.run_path({tmp_path!r}, run_name='__ct__')
f = m[{fn!r}]
_ = f(0)
"""
            rc2, tail2 = _subrun(py2)
            logs.append(f"t2 rc={rc2} {tail2}")
            if rc2 == 0:
                out["tests_passed"] += 1
        elif tmpl == "aggregate_metric":
            out["tests_ran"] = 1
            py1 = f"""
import runpy
m = runpy.run_path({tmp_path!r}, run_name='__ct__')
f = m[{fn!r}]
assert f([1, 2, 3]) == 6, f([1, 2, 3])
"""
            rc, tail = _subrun(py1)
            logs.append(f"t1 rc={rc} {tail}")
            if rc == 0:
                out["tests_passed"] = 1
        else:
            out["tests_ran"] = 1
            py1 = f"""
import runpy
m = runpy.run_path({tmp_path!r}, run_name='__ct__')
f = m[{fn!r}]
try:
    f(1)
except TypeError:
    f([1])
"""
            rc, tail = _subrun(py1)
            logs.append(f"t1 rc={rc} {tail}")
            if rc == 0:
                out["tests_passed"] = 1
    except subprocess.TimeoutExpired:
        logs.append("timeout")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    out["test_output"] = "\n".join(logs)[:4000]
    return out
