---
name: opencode
description: Delegate coding tasks to OpenCode CLI. Use for interactive tmux-supervised coding work, one-shot runs with `opencode run`, reviews, and autonomous repo tasks.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Code-Review, Refactoring]
    related_skills: [codex, claude-code, cli-coding-agent-orchestrator]
---

# OpenCode

Delegate coding tasks to OpenCode via the Hermes terminal. In this stack, OpenCode is supported as an additional tmux-supervised coding CLI alongside Codex, Gemini CLI, and Claude Code.

## Prerequisites

- OpenCode installed and on `PATH`
- Authenticated provider credentials for the models you want OpenCode to use
- Use `pty=true` for interactive `opencode` launches

## Interactive tmux work

OpenCode starts the TUI when run without a subcommand.

```
terminal(command="opencode", workdir="$HOME/project", pty=true)
```

For long unattended work, prefer the tmux supervisor skill over a plain terminal session.

## One-shot tasks

Use `opencode run` for non-interactive automation:

```
terminal(command="opencode run 'Review the auth flow and explain the main risks'", workdir="$HOME/project", pty=true)
```

## Supervised autonomous work

For substantial repo tasks, use the shared tmux supervisor infrastructure:

```
python3 "$HERMES_HOME/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/tmux_cli_supervisor.py" \
  --agent opencode \
  --workdir /abs/path/to/repo \
  --prompt-file /abs/path/to/prompt.txt \
  --substantial-job \
  --require-commit \
  --notify-on-state
```

Thin wrapper:

```
bash "$HERMES_HOME/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/run_opencode_supervised.sh" \
  --workdir /abs/path/to/repo \
  --prompt-file /abs/path/to/prompt.txt \
  --substantial-job \
  --require-commit \
  --notify-on-state
```

Named-job path:

```
python3 "$HERMES_HOME/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/codex_job.py" \
  start --agent opencode --name my-job --workdir /abs/path/to/repo --prompt-file /abs/path/to/prompt.txt
```

## Rules

1. Prefer plain `opencode` for interactive tmux sessions.
2. Prefer `opencode run` for one-shot non-interactive jobs.
3. For substantial coding work, prefer the shared tmux supervisor rather than ad hoc background sessions.
4. Keep the same completion discipline as the rest of this stack: validate, review substantial jobs, and require a final commit when the user asked for one.
