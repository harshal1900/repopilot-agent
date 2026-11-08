"""A refused diff goes back to the Implementer while repair attempts remain."""

from repopilot.nodes import route_after_implementer


def _state(status, attempts, max_attempts=2):
    return {"status": status, "repair_attempts": attempts, "max_repair_attempts": max_attempts}


def test_refused_patch_retries_within_limit():
    assert route_after_implementer(_state("PATCH_REFUSED", 1)) == "implementer"


def test_refused_patch_stops_after_limit():
    assert route_after_implementer(_state("PATCH_REFUSED", 3)) == "reporter"


def test_implemented_patch_goes_to_tests():
    assert route_after_implementer(_state("IMPLEMENTED", 0)) == "test_node"
