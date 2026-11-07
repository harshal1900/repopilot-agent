"""Runs the real graph with real nodes, real git, real pytest, and fake agents (no
model calls)."""

import sqlite3
import subprocess

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from repopilot.graph import build_graph
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
from repopilot.schemas import Analysis, Finding, Patch, Plan, Review, Task
from repopilot.state import make_initial_state
from repopilot.tools.test_runner import run_allowed

FIX = """--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def f():
- return 1
+ return 2
"""
NO_FIX = FIX.replace("+ return 2", "+ return 1")  # changes nothing useful


class FakeAgent:
    """Returns the scripted answers in order. An Exception item is raised instead."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0

    def invoke(self, payload):
        self.calls += 1
        answer = self.answers[min(self.calls - 1, len(self.answers) - 1)]
        if isinstance(answer, Exception):
            raise answer
        return {"messages": [AIMessage(content="ok")], "structured_response": answer}


ANALYSIS = Analysis(
    reproduced=True,
    expected_behavior="f() returns 2",
    actual_behavior="f() returns 1",
    acceptance_criteria=["tests/test_app.py passes"],
)
PLAN = Plan(
    files_to_change=["app.py"],
    change_summary="return 2",
    regression_test="tests/test_app.py",
    test_commands=["python -m pytest tests -q"],
)
EXPLORER_TEXT = "map: app.py, tests/test_app.py"


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "tests").mkdir(parents=True)
    (root / "app.py").write_text("def f():\n return 1\n")
    (root / "tests" / "test_app.py").write_text(
        "from app import f\n\ndef test_f():\n assert f() == 2\n"
    )
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "baseline",
        ],
        check=True,
    )
    return root


def make_nodes(tmp_path, agents, max_attempts=2):
    logs = tmp_path / "logs"
    reports = tmp_path / "reports"

    def run_test(command, root):
        return run_allowed(root, command, 120, logs)

    return {
        "validate": validate_node,
        "explorer": make_explorer_node(agents["explorer"]),
        "analyst": make_analyst_node(agents["analyst"]),
        "planner": make_planner_node(agents["planner"]),
        "baseline": make_baseline_node(run_test),
        "approval": approval_node,
        "implementer": make_implementer_node(agents["implementer"], max_lines=300),
        "test_node": make_test_node(run_test),
        "reviewer": make_reviewer_node(agents["reviewer"]),
        "reporter": make_reporter_node(reports),
    }, reports


def agents_for(implementer_answers, reviewer_answers=None):
    return {
        "explorer": FakeAgent([AIMessage(content=EXPLORER_TEXT)]),
        "analyst": FakeAgent([ANALYSIS]),
        "planner": FakeAgent([PLAN]),
        "implementer": FakeAgent(implementer_answers),
        "reviewer": FakeAgent(reviewer_answers or [Review(findings=[])]),
    }


def start(graph, repo, thread):
    task = Task(id=thread, repo_path=str(repo), issue="f() should return 2")
    config = {"configurable": {"thread_id": thread}}
    result = graph.invoke(make_initial_state(task, max_repair_attempts=2), config)
    return result, config


def test_happy_path_completes_with_fix(tmp_path, repo):
    agents = agents_for([Patch(diff=FIX)])
    nodes, reports = make_nodes(tmp_path, agents)
    graph = build_graph(nodes, InMemorySaver())
    result, config = start(graph, repo, "happy")
    assert "__interrupt__" in result  # paused for approval before any file change
    assert (repo / "app.py").read_text().endswith("return 1\n")
    final = graph.invoke(Command(resume=True), config)
    assert final["status"] == "COMPLETED"
    assert "return 2" in (repo / "app.py").read_text()
    assert (reports / "happy" / "report.md").exists()


def test_rejection_changes_nothing(tmp_path, repo):
    agents = agents_for([Patch(diff=FIX)])
    nodes, _ = make_nodes(tmp_path, agents)
    graph = build_graph(nodes, InMemorySaver())
    _, config = start(graph, repo, "rejected")
    final = graph.invoke(Command(resume=False), config)
    assert final["status"] == "REJECTED"
    assert agents["implementer"].calls == 0
    assert "return 1" in (repo / "app.py").read_text()


def test_repair_loop_stops_at_limit(tmp_path, repo):
    agents = agents_for([Patch(diff=NO_FIX)])
    nodes, _ = make_nodes(tmp_path, agents)
    graph = build_graph(nodes, InMemorySaver())
    _, config = start(graph, repo, "stuck")
    final = graph.invoke(Command(resume=True), config)
    assert final["status"] == "FAILED"
    # first attempt + 2 repairs, then the loop stops
    assert agents["implementer"].calls == 3
    assert final["repair_attempts"] == 3


def test_protected_file_in_plan_is_blocked(tmp_path, repo):
    agents = agents_for([Patch(diff=FIX)])
    agents["planner"] = FakeAgent(
        [
            Plan(
                files_to_change=[".env"],
                change_summary="x",
                regression_test="t",
                test_commands=["python -m pytest tests -q"],
            )
        ]
    )
    nodes, _ = make_nodes(tmp_path, agents)
    graph = build_graph(nodes, InMemorySaver())
    final = graph.invoke(
        make_initial_state(Task(id="prot", repo_path=str(repo), issue="x"), 2),
        {"configurable": {"thread_id": "prot"}},
    )
    assert final["status"] == "BLOCKED"
    assert agents["implementer"].calls == 0


def test_passing_planned_test_needs_human_review(tmp_path, repo):
    (repo / "app.py").write_text("def f():\n return 2\n")
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-qam",
            "already fixed",
        ],
        check=True,
    )
    agents = agents_for([Patch(diff=FIX)])
    nodes, _ = make_nodes(tmp_path, agents)
    graph = build_graph(nodes, InMemorySaver())
    final, _ = start(graph, repo, "already")
    assert final["status"] == "NEEDS_HUMAN_REVIEW"
    assert agents["implementer"].calls == 0


def test_blocker_review_triggers_one_repair(tmp_path, repo):
    blocker = Review(findings=[Finding(severity="blocker", file="app.py", message="too broad")])
    agents = agents_for([Patch(diff=FIX), Patch(diff=FIX)], [blocker, Review(findings=[])])
    nodes, _ = make_nodes(tmp_path, agents)
    graph = build_graph(nodes, InMemorySaver())
    _, config = start(graph, repo, "review")
    final = graph.invoke(Command(resume=True), config)
    assert agents["reviewer"].calls == 2
    assert final["status"] == "COMPLETED"


def test_resume_after_restart_does_not_repeat_earlier_nodes(tmp_path, repo):
    db = tmp_path / "checkpoints.sqlite"
    agents = agents_for([Patch(diff=FIX)])
    nodes, _ = make_nodes(tmp_path, agents)
    first = build_graph(nodes, SqliteSaver(sqlite3.connect(str(db), check_same_thread=False)))
    _, config = start(first, repo, "resume")
    assert agents["planner"].calls == 1
    # Simulate a new process: a new graph object and a new connection to the same database.
    second = build_graph(nodes, SqliteSaver(sqlite3.connect(str(db), check_same_thread=False)))
    final = second.invoke(Command(resume=True), config)
    assert final["status"] == "COMPLETED"
    assert agents["planner"].calls == 1  # not repeated after the restart
    assert agents["explorer"].calls == 1
