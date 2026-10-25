import pytest
from pydantic import ValidationError
from repopilot.schemas import Analysis, Finding, Report, TestResult


def test_analysis_rejects_empty_acceptance_criteria():
    with pytest.raises(ValidationError):
        Analysis(reproduced=True, expected_behavior="x", acceptance_criteria=[])


def test_test_result_cannot_pass_with_nonzero_exit():
    with pytest.raises(ValidationError):
        TestResult(command="pytest", exit_code=1, duration_s=0.1, passed=True)


def test_finding_rejects_unknown_severity():
    with pytest.raises(ValidationError):
        Finding(severity="urgent", message="bad")


def test_report_round_trips_through_json():
    report = Report(task_id="t1", repo_path="/x", status="COMPLETED")
    again = Report.model_validate_json(report.model_dump_json())
    assert again == report
