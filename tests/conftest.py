"""Shared fixtures for claude-workflow plugin tests."""

import json
import os

import pytest


HOOK_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "verify-completion.py"
)


@pytest.fixture
def hook_script():
    """Return the absolute path to the verify-completion.py hook script."""
    return os.path.abspath(HOOK_SCRIPT_PATH)


@pytest.fixture
def state_file(tmp_path):
    """Create a temporary workflow state file and return its path."""
    path = tmp_path / "workflow-state.json"
    return str(path)


@pytest.fixture
def write_state(state_file):
    """Return a helper function that writes JSON content to the state file."""

    def _write(content):
        with open(state_file, "w") as f:
            json.dump(content, f)

    return _write


