"""Builds the real graph from settings. Used by scripts/run_task.py."""

import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from repopilot.agents.analyst import build_analyst
from repopilot.agents.explorer import build_explorer
from repopilot.agents.implementer import build_implementer
from repopilot.agents.planner import build_planner
from repopilot.agents.reviewer import build_reviewer
from repopilot.config import Settings
from repopilot.graph import build_graph
from repopilot.models import get_model
from repopilot.nodes import (
    approval_node,
    make_analyst_node,
    make_baseline_node,
    make_explorer_node,
    make_implementer_node,
    make_planner_node,
    make_reporter_node,
    make_reviewer_node,
    make_test_node,
    validate_node,
)
from repopilot.sandbox.docker_runner import run_in_sandbox
from repopilot.tools.test_runner import run_allowed


def build_app(
    settings: Settings,
    repo_root: Path,
    reports_dir: Path,
    logs_dir: Path,
    checkpoint_db: Path,
):
    model = get_model(settings)
    if settings.sandbox not in ("docker", "none"):
        raise ValueError("SANDBOX must be 'docker' or 'none'")

    def run_test(command, root):
        if settings.sandbox == "docker":
            return run_in_sandbox(root, command, settings.command_timeout_s, logs_dir)
        return run_allowed(root, command, settings.command_timeout_s, logs_dir)

    nodes = {
        "validate": validate_node,
        "explorer": make_explorer_node(build_explorer(model, repo_root)),
        "analyst": make_analyst_node(build_analyst(model)),
        "planner": make_planner_node(build_planner(model)),
        "baseline": make_baseline_node(run_test),
        "approval": approval_node,
        "implementer": make_implementer_node(
            build_implementer(model, repo_root, settings.max_llm_calls),
            settings.max_patch_lines,
        ),
        "test_node": make_test_node(run_test),
        "reviewer": make_reviewer_node(build_reviewer(model)),
        "reporter": make_reporter_node(reports_dir),
    }
    connection = sqlite3.connect(str(checkpoint_db), check_same_thread=False)
    return build_graph(nodes, SqliteSaver(connection))
