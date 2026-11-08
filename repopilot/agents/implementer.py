"""Implementer: proposes a diff as data. It never writes files; the node applies the diff through the gate."""

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ModelRetryMiddleware
from langchain.agents.structured_output import ToolStrategy

from repopilot.agents.common import load_prompt
from repopilot.agents.explorer import make_explorer_tools
from repopilot.schemas import Patch


def build_implementer(model, repo_root, max_llm_calls: int):
    read_only = [
        tool
        for tool in make_explorer_tools(repo_root)
        if tool.name in {"read_file_tool", "search_code_tool", "load_skill_tool"}
    ]
    middleware: list[Any] = [
        ModelRetryMiddleware(on_failure="error"),
        ModelCallLimitMiddleware(run_limit=max_llm_calls, exit_behavior="error"),
    ]
    return create_agent(
        model=model,
        tools=read_only,
        system_prompt=load_prompt("implementer"),
        response_format=ToolStrategy(Patch),
        middleware=middleware,
    )
