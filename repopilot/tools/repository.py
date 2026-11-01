"""Read-only repository tools. They never leave the repository root."""

from pathlib import Path
from repopilot.gates.policy import resolve_inside_repo

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def _is_skipped(path: Path, root: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.relative_to(root).parts)


def list_files(root: Path, pattern: str = "*") -> list[str]:
    """Relative paths of files under root matching the glob pattern."""
    base = Path(root).resolve()
    return sorted(
        p.relative_to(base).as_posix()
        for p in base.rglob(pattern)
        if p.is_file() and not _is_skipped(p, base)
    )


def read_file(root: Path, rel_path: str, max_bytes: int = 20000) -> tuple[bool, str]:
    """Return (ok, text). On failure, ok is False and text explains why."""
    try:
        path = resolve_inside_repo(Path(root), rel_path)
    except PermissionError as error:
        return False, f"refused: {error}"
    if not path.is_file():
        return False, f"not found: {rel_path}"
    raw = path.read_bytes()
    if b"\x00" in raw[:1024]:
        return False, f"refused: {rel_path} looks binary"
    text = raw.decode("utf-8", errors="replace")
    if len(raw) > max_bytes:
        return True, text[:max_bytes] + f"\n[truncated at {max_bytes} bytes]"
    return True, text


def search_code(
    root: Path, query: str, max_hits: int = 50
) -> list[tuple[str, int, str]]:
    """Find lines containing `query`. Returns (relative file, line number, line text)."""
    base = Path(root).resolve()
    hits: list[tuple[str, int, str]] = []
    for rel in list_files(base):
        text = (base / rel).read_text(encoding="utf-8", errors="ignore")
    for number, line in enumerate(text.splitlines(), start=1):
        if query in line:
            hits.append((rel, number, line))
        if len(hits) >= max_hits:
            return hits
    return hits
