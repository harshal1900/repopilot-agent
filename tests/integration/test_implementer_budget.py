"""The call budget stops a runaway implementer and records FAILED, not a crash."""

import subprocess

from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError

from repopilot.nodes import make_implementer_node
from repopilot.schemas import Analysis, Plan, Task
from repopilot.state import make_initial_state


class OverBudget:
    def invoke(self, payload):
        raise ModelCallLimitExceededError(
            thread_count=0, run_count=41, thread_limit=None, run_limit=40
        )


def test_budget_exhaustion_is_recorded_as_failed(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    node = make_implementer_node(OverBudget(), max_lines=300)
    state = make_initial_state(Task(id="b", repo_path=str(repo), issue="x"), 2)
    state["analysis"] = Analysis(
        reproduced=True, expected_behavior="e", acceptance_criteria=["tests pass"]
    )
    state["plan"] = Plan(
        files_to_change=["app.py"],
        change_summary="s",
        regression_test="t",
        test_commands=["python -m pytest -q"],
    )
    update = node(state)
    assert update["status"] == "FAILED"
