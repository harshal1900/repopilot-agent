"""The supervisor graph. Routing functions only read state and return a node name."""

from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from repopilot.nodes import (
    route_after_analyst,
    route_after_approval,
    route_after_baseline,
    route_after_explorer,
    route_after_implementer,
    route_after_planner,
    route_after_review,
    route_after_test,
    route_after_validate,
)
from repopilot.state import RepoPilotState

NODE_NAMES = (
    "validate",
    "explorer",
    "analyst",
    "planner",
    "baseline",
    "approval",
    "implementer",
    "test_node",
    "reviewer",
    "reporter",
)


def build_graph(nodes: dict[str, Callable[..., Any]], checkpointer):
    builder = StateGraph(RepoPilotState)
    for name in NODE_NAMES:
        builder.add_node(name, nodes[name])
    builder.add_edge(START, "validate")
    builder.add_conditional_edges("validate", route_after_validate)
    builder.add_conditional_edges("explorer", route_after_explorer)
    builder.add_conditional_edges("analyst", route_after_analyst)
    builder.add_conditional_edges("planner", route_after_planner)
    builder.add_conditional_edges("baseline", route_after_baseline)
    builder.add_conditional_edges("approval", route_after_approval)
    builder.add_conditional_edges("implementer", route_after_implementer)
    builder.add_conditional_edges("test_node", route_after_test)
    builder.add_conditional_edges("reviewer", route_after_review)
    builder.add_edge("reporter", END)
    return builder.compile(checkpointer=checkpointer)
