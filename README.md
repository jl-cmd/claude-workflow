# claude-workflow

Workflow enforcement for Claude Code skills. A Stop hook blocks session completion until all defined workflow steps are marked done.

## Installation

1. Add the marketplace:

```shell
/plugin marketplace add jl-cmd/claude-workflow
```

2. Install the plugin:

```shell
/plugin install claude-workflow@jl-cmd-claude-workflow
```

## How It Works

1. A skill defines steps and writes them to a **workflow state file** at `~/.claude/runtime/workflow-state.json`.
2. Each step updates the state file's `completed` array as it finishes.
3. The **Stop hook** (`hooks/verify-completion.py`) runs when a session tries to end. If any steps remain incomplete, it blocks completion with a message listing what is left.

### State File Format

```json
{
  "workflow": "my-workflow",
  "steps": ["step-a", "step-b", "step-c"],
  "completed": ["step-a"]
}
```

- `workflow` -- name shown in the blocking message
- `steps` -- all steps that must complete
- `completed` -- steps finished so far

## Usage

Try the built-in demo:

```
/workflow-demo
```

This runs a 3-step workflow. Try ending the session before all steps finish -- the hook will block you.

## Adding Enforcement to Your Own Skills

1. In your SKILL.md frontmatter, reference the hook:

```yaml
---
name: my-skill
hooks:
  - type: Stop
    script: hooks/verify-completion.py
---
```

2. In your skill's first step, write the state file:

```python
import json, os

state_path = os.path.expanduser("~/.claude/runtime/workflow-state.json")
os.makedirs(os.path.dirname(state_path), exist_ok=True)

state = {
    "workflow": "my-skill",
    "steps": ["step-1", "step-2", "step-3"],
    "completed": [],
}

with open(state_path, "w") as f:
    json.dump(state, f, indent=2)
```

3. After each step completes, append to the `completed` array:

```python
import json

state_path = os.path.expanduser("~/.claude/runtime/workflow-state.json")

with open(state_path) as f:
    state = json.load(f)

state["completed"].append("step-1")

with open(state_path, "w") as f:
    json.dump(state, f, indent=2)
```

4. Once all steps are in `completed`, the Stop hook allows the session to end normally.

## Safety

- If the state file does not exist or is malformed, the hook allows completion (never crashes).
- If the hook input contains `stop_hook_active: true`, it exits immediately to prevent infinite loops.
- The state file path can be overridden via the `CLAUDE_WORKFLOW_STATE_PATH` environment variable (used in tests).

## License

MIT
