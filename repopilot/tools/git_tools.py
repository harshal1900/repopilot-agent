"""Git helpers. Arguments are always passed as a list; no shell strings."""

import subprocess
from pathlib import Path


def run_git(root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def git_status(root: Path) -> str:
    return run_git(Path(root), ["status", "--short"])


def git_diff(root: Path) -> str:
    return run_git(Path(root), ["diff"])


def make_worktree(repo: Path, commit: str, dest: Path) -> None:
    """Create a disposable checkout at `commit`. The agent works only in `dest`."""
    run_git(Path(repo), ["worktree", "add", "--detach", str(dest), commit])
