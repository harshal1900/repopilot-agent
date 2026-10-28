from operator import add
from repopilot.schemas import Task
from repopilot.state import make_initial_state


def test_initial_state_has_zero_attempts():
    state = make_initial_state(Task(id="t", repo_path="/r", issue="i"), 2)
    assert state["repair_attempts"] == 0


def test_list_reducer_appends():
    # This is the reducer LangGraph uses for keys annotated with `add`.
    assert add([1], [2]) == [1, 2]
