""" Shared state for the LangGraph workflow.
Keys annotated with `add` are list reducers: a node that returns a list for
such a key appends to the existing list instead of replacing it. """

from operator import add
from typing import Annotated, TypedDict
from repopilot.schemas import Analysis, Finding, Patch, Plan, Report, Task, TestResult


class RepoPilotState(TypedDict):
    task: Task
    status: str
    max_repair_attempts: int
    repo_map: str
    analysis: Analysis | None
    plan: Plan | None
    patch: Patch | None
    test_results: Annotated[list[TestResult], add]
    findings: Annotated[list[Finding], add]
    review_blockers: int
    repair_attempts: int
    llm_calls: int
    report: Report | None
    
def make_initial_state(task: Task, max_repair_attempts: int) -> RepoPilotState:
    return RepoPilotState(
        task=task,
        status="RCEIVED",
        max_repair_attempts=max_repair_attempts,
        repo_map="",
        analysis=None,
        plan=None,
        patch=None,
        test_results=[],
        findings=[],
        review_blockers=0,
        repair_attempts=0,
        llm_calls=0,
        report=None,
    )


