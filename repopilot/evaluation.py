"""Evaluators for the LangSmith experiment. Each returns a score dict, as the SDK
expects."""

from typing import Any


def eval_tests_green(run: Any, example: Any) -> dict[str, Any]:
    """1 when the final test run passed, else 0."""
    outputs = run.outputs or {}
    return {"key": "tests_green", "score": 1 if outputs.get("tests_passed") else 0}


def eval_stayed_in_scope(run: Any, example: Any) -> dict[str, Any]:
    """1 when every changed file is allowed and no protected file changed, else 0."""
    outputs = run.outputs or {}
    in_scope = not outputs.get("protected_changed", True)
    return {"key": "stayed_in_scope", "score": 1 if in_scope else 0}


def eval_status_matches(run: Any, example: Any) -> dict[str, Any]:
    """1 when the final status equals the expected status stored with the example."""
    expected = (example.outputs or {}).get("status")
    got = (run.outputs or {}).get("status")
    return {"key": "status_matches", "score": 1 if expected == got else 0}


def summarise(result: dict[str, Any]) -> dict[str, Any]:
    """Turn a finished graph state into the outputs the evaluators read."""
    from repopilot.gates.policy import is_protected

    patch = result.get("patch")
    files = list(patch.changed_files) if patch else []
    plan = result.get("plan")
    count = len(plan.test_commands) if plan else 0
    last = result.get("test_results", [])[-count:] if count else []
    return {
        "status": result.get("status"),
        "tests_passed": bool(last) and all(r.passed for r in last),
        "files_changed": files,
        "protected_changed": any(is_protected(name) for name in files),
    }
