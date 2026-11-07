"""Runs allowed test commands and records the real exit status. The model never decides pass/fail."""
import re
import shlex
import subprocess
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from repopilot.gates.policy import is_command_allowed
from repopilot.schemas import TestResult

_COUNT = re.compile(r"(\d+) (passed|failed)")


def parse_counts(output: str) -> tuple[int | None, int | None]:
    """Read pytest's summary line such as '2 failed, 5 passed'. Unknown counts stay None."""
    lines = [line for line in output.splitlines() if _COUNT.search(line)]
    if not lines:
        return None, None
    found = {kind: int(num) for num, kind in _COUNT.findall(lines[-1])}
    return found.get("passed"), found.get("failed")


def execute(
    argv: list[str],
    cwd: Path | None,
    command_text: str,
    timeout_s: int,
    logs_dir: Path,
    on_timeout: Callable[[], None] | None = None,
) -> TestResult:
    """Run argv, save the output to a log file, and return the recorded result."""
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{datetime.now():%Y%m%d-%H%M%S-%f}.log"
    start = time.monotonic()
    try:
        done = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout_s,
            check=False,
        )
        output, exit_code, timed_out = done.stdout + done.stderr, done.returncode, False
    except subprocess.TimeoutExpired as expired:
        if on_timeout is not None:
            on_timeout()
        raw = expired.stdout or b""
        partial = raw.decode(errors="replace") if isinstance(raw, bytes) else raw
        output, exit_code, timed_out = partial + "\n[timed out]", None, True

    duration = round(time.monotonic() - start, 3)
    log_path.write_text(output, encoding="utf-8")
    passed_count, failed_count = parse_counts(output)
    return TestResult(
        command=command_text,
        exit_code=exit_code,
        duration_s=duration,
        timed_out=timed_out,
        passed=(exit_code == 0 and not timed_out),
        passed_count=passed_count,
        failed_count=failed_count,
        log_path=str(log_path),
    )


def run_allowed(root: Path, command: str, timeout_s: int, logs_dir: Path) -> TestResult:
    """Run an allowed command directly on this computer. Use only for trusted fixtures."""
    if not is_command_allowed(command):
        raise PermissionError(f"command not in allowlist: {command}")
    return execute(shlex.split(command), Path(root), command, timeout_s, logs_dir)
