import pytest

from repopilot.tools.test_runner import parse_counts, run_allowed


def test_passing_command_is_passed(tmp_path):
    result = run_allowed(tmp_path, "python -m pytest --version", 60, tmp_path / "logs")
    assert result.exit_code == 0 and result.passed


def test_disallowed_command_is_refused_before_running(tmp_path):
    with pytest.raises(PermissionError):
        run_allowed(tmp_path, "rm -rf /", 60, tmp_path / "logs")


def test_timeout_is_recorded(tmp_path):
    result = run_allowed(
        tmp_path, "python -m pytest --co -q -p no:cacheprovider", 0, tmp_path / "logs"
    )
    assert result.timed_out and not result.passed


def test_parse_counts_reads_pytest_summary():
    assert parse_counts("...\n2 failed, 5 passed in 0.1s") == (5, 2)
    assert parse_counts("no summary here") == (None, None)
