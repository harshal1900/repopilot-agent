from pathlib import Path
from repopilot.sandbox.docker_runner import build_docker_command


def test_container_has_no_network_and_no_key(tmp_path: Path):
    cmd = build_docker_command(tmp_path, ["pytest"])
    assert "--network" in cmd and cmd[cmd.index("--network") + 1] == "none"
    assert not any("GOOGLE_API_KEY" in part for part in cmd)
    assert not any("docker.sock" in part for part in cmd)


def test_container_runs_as_non_root(tmp_path: Path):
    cmd = build_docker_command(tmp_path, ["pytest"])
    assert cmd[cmd.index("--user") + 1] == "1000:1000"


def test_only_the_task_folder_is_mounted(tmp_path: Path):
    cmd = build_docker_command(tmp_path, ["pytest"])
    mounts = [cmd[i + 1] for i, part in enumerate(cmd) if part == "-v"]
    assert mounts == [f"{tmp_path.resolve()}:/work"]
