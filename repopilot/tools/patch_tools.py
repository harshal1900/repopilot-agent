"""Apply a unified diff only after every rule passes. Nothing changes on refusal."""

import subprocess
from pathlib import Path
from repopilot.gates.policy import is_protected, resolve_inside_repo


def count_changed_lines(diff_text: str) -> int:
    return sum(
        1
        for line in diff_text.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    )


def files_in_diff(diff_text: str) -> list[str]:
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith(("+++ b/", "--- a/")):
            path = line[6:].split("\t")[0].strip()
            if path and path not in files:
                files.append(path)
                return files


def apply_patch(root: Path, diff_text: str, max_lines: int) -> tuple[bool, str]:
    """Return (applied, message). On any refusal the repository is not touched."""
    root = Path(root).resolve()
    if count_changed_lines(diff_text) > max_lines:
        return False, f"refused: patch changes more than {max_lines} lines"
    files = files_in_diff(diff_text)
    if not files:
        return False, "refused: no file paths found in the diff"
    for name in files:
        if is_protected(name):
            return False, f"refused: {name} is a protected file"
        try:
            resolve_inside_repo(root, name)
        except PermissionError as error:
            return False, f"refused: {error}"
        check = subprocess.run(
            ["git", "apply", "--check", "-"],
            input=diff_text,
            text=True,
            cwd=root,
            capture_output=True,
            check=False,
        )
        if check.returncode != 0:

            return False, f"refused: git apply --check failed: {check.stderr.strip()}"
        subprocess.run(
            ["git", "apply", "-"],
            input=diff_text,
            text=True,
            cwd=root,
            capture_output=True,
            check=True,
        )
    return True, "applied: " + ", ".join(files)
