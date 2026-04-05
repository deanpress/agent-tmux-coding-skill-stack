---
name: tmux-cli-agent-supervisor
description: Use the standalone tmux supervisor infrastructure to launch and autonomously supervise Codex CLI, Gemini CLI, or Claude Code without requiring continual manual polling.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tmux, supervisor, codex, gemini, claude-code, automation]
    related_skills: [cli-coding-agent-orchestrator, tmux-cli-agent-checkin, tmux-cli-agent-resume]
---

# Tmux CLI Agent Supervisor

Use this skill when the user wants actual automated supervision infrastructure rather than manual polling by the assistant.

## What this skill is
This skill uses the standalone supervisor script:
- `scripts/tmux_cli_supervisor.py`

It can:
- launch a coding CLI in tmux
- wait for the CLI readiness gate before sending the initial prompt
- poll automatically every ~30 seconds
- detect phase markers
- detect likely idleness
- request code review on substantial jobs
- detect review completion
- trigger the fix/rerun pass
- optionally require a final git commit
- maintain run logs under the runtime log root, typically `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/`

Default ownership boundary:
- the supervisor only watches the tmux session it launched
- it does not scan unrelated tmux sessions unless the user explicitly asks for external-session inspection through a separate check-in/resume action

## Required prompt markers
The launched coding-agent prompt should include the supervisor marker requirements from:
- `references/supervisor-prompt-addendum.md`

Especially:
- `<< PHASE: INSPECT >>`
- `<< PHASE: IMPLEMENT >>`
- `<< PHASE: VALIDATE >>`
- `<< TASK COMPLETE >>`
- `<< REVIEW FIXES COMPLETE >>`
- `<< COMMIT COMPLETE >>` when a final commit is required

## Typical usage
1. Build a strong initial prompt.
2. Append the supervisor marker addendum.
3. Decide whether the job is substantial.
4. Launch the supervisor script with:
   - agent
   - workdir
   - prompt or prompt file
   - poll interval
   - readiness timeout when needed
   - substantial job flag if needed
   - `--notify-on-state` so milestone updates are printed to stdout
5. Prefer launching it as a Hermes background terminal process with `check_interval=30` so meaningful supervisor output can be delivered back to the user autonomously.
6. Use `tmux-cli-agent-checkin` to inspect progress later.
7. Use `tmux-cli-agent-resume` if re-steering is needed.

Example launch pattern:
- `python3 "${HERMES_HOME:-$HOME/.hermes}/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/tmux_cli_supervisor.py" --agent codex --workdir /abs/path --prompt-file /abs/path/prompt.txt --ready-timeout 45 --substantial-job --require-commit --notify-on-state`
- thin wrapper: `bash "${HERMES_HOME:-$HOME/.hermes}/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/run_codex_supervised.sh" --workdir /abs/path --prompt-file /abs/path/prompt.txt --ready-timeout 45 --substantial-job --require-commit --notify-on-state`
- job manager: `python3 "${HERMES_HOME:-$HOME/.hermes}/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/codex_job.py" start --name my-job --workdir /abs/path --prompt-file /abs/path/prompt.txt --substantial-job --require-commit`
- job check-in: `python3 "${HERMES_HOME:-$HOME/.hermes}/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/codex_job.py" checkin my-job`
- job resume: `python3 "${HERMES_HOME:-$HOME/.hermes}/skills/autonomous-ai-agents/cli-coding-agent-orchestrator/scripts/codex_job.py" resume my-job --prompt "Continue from the current state and finish the remaining work."`

For Codex in this skill stack, the supervisor launches `codex --yolo` directly. The supervisor auto-accepts the initial Codex trust prompt in tmux, waits for readiness, sends the task prompt, drives the review/fix loop for substantial jobs, and can optionally hold completion until a git commit is created. The job manager adds named start/status/checkin/resume/tail/list/kill operations.

## Desired outcome
The coding job should continue under actual automated supervision infrastructure, not just ad hoc assistant polling.

For Codex specifically, prefer the named wrapper `scripts/codex_job.py` when you want start/status/checkin/resume/tail/list/kill ergonomics on top of the supervisor.
