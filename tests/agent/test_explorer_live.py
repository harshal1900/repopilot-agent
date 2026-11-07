"""Live test: calls the real model. Run only with: python -m pytest tests/agent -q -m
live"""

import shutil
from pathlib import Path

import pytest

from repopilot.agents.common import ask
from repopilot.agents.explorer import build_explorer
from repopilot.config import load_settings
from repopilot.models import get_model

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "legacy_app"


@pytest.mark.live
def test_explorer_names_only_files_that_exist(tmp_path):
    repo = tmp_path / "legacy"
    shutil.copytree(FIXTURE, repo)
    model = get_model(load_settings())
    result = ask(build_explorer(model, repo), "Map this repository for the failing test.")
    text = str(result["messages"][-1].content)
    assert "service.py" in text
