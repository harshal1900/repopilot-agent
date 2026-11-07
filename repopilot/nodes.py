"""Workflow nodes. Each node takes the state and returns only the keys it changes.
Agents propose (text or typed objects). Code decides: the gate checks paths and
commands, the test runner records exit codes, and the reporter writes the facts.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langgraph.types import interrupt
from pydantic import ValidationError

from repopilot.agents.common import ask
from repopilot.gates.policy import is_command_allowed, is_protected
from repopilot.schemas import Analysis, Finding, Patch, Plan, Report, TestResult
from repopilot.state import RepoPilotState
from repopilot.tools.git_tools import git_diff, run_git
from repopilot.tools.patch_tools import apply_patch, files_in_diff

RunTest = Callable[[str, Path], TestResult]
FINAL_STOP = {"BLOCKED", "ERROR", "FAILED", "REJECTED", "NEEDS_HUMAN_REVIEW"}


def _last_text(result: dict[str, Any]) -> str:
    return str(result["messages"][-1].content)


def _plan(state: RepoPilotState) -> Plan:
    if state["plan"] is None:
        raise RuntimeError("no plan in state: the planner has not run")
    return state["plan"]


def _analysis(state: RepoPilotState) -> Analysis:
    if state["analysis"] is None:
        raise RuntimeError("no analysis in state: the analyst has not run")
    return state["analysis"]


def _failing_output(state: RepoPilotState) -> str:
    failing = [r for r in state["test_results"] if not r.passed]
    if not failing or not failing[-1].log_path:
        return ""
    return Path(failing[-1].log_path).read_text(encoding="utf-8")[-3000:]


def validate_node(state: RepoPilotState) -> dict[str, Any]:
    path = Path(state["task"].repo_path)
    if not path.is_dir() or not (path / ".git").exists():
        return {"status": "BLOCKED"}
    return {"status": "VALIDATED"}


def make_explorer_node(agent) -> Callable[[RepoPilotState], dict[str, Any]]:
    def explorer_node(state: RepoPilotState) -> dict[str, Any]:
        result = ask(
            agent,
            f"Issue:\n{state['task'].issue}\n\nMap the repository for this issue.",
        )
        return {
            "repo_map": _last_text(result),
            "status": "EXPLORED",
            "llm_calls": state["llm_calls"] + 1,
        }

    return explorer_node


def make_analyst_node(agent) -> Callable[[RepoPilotState], dict[str, Any]]:
    def analyst_node(state: RepoPilotState) -> dict[str, Any]:
        message = f"Issue:\n{state['task'].issue}\n\nRepository map:\n{state['repo_map']}"
        analysis: Analysis | None = None
        for _ in range(2):  # one retry on a malformed answer
            try:
                analysis = ask(agent, message)["structured_response"]
                break
            except (ValidationError, ValueError, KeyError, TypeError):
                analysis = None
        if analysis is None:
            return {
                "status": "NEEDS_HUMAN_REVIEW",
                "llm_calls": state["llm_calls"] + 2,
            }
        return {
            "analysis": analysis,
            "status": "ANALYSED",
            "llm_calls": state["llm_calls"] + 1,
        }

    return analyst_node


def make_planner_node(agent) -> Callable[[RepoPilotState], dict[str, Any]]:
    def planner_node(state: RepoPilotState) -> dict[str, Any]:
        analysis = _analysis(state)
        message = f"Analysis:\n{analysis.model_dump_json(indent=2)}\n\nRepository map:\n{state['repo_map']}"
        plan: Plan = ask(agent, message)["structured_response"]
        updates: dict[str, Any] = {
            "plan": plan,
            "status": "PLANNED",
            "llm_calls": state["llm_calls"] + 1,
        }
        if any(is_protected(name) for name in plan.files_to_change):
            updates["status"] = "BLOCKED"
        if not all(is_command_allowed(c) for c in plan.test_commands):
            updates["status"] = "BLOCKED"
        return updates

    return planner_node


def make_baseline_node(run_test: RunTest) -> Callable[[RepoPilotState], dict[str, Any]]:
    def baseline_node(state: RepoPilotState) -> dict[str, Any]:
        root = Path(state["task"].repo_path)
        results = [run_test(command, root) for command in _plan(state).test_commands]
        updates: dict[str, Any] = {"test_results": results, "status": "BASELINE"}
        if all(r.passed for r in results):
            # The planned test already passes, so there is nothing to repair. A person must check.
            updates["status"] = "NEEDS_HUMAN_REVIEW"
        return updates

    return baseline_node


def route_after_validate(state: RepoPilotState) -> str:
    return "reporter" if state["status"] == "BLOCKED" else "explorer"


def route_after_planner(state: RepoPilotState) -> str:
    return "reporter" if state["status"] == "BLOCKED" else "baseline"


def route_after_baseline(state: RepoPilotState) -> str:
    return "reporter" if state["status"] == "NEEDS_HUMAN_REVIEW" else "approval"


def approval_node(state: RepoPilotState) -> dict[str, Any]:
    # interrupt() pauses the graph here. The run resumes with Command(resume=True) or Command(resume=False).
    decision = interrupt(
        {
            "task": state["task"].id,
            "plan": _plan(state).model_dump(),
            "question": "Approve applying this plan to the workspace?",
        }
    )
    return {"status": "APPROVED" if decision else "REJECTED"}


def make_implementer_node(agent, max_lines: int) -> Callable[[RepoPilotState], dict[str, Any]]:
    def implementer_node(state: RepoPilotState) -> dict[str, Any]:
        root = Path(state["task"].repo_path)

        if state["patch"] and state["patch"].changed_files:
            # Repair attempt: return to the known state before the new diff is applied.
            run_git(root, ["checkout", "--", *state["patch"].changed_files])
        message = (
            f"Plan:\n{_plan(state).model_dump_json(indent=2)}\n\n"
            f"Previous failing output (if any):\n{_failing_output(state)}"
        )
        try:
            patch: Patch = ask(agent, message)["structured_response"]
        except (
            ModelCallLimitExceededError,
            ValidationError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            return {
                "status": "FAILED",
                "patch": Patch(status="ERROR", reason=str(error)),
                "llm_calls": state["llm_calls"] + 1,
            }
        calls = state["llm_calls"] + 1
        if patch.status != "OK":
            return {"patch": patch, "status": "BLOCKED", "llm_calls": calls}
        applied, reason = apply_patch(root, patch.diff, max_lines)
        if not applied:
            return {
                "patch": Patch(status="ERROR", reason=reason),
                "status": "ERROR",
                "llm_calls": calls,
            }
        return {
            "patch": patch.model_copy(update={"changed_files": files_in_diff(patch.diff)}),
            "status": "IMPLEMENTED",
            "llm_calls": calls,
        }

    return implementer_node


def route_after_approval(state: RepoPilotState) -> str:
    return "reporter" if state["status"] == "REJECTED" else "implementer"


def route_after_implementer(state: RepoPilotState) -> str:
    return "reporter" if state["status"] in FINAL_STOP else "test_node"


def make_test_node(run_test: RunTest) -> Callable[[RepoPilotState], dict[str, Any]]:
    def test_node(state: RepoPilotState) -> dict[str, Any]:
        root = Path(state["task"].repo_path)
        results = [run_test(command, root) for command in _plan(state).test_commands]
        updates: dict[str, Any] = {"test_results": results, "status": "TESTED"}
        if not all(r.passed for r in results):
            updates["repair_attempts"] = state["repair_attempts"] + 1
        return updates

    return test_node


def route_after_test(state: RepoPilotState) -> str:
    count = len(_plan(state).test_commands)
    if all(r.passed for r in state["test_results"][-count:]):
        return "reviewer"
    if state["repair_attempts"] <= state["max_repair_attempts"]:
        return "implementer"
    return "reporter"


def make_reviewer_node(agent) -> Callable[[RepoPilotState], dict[str, Any]]:
    def reviewer_node(state: RepoPilotState) -> dict[str, Any]:
        criteria = "\n".join(f"- {c}" for c in _analysis(state).acceptance_criteria)
        results = "\n".join(f"{r.command}: exit {r.exit_code}" for r in state["test_results"])
        message = (
            f"Acceptance criteria:\n{criteria}\n\nTest results:\n{results}\n\n"
            f"Diff:\n{git_diff(Path(state['task'].repo_path))}"
        )
        findings: list[Finding] = ask(agent, message)["structured_response"].findings
        blockers = sum(1 for f in findings if f.severity == "blocker")
        updates: dict[str, Any] = {
            "findings": findings,
            "review_blockers": blockers,
            "status": "REVIEWED",
            "llm_calls": state["llm_calls"] + 1,
        }
        if blockers:
            updates["repair_attempts"] = state["repair_attempts"] + 1
        return updates

    return reviewer_node


def route_after_review(state: RepoPilotState) -> str:
    if state["review_blockers"] == 0:
        return "reporter"
    if state["repair_attempts"] <= state["max_repair_attempts"]:
        return "implementer"
    return "reporter"


def final_status(state: RepoPilotState) -> str:
    if state["status"] in FINAL_STOP:
        return state["status"]
    if not state["test_results"]:
        return "FAILED"
    count = len(_plan(state).test_commands) if _plan(state) else 0
    if not all(r.passed for r in state["test_results"][-count:]):
        return "FAILED"
    if state["review_blockers"] > 0:
        return "NEEDS_HUMAN_REVIEW"
    return "COMPLETED"


def build_report(state: RepoPilotState, status: str) -> Report:
    tests = state["test_results"]
    passed = sum(1 for r in tests if r.passed)
    plan = _plan(state)
    return Report(
        task_id=state["task"].id,
        repo_path=state["task"].repo_path,
        status=status,
        files_changed=state["patch"].changed_files if state["patch"] else [],
        tests=tests,
        not_run=plan.test_commands if (plan and not tests) else [],
        findings=state["findings"],
        repair_attempts=state["repair_attempts"],
        llm_calls=state["llm_calls"],
        summary=(
            f"{status}: {passed} of {len(tests)} test runs passed; "
            f"{state['review_blockers']} blocker finding(s); "
            f"{state['repair_attempts']} repair attempt(s)."
        ),
    )


def write_report(report: Report, reports_dir: Path) -> Path:
    folder = Path(reports_dir) / report.task_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    lines = [
        f"# RepoPilot report: {report.task_id}",
        "",
        f"**Status:** {report.status}",
        "",
        report.summary,
        "",
        "## Files changed",
    ]
    lines += [f"- {name}" for name in report.files_changed] or ["- none"]
    lines += ["", "## Tests"]
    lines += [f"- `{t.command}`: exit {t.exit_code}, passed={t.passed}" for t in report.tests] or [
        "- none run"
    ]
    lines += [f"- NOT RUN: `{c}`" for c in report.not_run]
    lines += ["", "## Findings"]
    lines += [f"- [{f.severity}] {f.file}: {f.message}" for f in report.findings] or ["- none"]
    (folder / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return folder


def make_reporter_node(reports_dir: Path) -> Callable[[RepoPilotState], dict[str, Any]]:
    def reporter_node(state: RepoPilotState) -> dict[str, Any]:
        status = final_status(state)
        report = build_report(state, status)
        write_report(report, reports_dir)
        return {"status": status, "report": report}

    return reporter_node
