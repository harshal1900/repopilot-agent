import subprocess
import sys
from pathlib import Path

from repopilot.config import Settings
from repopilot.entry import build_app

ROOT = Path(__file__).resolve().parents[2]


def test_run_task_help_works_without_model_settings():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_task.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and "--issue" in result.stdout

    def test_build_app_constructs_graph_without_calling_model(tmp_path, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "dummy-for-construction-only")
        settings = Settings(
            model_provider="google",
            model_name="gemini-3.8-flash",
            workspace_root=tmp_path,
            max_llm_calls=40,
            max_repair_attempts=2,
            command_timeout_s=60,
            max_patch_lines=300,
        )
        app = build_app(
            settings,
            tmp_path,
            tmp_path / "reports",
            tmp_path / "logs",
            tmp_path / "checkpoints.sqlite",
        )
        assert "implementer" in app.get_graph().nodes

        def test_unknown_sandbox_setting_is_refused(tmp_path, monkeypatch):
            import pytest

            monkeypatch.setenv("GOOGLE_API_KEY", "dummy-for-construction-only")
            settings = Settings(
                model_provider="google",
                model_name="gemini-3.8-flash",
                workspace_root=tmp_path,
                max_llm_calls=40,
                max_repair_attempts=2,
                command_timeout_s=60,
                max_patch_lines=300,
                sandbox="maybe",
            )
            with pytest.raises(ValueError):
                build_app(settings, tmp_path, tmp_path / "r", tmp_path / "l", tmp_path / "c.sqlite")
