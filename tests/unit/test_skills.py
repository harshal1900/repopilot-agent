import pytest

from repopilot.tools.skills import list_skills, load_skill


def test_list_skills_returns_both_names():
    names = {skill["name"] for skill in list_skills()}
    assert {"pydantic-v1-to-v2", "renamed-function"} <= names


def test_load_skill_returns_playbook():
    assert "AttributeError" in load_skill("renamed-function")


def test_traversal_skill_name_is_refused():
    with pytest.raises(PermissionError):
        load_skill("../../etc/passwd")
