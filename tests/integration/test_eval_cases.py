import subprocess
from pathlib import Path

from scripts.eval_cases import CASES, build_case_repo


def test_each_case_builds_a_git_repo(tmp_path: Path):
    for name in CASES:
        repo = build_case_repo(name, tmp_path / name)
        assert (repo / ".git").exists(), name
        assert (repo / "legacy_app" / "service.py").exists(), name


def test_already_passing_case_really_passes(tmp_path: Path):
    repo = build_case_repo("already-passing", tmp_path / "already")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_models.py", "tests/test_service.py", "-q"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout


def test_dict_case_fails_before_the_agent_runs(tmp_path: Path):
    repo = build_case_repo("pydantic-dict-call", tmp_path / "dict")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_models.py", "-q"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
