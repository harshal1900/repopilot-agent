"""The supervisor graph. Routing functions only read state and return a node name."""

from collections.abc import Callable
from typing import Any

# StateGraph is the LangGraph builder. You add nodes, connect them with edges, then compile() a runnable graph.
from langgraph.graph import END, START, StateGraph

from repopilot.nodes import (
    route_after_approval,
    route_after_baseline,
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
    # add_edge(A, B): after A finishes, B always runs next. This is a fixed step with no decision.
    builder.add_edge(START, "validate")
    # add_conditional_edges(A, router): after A finishes, the router function reads the state and returns the name of the next node.
    # The router decides; it does not change the state.
    builder.add_conditional_edges("validate", route_after_validate)
    # Fixed edges have no decisions. Explorer always hands over to Analyst, which always hands over to Planner.
    builder.add_edge("explorer", "analyst")
    builder.add_edge("analyst", "planner")
    builder.add_conditional_edges("planner", route_after_planner)
    builder.add_conditional_edges("baseline", route_after_baseline)
    builder.add_conditional_edges("approval", route_after_approval)
    builder.add_conditional_edges("implementer", route_after_implementer)
    builder.add_conditional_edges("test_node", route_after_test)
    builder.add_conditional_edges("reviewer", route_after_review)
    builder.add_edge("reporter", END)
    # The checkpointer saves the state after each step. A paused run, waiting for approval, can resume from that saved state.
    return builder.compile(checkpointer=checkpointer)
