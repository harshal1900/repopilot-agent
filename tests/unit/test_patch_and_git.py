import subprocess
import pytest
from repopilot.tools.patch_tools import apply_patch, count_changed_lines, files_in_diff


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    (tmp_path / "app.py").write_text("def f():\n return 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "init",
        ],
        check=True,
    )
    return tmp_path


GOOD = (
    "--- a/app.py\n"
    "+++ b/app.py\n"
    "@@ -1,2 +1,2 @@\n"
    " def f():\n"
    "- return 1\n"
    "+ return 2\n"
)


def test_valid_one_line_change_applies(repo):
    ok, _ = apply_patch(repo, GOOD, max_lines=300)
    assert ok
    assert "return 2" in (repo / "app.py").read_text()


def test_protected_file_is_refused_and_unchanged(repo):
    env_patch = GOOD.replace("app.py", ".env")
    ok, message = apply_patch(repo, env_patch, max_lines=300)
    assert not ok and "protected" in message
    assert not (repo / ".env").exists()


def test_over_line_limit_is_refused(repo):
    ok, message = apply_patch(repo, GOOD, max_lines=1)
    assert not ok and "more than 1 lines" in message
    assert "return 1" in (repo / "app.py").read_text()


def test_malformed_diff_is_refused_and_unchanged(repo):
    ok, _ = apply_patch(
        repo, "--- a/app.py\n+++ b/app.py\n@@ garbage @@\n+x\n", max_lines=300
    )
    assert not ok
    assert "return 1" in (repo / "app.py").read_text()


def test_count_and_paths_helpers():
    assert count_changed_lines(GOOD) == 2
    assert files_in_diff(GOOD) == ["app.py"]
