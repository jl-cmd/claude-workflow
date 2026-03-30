---
name: workflow-demo
description: A 3-step demo workflow that enforces completion via the verify-completion Stop hook. Use to test workflow enforcement or as a template for your own skills.
hooks:
  - type: Stop
    script: hooks/verify-completion.py
---

# Workflow Demo

A 3-step demo skill that demonstrates workflow enforcement. The Stop hook blocks session completion until all steps are marked done.

## Steps

### Step 1: Initialize

Write the workflow state file to begin tracking:

```python
import json, os

state_path = os.path.expanduser("~/.claude/runtime/workflow-state.json")
os.makedirs(os.path.dirname(state_path), exist_ok=True)

state = {
    "workflow": "workflow-demo",
    "steps": ["initialize", "process", "finalize"],
    "completed": ["initialize"],
}

with open(state_path, "w") as f:
    json.dump(state, f, indent=2)
```

Announce: "Step 1/3 complete -- initialized workflow state."

### Step 2: Process

Read the state file, perform the main work, then mark this step complete:

```python
import json

state_path = os.path.expanduser("~/.claude/runtime/workflow-state.json")

with open(state_path) as f:
    state = json.load(f)

state["completed"].append("process")

with open(state_path, "w") as f:
    json.dump(state, f, indent=2)
```

Announce: "Step 2/3 complete -- processing done."

### Step 3: Finalize

Mark the final step complete. The Stop hook will now allow session completion:

```python
import json

state_path = os.path.expanduser("~/.claude/runtime/workflow-state.json")

with open(state_path) as f:
    state = json.load(f)

state["completed"].append("finalize")

with open(state_path, "w") as f:
    json.dump(state, f, indent=2)
```

Announce: "Step 3/3 complete -- all steps finished. Session completion is now allowed."
