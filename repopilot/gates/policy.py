"""Rules enforced by code. Prompts are suggestions; these functions decide."""

import shlex
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from repopilot.config import PROTECTED_PATTERNS

# Only these command prefixes may run. Nothing else is ever executed.
# Allowlist: only commands listed here may run. Anything not listed is refused, even if a model asks for it.
ALLOWED_COMMANDS = ("pytest", "python -m pytest", "ruff check")
# Shell operators are refused even inside an allowed command.
# Denylist inside an allowed command: shell operators such as && or ; could chain a second command, so they are refused.
FORBIDDEN_TOKENS = {"&&", "||", ";", "|", "&", ">", ">>", "<", "`"}


def resolve_inside_repo(repo_root: Path, requested: str) -> Path:
    """Return the real path of `requested` inside `repo_root`, or raise PermissionError."""
    # resolve() turns a relative path into an absolute path and follows symlinks. The checks after this line see the real location.
    root = Path(repo_root).resolve()
    candidate = (root / requested).resolve()  # resolve() follows '..' and symlinks
    # Path guard: the resolved path must be the repository itself or sit inside it. '../' and symlinks cannot escape.
    if candidate != root and root not in candidate.parents:
        raise PermissionError(f"path escapes the repository: {requested}")
    return candidate


def is_protected(path: str) -> bool:
    """True for files the agent must never change without human approval."""
    # PurePosixPath works on path text without touching the disk. Windows backslashes become forward slashes first.
    normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
    name = PurePosixPath(normalized).name
    return any(
        fnmatch(normalized, pattern) or fnmatch(name, pattern)
        for pattern in PROTECTED_PATTERNS
    )


def is_command_allowed(command: str) -> bool:
    """True only if the command starts with an allowed prefix and has no shell operators."""
    try:
        # shlex.split splits a command string the way a shell would, but never runs it. Quotes are handled correctly.
        tokens = shlex.split(command)
    except ValueError:
        return False
    if not tokens or any(token in FORBIDDEN_TOKENS for token in tokens):
        return False
    return any(
        tokens[: len(shlex.split(prefix))] == shlex.split(prefix)
        for prefix in ALLOWED_COMMANDS
    )
