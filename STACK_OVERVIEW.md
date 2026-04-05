# Stack Overview

## Core flow

1. `cli-coding-agent-orchestrator` defines the orchestration protocol.
2. `tmux_cli_supervisor.py` launches and supervises the agent inside tmux.
3. `codex_job.py` provides named start/status/checkin/resume/tail/list/kill operations for the supported agents.
4. `tmux-cli-agent-checkin` and `tmux-cli-agent-resume` support mid-run operations.
5. `tmux-codex-initialization` documents safe Codex startup timing.
6. The supervisor can optionally enforce a final commit phase with `--require-commit`.

## Codex launch policy

For Codex, this stack uses:

```bash
export TERM=xterm-256color && codex --yolo
```

## OpenCode launch policy

For OpenCode, this stack uses:

```bash
export TERM=xterm-256color && opencode
```

## Important artifacts

- `skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/tmux_cli_supervisor.py`
- `skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/codex_job.py`
- `skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/run_codex_supervised.sh`
- `skills/autonomous-ai-agents/cli-coding-agent-orchestrator/references/prompt-template.md`
- `skills/autonomous-ai-agents/cli-coding-agent-orchestrator/references/supervisor-prompt-addendum.md`
- `skills/autonomous-ai-agents/tmux-cli-agent-resume/references/resume-template.md`

## Optional OMX layer

This repo also includes `skills/autonomous-ai-agents/oh-my-codex` as an optional companion skill.

It is not part of the required core path. The default `python3 scripts/install_stack.py --dest ...` flow skips it, and the default stack remains vanilla `codex --yolo`.
Install it only when OMX is explicitly desired:

```bash
python3 scripts/install_stack.py --dest "$HOME/.hermes/skills" --include-skill oh-my-codex
```

If a target environment wants OMX, use the guidance in `extensions/omx/README.md` and `extensions/omx/omx_backend_notes.md`.
