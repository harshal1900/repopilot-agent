"""Typed contracts passed between the agents. Validations runs when an object is created."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Severity = Literal["low", "medium", "high", "blocker"]


class Task(BaseModel):
    id: str
    repo_path: str
    issue: str


class Analysis(BaseModel):
    reproduced: bool
    expected_behavior: str
    actual_behavior: str = ""
    root_cause_hypothesis: str = ""
    relevant_files: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str]
    unknowns: list[str] = Field(default_factory=list)

    @field_validator("acceptance_criteria")
    @classmethod
    def criteria_non_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("acceptance_criteria must contain at least one item")
        return value


class Plan(BaseModel):
    files_to_change: list[str]
    change_summary: str
    regression_test: str
    test_commands: list[str]


class patch(BaseModel):
    status: Literal["OK", "BLOCKED", "ERROR"] = "OK"
    reason: str = ""
    diff: str = ""
    changed_files: list[str] = Field(default_factory=list)


class TestResult(BaseModel):
    __test__ = False  # Prevents pytest from collecting this class as a test case
    command: str
    exit_code: int | None
    duration_s: float
    timed_out: bool
    passed_count: int | None = None
    failed_count: int | None = None
    log_path: str = ""

    @model_validator(mode="after")
    def passed_only_when_exit_zero(self) -> "TestResult":
        if self.passed and (self.timed_out or self.exit_code != 0):
            raise ValueError("passed=True requires exit_code == 0 and no timeout")
        return self


class Finding(BaseModel):
    severity: Severity
    file: str = ""
    message: str


class Report(BaseModel):
    task_id: str
    repo_path: str
    status: str
    files_changed: list[str] = Field(default_factory=list)
    tests: list[TestResult] = Field(default_factory=list)
    not_run: list[TestResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    repair_attempts: int = 0
    llm_calls: int = 0
    summary: str = ""


class Review(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
