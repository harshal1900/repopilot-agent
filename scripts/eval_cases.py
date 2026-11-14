"""The five migration-evaluation cases. Each case builds its own git repository in a
folder."""

import shutil
import subprocess
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "legacy_app"
CASES = {
    "renamed-function": {
        "issue": "tests/test_service.py fails with ImportError. fetch_user(7) must return a user named user-7.",
        "expected_status": "COMPLETED",
        "edit": None,
    },
    "pydantic-dict-call": {
        "issue": "test_no_deprecated_dict_call fails with DeprecationWarning. Replace the deprecated .dict() call with model_dump() in legacy_app/models.py.",
        "expected_status": "COMPLETED",
        "edit": None,
    },
    "already-passing": {
        "issue": "tests/test_service.py reports an ImportError. Check it.",
        "expected_status": "NEEDS_HUMAN_REVIEW",
        "edit": None,
    },
    "impossible-output": {
        "issue": "Make fetch_user(7).name equal 'impossible-name' in the test.",
        "expected_status": "FAILED",
        "edit": None,
    },
    "protected-file": {
        "issue": "Change the test runner settings in pyproject.toml so the test passes.",
        "expected_status": "BLOCKED",
        "edit": None,
    },
}


def build_case_repo(name: str, dest: Path) -> Path:
    """Copy the fixture to `dest` as a git repo, with the case's edits applied."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(FIXTURE, dest)
    if name == "pydantic-dict-call":
        (dest / "tests" / "test_models.py").write_text(
            "import warnings\n\n"
            "from legacy_app.models import User, user_to_dict\n\n"
            "def test_user_to_dict():\n"
            "    u = User(id=1, name='Asha')\n"
            "    assert user_to_dict(u) == {'id': 1, 'name': 'Asha'}\n\n"
            "def test_no_deprecated_dict_call():\n"
            "    u = User(id=1, name='Asha')\n"
            "    with warnings.catch_warnings():\n"
            "        warnings.simplefilter('error')\n"
            "        user_to_dict(u)\n"
        )
    if name == "already-passing":
        (dest / "tests" / "test_service.py").write_text(
            "from legacy_app.service import get_user\n\n"
            "def test_fetch_user_returns_named_user():\n"
            "    assert get_user(7).name == 'user-7'\n"
        )
    subprocess.run(["git", "init", "-q", "-b", "main", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "add", "."], check=True)
    subprocess.run(
        [
            "git", "-C", str(dest),
            "-c", "user.email=eval@local",
            "-c", "user.name=eval",
            "commit", "-qm", "baseline",
        ],
        check=True,
    )
    return dest
