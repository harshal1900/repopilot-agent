from types import SimpleNamespace

from repopilot.evaluation import eval_status_matches, eval_stayed_in_scope, eval_tests_green


def run_with(outputs):
    return SimpleNamespace(outputs=outputs)


def test_tests_green_scores_one_only_when_tests_passed():
    assert eval_tests_green(run_with({"tests_passed": True}), None)["score"] == 1
    assert eval_tests_green(run_with({"tests_passed": False}), None)["score"] == 0


def test_stayed_in_scope_fails_when_protected_file_changed():
    assert eval_stayed_in_scope(run_with({"protected_changed": False}), None)["score"] == 1
    assert eval_stayed_in_scope(run_with({"protected_changed": True}), None)["score"] == 0


def test_status_matches_compares_expected_status():
    example = SimpleNamespace(outputs={"status": "BLOCKED"})
    assert eval_status_matches(run_with({"status": "BLOCKED"}), example)["score"] == 1
    assert eval_status_matches(run_with({"status": "COMPLETED"}), example)["score"] == 0
