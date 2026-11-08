"""Analyst: returns a typed Analysis. Tools: none. It reads the failure text it is given."""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware
from langchain.agents.structured_output import ToolStrategy

from repopilot.agents.common import load_prompt
from repopilot.schemas import Analysis


def build_analyst(model):
    return create_agent(
        model=model,
        tools=[],
        system_prompt=load_prompt("analyst"),
        response_format=ToolStrategy(Analysis),
        middleware=[ModelRetryMiddleware(on_failure="error")],
    )
