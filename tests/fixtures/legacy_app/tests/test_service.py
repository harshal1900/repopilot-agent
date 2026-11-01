from legacy_app.service import (
    fetch_user,
)  # service.py only defines get_user, so this fails


def test_fetch_user_returns_named_user():
    assert fetch_user(7).name == "user-7"
