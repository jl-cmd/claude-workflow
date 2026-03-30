#!/usr/bin/env python3
"""Stop hook -- blocks completion when workflow steps remain incomplete.

Reads JSON from stdin (Claude Code hook input).
Reads workflow state from ~/.claude/runtime/workflow-state.json.
Override state path via CLAUDE_WORKFLOW_STATE_PATH env var.
"""

import json
import os
import sys


def main():
    state_path = os.environ.get(
        "CLAUDE_WORKFLOW_STATE_PATH",
        os.path.join(
            os.path.expanduser("~"), ".claude", "runtime", "workflow-state.json"
        ),
    )

    try:
        hook_input = json.loads(sys.stdin.read())
    except Exception:
        hook_input = {}

    if hook_input.get("stop_hook_active"):
        return

    try:
        with open(state_path) as f:
            state = json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return

    if not isinstance(state, dict):
        return

    steps = state.get("steps", [])
    completed = state.get("completed", [])
    workflow = state.get("workflow", "unknown")

    if not steps:
        return

    incomplete = [step for step in steps if step not in completed]

    if not incomplete:
        return

    decision = {
        "decision": "block",
        "reason": (
            f"Workflow '{workflow}' has {len(incomplete)} incomplete step(s): "
            f"{', '.join(incomplete)}"
        ),
    }
    print(json.dumps(decision))


if __name__ == "__main__":
    main()
