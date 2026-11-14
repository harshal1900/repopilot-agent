from repopilot.evaluation import summarise
from repopilot.schemas import Patch, Plan, TestResult


def test_summary_reports_protected_change_and_tests():
    plan = Plan(
        files_to_change=["x.py"],
        change_summary="s",
        regression_test="t",
        test_commands=["python -m pytest -q"],
    )
    ok = TestResult(command="c", exit_code=0, duration_s=0.1, passed=True)
    state = {
        "status": "COMPLETED",
        "plan": plan,
        "test_results": [ok],
        "patch": Patch(changed_files=[".env"]),
    }
    summary = summarise(state)
    assert summary["tests_passed"] is True
    assert summary["protected_changed"] is True
    assert summary["files_changed"] == [".env"]


def test_no_plan_means_tests_not_passed():
    summary = summarise({"status": "BLOCKED", "plan": None, "test_results": [], "patch": None})
    assert summary["tests_passed"] is False
    assert summary["files_changed"] == []
