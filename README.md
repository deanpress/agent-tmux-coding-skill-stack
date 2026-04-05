# Agent Tmux Coding Skill Stack

A portable tmux-based coding-agent skill stack for Hermes-style agents.

This repository packages a structured set of autonomous coding skills centered around vanilla Codex (`codex --yolo`) plus tmux supervision, check-ins, resume flows, and prompt templates. It also includes first-class OpenCode support and an optional OMX extension for environments that want `oh-my-codex` without making it a core dependency.

## Goals

- launch autonomous coding agents inside dedicated tmux sessions
- wait for readiness before sending the real task
- monitor without constant babysitting
- support resume/check-in workflows
- require review/fix loops for substantial jobs
- package the stack so another agent can install it from one repo

## Included skills

- `codex`
- `opencode`
- `claude-code`
- `cli-coding-agent-orchestrator`
- `tmux-cli-agent-supervisor`
- `tmux-cli-agent-checkin`
- `tmux-cli-agent-resume`
- `tmux-codex-initialization`
- `oh-my-codex` (optional extension, installed with `--include-skill oh-my-codex`)

## Structure

- `skills/autonomous-ai-agents/...` — skill directories ready to copy into an agent skill store
- `scripts/install_stack.py` — local installer for Hermes-style `~/.hermes/skills` (core stack by default, `--include-skill ...` for optional skills)
- `scripts/bootstrap_doctor.py` — prerequisite checker plus recommended install/launch commands
- `STACK_OVERVIEW.md` — concise architecture and how the pieces fit together
- `AGENT_BOOTSTRAP_PROMPT.md` — prompt you can paste into another agent to install/adapt this stack
- `extensions/omx/` — optional OMX backend notes and adoption guidance

## Intended usage with another agent

Tell the agent something like:

"Use this repo as the source of truth for a tmux-based coding orchestration stack. Run `python3 scripts/bootstrap_doctor.py --dest ~/.hermes/skills`, install the core skills into the local skill directory, and for substantial tasks use the supervised Codex tmux workflow instead of one-shot `codex exec`. If the task requires full finalization, use the equivalent of `--substantial-job --require-commit` so the flow is implement -> review -> fix -> commit. If OMX is explicitly desired, treat it as an optional extension rather than a required dependency. Then verify the scripts and docs are internally consistent."

If the other agent already knows how to install skills from a repository, giving it this repo URL plus a similar instruction should be enough.

## Safety / credential policy

This repo intentionally excludes:

- auth tokens
- host-specific credentials
- `.codex` auth files
- git credential stores
- agent runtime state
- machine-specific logs

Only portable skill content, prompt templates, and helper scripts are included.

## Publish / support status

- Safe to publish: the tracked tree is intended to be portable and credential-free.
- Supported baseline: local scripts, docs, installer flow, and tmux smoke tests for the Codex-supervisor path.
- Current focus: Codex-first orchestration. Gemini CLI, Claude Code, and OpenCode are supported by the shared supervisor, while the deepest local ergonomics are still on the Codex-first job-manager path.
- Expected operator model: supervise and inspect only sessions this stack spawned, unless you explicitly choose to adopt an external tmux session.

## Prerequisites on the target machine

- Python 3
- tmux
- Codex CLI (`codex`)
- optional: OpenCode (`opencode`) if you want that path
- optional: Claude Code (`claude`) if you want that path
- optional: Gemini CLI (`gemini`) if you want that path
- a Hermes-compatible skill directory, usually `~/.hermes/skills`

## Install locally

```bash
python3 scripts/install_stack.py --dest "$HOME/.hermes/skills"
```

To also install the optional OMX skill:

```bash
python3 scripts/install_stack.py --dest "$HOME/.hermes/skills" --include-skill oh-my-codex
```

Compatibility alias:

```bash
python3 scripts/install_stack.py --dest "$HOME/.hermes/skills" --include-omx
```

Check prerequisites and see the recommended launch command:

```bash
python3 scripts/bootstrap_doctor.py --dest "$HOME/.hermes/skills"
```

The supervisor/job-manager runtime defaults to the installed stack root and writes logs under `agent-supervisor/` next to that root. You can override the runtime root with `HERMES_HOME=/abs/path`.

## Notes

- This stack is Codex-first and uses vanilla `codex --yolo` in the orchestration layer.
- The included `codex`, `opencode`, and tmux supervisor scripts are aligned to those supported CLI surfaces.
- OpenCode is supported through the shared supervisor using plain `opencode` for interactive tmux sessions and `opencode run` for one-shot work.
- The supervisor stack can enforce `implement -> review -> fix -> commit` when launched with `--substantial-job --require-commit`.
- Commit-required runs record `HEAD` and `git status --short` evidence in the supervisor status payload.

## Optional OMX mode

If you want an OMX-powered workflow, see `extensions/omx/README.md`.

The recommendation is:
- default: vanilla Codex
- optional: OMX overlay

That keeps the repo portable while still supporting your preferred power-user workflow.

## License

This repository is released under the MIT License. See `LICENSE`.
