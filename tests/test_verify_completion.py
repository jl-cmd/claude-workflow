"""Tests for the verify-completion.py Stop hook.

The hook reads JSON from stdin, checks workflow state, and either:
- Exits 0 with no stdout (allow completion)
- Writes {"decision": "block", "reason": "..."} to stdout (block completion)

State file location: ~/.claude/runtime/workflow-state.json
Overridable via CLAUDE_WORKFLOW_STATE_PATH env var for testing.
"""

import json
import os
import subprocess
import sys


def run_hook(hook_script, stdin_data=None, state_file_path=None):
    """Run the hook script as a subprocess, returning (returncode, stdout, stderr).

    Args:
        hook_script: Path to the verify-completion.py script.
        stdin_data: Dict to serialize as JSON on stdin. Defaults to empty object.
        state_file_path: Path to the workflow state file. Passed via env var.
    """
    env = os.environ.copy()
    if state_file_path:
        env["CLAUDE_WORKFLOW_STATE_PATH"] = state_file_path

    stdin_text = json.dumps(stdin_data) if stdin_data is not None else "{}"

    result = subprocess.run(
        [sys.executable, hook_script],
        input=stdin_text,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    return result.returncode, result.stdout, result.stderr


class TestNoStateFile:
    """When no workflow state file exists, the hook should allow completion."""

    def test_exits_zero(self, hook_script, state_file):
        # state_file points to a path that does not exist on disk
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0

    def test_no_stdout_output(self, hook_script, state_file):
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert stdout.strip() == ""


class TestAllStepsCompleted:
    """When all steps are in the completed array, the hook allows completion."""

    def test_exits_zero(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint", "test", "build"],
        })
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0

    def test_no_blocking_output(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint", "test", "build"],
        })
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert stdout.strip() == ""


class TestIncompleteSteps:
    """When steps remain incomplete, the hook blocks completion."""

    def test_returns_block_decision(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint"],
        })
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        output = json.loads(stdout)
        assert output["decision"] == "block"

    def test_reason_includes_workflow_name(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint"],
        })
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        output = json.loads(stdout)
        assert "deploy-feature" in output["reason"]

    def test_reason_includes_incomplete_count(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint"],
        })
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        output = json.loads(stdout)
        # 2 incomplete steps: test, build
        assert "2" in output["reason"]

    def test_reason_lists_incomplete_step_names(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint"],
        })
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        output = json.loads(stdout)
        assert "test" in output["reason"]
        assert "build" in output["reason"]

    def test_exits_zero_even_when_blocking(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint"],
        })
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0


class TestStopHookActiveGuard:
    """When input JSON has stop_hook_active: true, exit immediately to prevent loops."""

    def test_exits_zero(self, hook_script, state_file, write_state):
        # Even with incomplete steps, stop_hook_active should bypass blocking
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint"],
        })
        returncode, _stdout, _stderr = run_hook(
            hook_script,
            stdin_data={"stop_hook_active": True},
            state_file_path=state_file,
        )
        assert returncode == 0

    def test_no_blocking_output(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "deploy-feature",
            "steps": ["lint", "test", "build"],
            "completed": ["lint"],
        })
        _returncode, stdout, _stderr = run_hook(
            hook_script,
            stdin_data={"stop_hook_active": True},
            state_file_path=state_file,
        )
        assert stdout.strip() == ""


class TestMalformedStateFile:
    """Malformed or corrupt state files should never crash the hook."""

    def test_invalid_json_exits_zero(self, hook_script, state_file):
        with open(state_file, "w") as f:
            f.write("{{not valid json!!!")
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0

    def test_invalid_json_no_stdout(self, hook_script, state_file):
        with open(state_file, "w") as f:
            f.write("{{not valid json!!!")
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert stdout.strip() == ""

    def test_empty_file_exits_zero(self, hook_script, state_file):
        with open(state_file, "w") as f:
            f.write("")
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0

    def test_missing_keys_exits_zero(self, hook_script, state_file, write_state):
        write_state({"unexpected": "data"})
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0

    def test_null_content_exits_zero(self, hook_script, state_file):
        with open(state_file, "w") as f:
            f.write("null")
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0


class TestEmptyStepsArray:
    """An empty steps array means nothing to enforce -- allow completion."""

    def test_exits_zero(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "empty-workflow",
            "steps": [],
            "completed": [],
        })
        returncode, _stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert returncode == 0

    def test_no_blocking_output(self, hook_script, state_file, write_state):
        write_state({
            "workflow": "empty-workflow",
            "steps": [],
            "completed": [],
        })
        _returncode, stdout, _stderr = run_hook(hook_script, state_file_path=state_file)
        assert stdout.strip() == ""
