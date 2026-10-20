"""Deterministic + judged checks, and an author-side task linter."""
import json
import re
from typing import Callable
from jsonschema import Draft202012Validator

TYPES = ["contains", "not_contains", "regex", "json_valid", "json_schema", "max_words", "llm_judge"]
DETERMINISTIC = set(TYPES) - {"llm_judge"}


def run_check(spec: dict, output: str, judge: Callable[[str], str] | None = None) -> dict:
    t, v = spec["type"], spec.get("value")
    try:
        if t == "contains":
            ok, detail = str(v).lower() in output.lower(), f"contains '{v}'"
        elif t == "not_contains":
            ok, detail = str(v).lower() not in output.lower(), f"does not contain '{v}'"
        elif t == "regex":
            ok, detail = re.search(str(v), output, re.S) is not None, f"matches /{v}/"
        elif t == "json_valid":
            json.loads(output)
            ok, detail = True, "is valid JSON"
        elif t == "json_schema":
            schema = json.loads(v) if isinstance(v, str) else v
            errs = list(Draft202012Validator(schema).iter_errors(json.loads(output)))
            ok, detail = not errs, "matches schema" if not errs else errs[0].message
        elif t == "max_words":
            n = len(output.split())
            ok, detail = n <= int(v), f"{n} words (max {v})"
        elif t == "llm_judge":
            verdict = judge(f"Rubric: {v}\n\nResponse:\n{output}\n\nReply with exactly PASS or FAIL.") if judge else "FAIL"
            ok, detail = verdict.strip().upper().startswith("PASS"), f"judge: {verdict.strip()[:40]}"
        else:
            ok, detail = False, f"unknown check type '{t}'"
    except Exception as e:  # a broken output or spec is a failed check, not a crashed run
        ok, detail = False, f"{type(e).__name__}: {e}"
    return {"type": t, "label": spec.get("label") or t, "passed": ok, "detail": detail, "weight": spec.get("weight", 1)}


def score(results: list[dict]) -> float:
    total = sum(r["weight"] for r in results)
    return round(sum(r["weight"] for r in results if r["passed"]) / total, 4) if total else 0.0


def lint_task(prompt: str, checks: list[dict]) -> dict:
    """Task-quality checks: flags tasks that can't discriminate between good and bad answers."""
    issues = []
    add = lambda sev, msg: issues.append({"severity": sev, "message": msg})
    if len(prompt.split()) < 8:
        add("warn", "Prompt is very short; state the goal, constraints and output format.")
    if not checks:
        add("error", "No checks defined. A task without checks cannot be scored.")
    elif not any(c["type"] in DETERMINISTIC for c in checks):
        add("warn", "Only llm_judge checks. Add at least one deterministic check so scores are reproducible.")
    if checks and all(c["type"] in ("max_words",) for c in checks):
        add("warn", "Length limits alone pass almost any answer, including an empty one.")
    if checks and all(c["type"] == "not_contains" for c in checks):
        add("warn", "Negative checks alone pass an empty answer. Add a positive check.")
    seen = set()
    for c in checks:
        key = (c["type"], str(c.get("value")))
        if key in seen:
            add("info", f"Duplicate check: {c['type']} '{c.get('value')}'.")
        seen.add(key)
        if c["type"] == "regex":
            try:
                re.compile(str(c.get("value")))
            except re.error as e:
                add("error", f"Invalid regex '{c.get('value')}': {e}")
        if c["type"] == "json_schema":
            try:
                v = c.get("value")
                Draft202012Validator.check_schema(json.loads(v) if isinstance(v, str) else v)
            except Exception as e:
                add("error", f"Invalid JSON schema: {e}")
    quality = max(0, 100 - 40 * sum(i["severity"] == "error" for i in issues) - 15 * sum(i["severity"] == "warn" for i in issues) - 5 * sum(i["severity"] == "info" for i in issues))
    return {"quality": quality, "issues": issues}
