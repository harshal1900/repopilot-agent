"""Pre-work smoke checks. Run once, from the project root, with the virtual environment active.

    python -m pytest tests/test_prework.py -v

These tests check names and versions only. They never print a secret value.
"""

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENV = ["MODEL_PROVIDER", "MODEL_NAME", "LANGSMITH_TRACING", "LANGSMITH_PROJECT", "LANGSMITH_API_KEY"]


def read_env_names(path: Path) -> set[str]:
    names = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            names.add(line.split("=", 1)[0].strip())
    return names


def test_python_is_3_11_or_newer():
    assert sys.version_info >= (3, 11), f"Found Python {sys.version.split()[0]}; install 3.11+ (3.12 recommended)"


@pytest.mark.parametrize("module", ["langchain", "langgraph", "langsmith", "pydantic", "dotenv", "pytest", "ruff", "mypy"])
def test_requirement_imports(module):
    importlib.import_module(module)


def test_env_file_has_every_required_name():
    env_file = ROOT / ".env"
    assert env_file.exists(), "Copy .env.example to .env first"
    missing = REQUIRED_ENV and sorted(set(REQUIRED_ENV) - read_env_names(env_file))
    assert not missing, f"Missing names in .env: {missing}"


def test_env_file_is_git_ignored():
    gitignore = (ROOT / ".gitignore").read_text()
    assert ".env" in gitignore.splitlines(), ".env must be listed in .gitignore"


def test_git_is_installed():
    assert shutil.which("git"), "Install Git and reopen the terminal"
    subprocess.run(["git", "--version"], check=True, capture_output=True)


def test_docker_daemon_is_running():
    if not shutil.which("docker"):
        pytest.skip("Docker not installed yet; needed before Day 2 Lab 14")
    result = subprocess.run(["docker", "info"], capture_output=True, text=True)
    assert result.returncode == 0 and "Server Version" in result.stdout, "Start Docker Desktop, then run: docker info"


def test_model_key_is_not_placeholder_when_live_run_needed():
    values = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip()
    if os.environ.get("RUN_LIVE_CHECK") != "1":
        pytest.skip("Set RUN_LIVE_CHECK=1 to check that your model key is filled in")
    assert values.get("GOOGLE_API_KEY", "replace_me") != "replace_me", "Put your Gemini key in .env"
