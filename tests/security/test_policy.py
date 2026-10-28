import os
from pathlib import Path
import pytest
from repopilot.gates.policy import is_command_allowed, is_protected, resolve_inside_repo


def test_parent_traversal_is_refused(tmp_path: Path):
    with pytest.raises(PermissionError):
        resolve_inside_repo(tmp_path, "../../etc/passwd")


def test_absolute_path_is_refused(tmp_path: Path):
    with pytest.raises(PermissionError):
        resolve_inside_repo(tmp_path, "/etc/hosts")


def test_symlink_pointing_outside_is_refused(tmp_path: Path):
    repo = tmp_path / "repo"
    outside = tmp_path / "outside.txt"
    repo.mkdir()
    outside.write_text("secret")
    link = repo / "link.txt"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("symlinks need extra rights on this system; recorded as skipped")
    with pytest.raises(PermissionError):
        resolve_inside_repo(repo, "link.txt")


def test_env_file_is_protected():
    assert is_protected(".env")


def test_workflow_file_is_protected():
    assert is_protected(".github/workflows/ci.yml")


def test_rm_rf_is_not_allowed():
    assert not is_command_allowed("rm -rf /")


def test_pytest_is_allowed():
    assert is_command_allowed("python -m pytest tests/unit -q")


def test_chained_shell_command_is_refused():
    assert not is_command_allowed("pytest && rm -rf ~")


def test_test_files_are_protected():
    # The agent may fix code, never the tests that define the expected behaviour.
    assert is_protected("tests/test_service.py")
