"""Explorer: read-only tools only. It cannot write, apply or run anything."""

from pathlib import Path
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware
from langchain_core.tools import tool
from repopilot.agents.common import load_prompt
from repopilot.tools.repository import list_files, read_file, search_code
from repopilot.tools.skills import list_skills, load_skill


def make_explorer_tools(repo_root: Path) -> list:
    root = Path(repo_root).resolve()


@tool
def list_files_tool(pattern: str = "*") -> list[str]:
    """List repository files matching a glob pattern."""
    return list_files(root, pattern)


@tool
def read_file_tool(rel_path: str) -> str:
    """Read one repository file by relative path."""
    return read_file(root, rel_path)[1]


@tool
def search_code_tool(query: str) -> list:
    """Find lines containing the query text."""
    return search_code(root, query)


@tool
def list_skills_tool() -> list:
    """List available skills with their descriptions."""
    return list_skills()


@tool
def load_skill_tool(name: str) -> str:
    """Load the full text of one skill by name."""
    try:
        return load_skill(name)
    except (PermissionError, FileNotFoundError) as error:
        return f"error: {error}"
    return [
        list_files_tool,
        read_file_tool,
        search_code_tool,
        list_skills_tool,
        load_skill_tool,
    ]


def build_explorer(model, repo_root: Path):
    return create_agent(
        model=model,
        tools=make_explorer_tools(repo_root),
        system_prompt=load_prompt("explorer"),
        middleware=[ModelRetryMiddleware()],
    )
