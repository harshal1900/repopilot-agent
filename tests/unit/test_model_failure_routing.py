"""A failed model call stops the run at the node that made it."""

from repopilot.nodes import route_after_analyst, route_after_explorer, route_after_planner


def test_failed_explorer_goes_to_reporter():
    assert route_after_explorer({"status": "NEEDS_HUMAN_REVIEW"}) == "reporter"


def test_explored_goes_to_analyst():
    assert route_after_explorer({"status": "EXPLORED"}) == "analyst"


def test_failed_analyst_goes_to_reporter():
    assert route_after_analyst({"status": "NEEDS_HUMAN_REVIEW"}) == "reporter"


def test_failed_planner_goes_to_reporter():
    assert route_after_planner({"status": "NEEDS_HUMAN_REVIEW"}) == "reporter"
