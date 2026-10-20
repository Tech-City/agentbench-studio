from app.checks import lint_task, run_check, score


def test_checks_and_score():
    out = '{"city": "Lagos"}'
    rs = [run_check({"type": "json_valid"}, out),
          run_check({"type": "contains", "value": "lagos"}, out),
          run_check({"type": "json_schema", "value": {"type": "object", "required": ["pop"]}}, out),
          run_check({"type": "llm_judge", "value": "polite"}, out, lambda p: "PASS")]
    assert [r["passed"] for r in rs] == [True, True, False, True]
    assert score(rs) == 0.75


def test_bad_output_fails_instead_of_crashing():
    assert not run_check({"type": "json_valid"}, "not json")["passed"]


def test_lint_flags_weak_tasks():
    assert lint_task("Hi", [])["quality"] < 50
    good = lint_task("Summarise the report in exactly three bullet points about revenue.", [{"type": "contains", "value": "revenue"}])
    assert good["quality"] == 100
