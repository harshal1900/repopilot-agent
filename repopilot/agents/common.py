"""Helpers shared by every agent: load a prompt file and run an agent on one message."""

from pathlib import Path
from typing import Any

# __file__ is the path of this file. Going up two folders reaches the project's prompts folder on any machine.
PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


# A prompt is a Markdown file. Keeping prompts in files lets you change them without touching Python code.
def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")
    # agent.invoke sends one message and waits for the full result. The result holds the messages and, when a schema is set, a typed structured_response.


def ask(agent: Any, message: str) -> dict[str, Any]:
    """Run an agent once. Returns the full result dict (structured_response when a
    schema is set)."""
    return agent.invoke({"messages": [{"role": "user", "content": message}]})
