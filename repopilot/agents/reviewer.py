"""Reviewer: independent read of the diff and the test evidence. Returns typed
findings."""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware

from repopilot.agents.common import load_prompt
from repopilot.schemas import Review


def build_reviewer(model):
    return create_agent(
        model=model,
        tools=[],
        system_prompt=load_prompt("reviewer"),
        response_format=Review,
        middleware=[ModelRetryMiddleware()],
    )
