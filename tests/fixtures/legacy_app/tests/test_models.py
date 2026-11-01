from legacy_app.models import User, user_to_dict


def test_user_to_dict():
    u = User(id=1, name="Asha")
    assert user_to_dict(u) == {"id": 1, "name": "Asha"}
