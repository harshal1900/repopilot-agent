"""Run untrusted repository commands in a disposable Docker container."""

import shlex
import subprocess
import uuid
from pathlib import Path

from repopilot.gates.policy import is_command_allowed
from repopilot.schemas import TestResult
from repopilot.tools.test_runner import execute

SANDBOX_IMAGE = "repopilot-sandbox:latest"


def build_docker_command(
    workdir: Path,
    command: list[str],
    image: str = SANDBOX_IMAGE,
    name: str | None = None,
) -> list[str]:
    """The exact `docker run` argument list. Kept separate so tests can inspect it."""
    args = ["docker", "run", "--rm"]
    if name:
        args += ["--name", name]
    return [
        *args,
        "--network",
        "none",  # no internet inside the container
        "--memory",
        "1g",
        "--cpus",
        "1",
        "--pids-limit",
        "256",
        "--user",
        "1000:1000",  # not root
        "-v",
        f"{Path(workdir).resolve()}:/work",
        "-w",
        "/work",  # only the task folder is mounted
        image,
        *command,
    ]


def run_in_sandbox(
    root: Path, command: str, timeout_s: int, logs_dir: Path, image: str = SANDBOX_IMAGE
) -> TestResult:
    """Run an allowed test command inside the sandbox container and record the result."""
    if not is_command_allowed(command):
        raise PermissionError(f"command not in allowlist: {command}")
    name = f"repopilot-{uuid.uuid4().hex[:12]}"
    argv = build_docker_command(Path(root), shlex.split(command), image, name)

    def kill_container() -> None:
        # Stopping the docker client does not stop the container, so kill it by name.
        subprocess.run(["docker", "kill", name], capture_output=True, check=False)

    return execute(argv, None, command, timeout_s, logs_dir, on_timeout=kill_container)
