"""Settings loaded from environment variables (and a local .env)"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Files matching these patterns can never be changed by the agent. The rule lives in code, not in a prompt.
PROTECTED_PATTERNS = (
    ".env",
    ".env.*",
    ".github/*",
    ".locl",
    "pyproject.toml",
    "tests/*",
)


@dataclass(frozen=True)
# A dataclass with frozen=True is an immutable settings object. The code can read the values but cannot change them during a run.
class Settings:
    """Settings loaded from environment variables (and a local .env)"""

    # model provider to use for the model calls
    model_provider: str
    # model name to use for the model calls
    model_name: str
    # path to the local repo root
    workspace_root: Path
    # max llm calls
    max_llm_calls: int
    # max repair attempts
    max_repair_attempts: int
    # command timeout in seconds
    command_timeout_s: int
    # max patch lines
    max_patch_lines: int
    # sandbox type
    sandbox: str = "docker"


def load_settings() -> Settings:
    # os.environ.get returns None when a variable is missing. The next lines turn that into a clear error instead of a failure later.
    model_name = os.environ.get("MODEL_NAME")
    if not model_name:
        raise RuntimeError("MODEL_NAME environment variable is not set")
    return Settings(
        model_provider=os.environ.get("MODEL_PROVIDER", "google"),
        model_name=model_name,
        workspace_root=Path(os.environ.get("WORKSPACE_ROOT", "./workspace")),
        max_llm_calls=int(os.environ.get("MAX_LLM_CALLS", "40")),
        max_repair_attempts=int(os.environ.get("MAX_REPAIR_ATTEMPTS", "2")),
        command_timeout_s=int(os.environ.get("COMMAND_TIMEOUT_S", "300")),
        max_patch_lines=int(os.environ.get("MAX_PATCH_LINES", "300")),
        sandbox=os.environ.get("SANDBOX", "docker"),
    )
