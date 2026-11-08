"""Planner: turns an Analysis into a typed Plan."""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware
from langchain.agents.structured_output import ToolStrategy

from repopilot.agents.common import load_prompt
from repopilot.schemas import Plan


def build_planner(model):
    return create_agent(
        model=model,
        tools=[],
        system_prompt=load_prompt("planner"),
        response_format=ToolStrategy(Plan),
        middleware=[ModelRetryMiddleware(on_failure="error")],
    )
