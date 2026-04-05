---
name: tmux-cli-agent-resume
description: Resume or re-steer an existing tmux-based coding CLI agent session, re-establish the current state, and continue the job without starting over.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tmux, resume, codex, gemini, claude-code, orchestration]
    related_skills: [cli-coding-agent-orchestrator, tmux-cli-agent-checkin]
---

# Tmux CLI Agent Resume

Use this skill when the user wants to continue an already-running or previously-started tmux coding-agent session instead of starting a fresh one.

Typical requests:
- "resume the codex run"
- "continue the gemini session"
- "reattach to claude code and keep going"
- "pick up where that tmux agent left off"

## Purpose

This skill is for restoring context around an existing tmux-based coding agent and steering it forward.

Default ownership boundary:
- prefer resuming sessions that this skill stack launched and recorded under `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/`
- only resume or adopt an unrelated tmux session when the user explicitly asks for that

## Workflow

### 1) Locate the session
Identify the intended tmux session by:
- explicit session name from user
- owned supervisor/job metadata under `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/`
- recent session naming pattern within the owned set

Only fall back to arbitrary tmux-session discovery when the user explicitly asks to adopt an external session.

### 2) Reconstruct current state
Capture recent pane output and infer:
- current phase
- whether task is active, idle, blocked, or completed
- whether review has been requested or completed
- what the last meaningful milestone was

Also inspect supervisor artifacts when present:
- `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/status.json`
- `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/events.jsonl`

### 3) Decide whether resume is appropriate
Resume if:
- the job is unfinished
- the session still exists or can be safely continued
- the agent is idle or waiting but not complete

Start a fresh session instead if:
- the session is gone and context is unrecoverable
- the work drifted badly
- the repo/workdir changed materially

### 4) Send a continuation prompt
When resuming, send a concise continuation prompt rather than restating the whole job from scratch.
Examples:
- `Continue from the current state and finish the remaining implementation.`
- `Proceed to validation and fix any failing checks.`
- `You previously finished review. Now fix all substantive review findings and rerun validation.`
- `Resume phase 2 implementation and continue autonomously until the original objective is complete.`

Use the bundled resume prompt template in:
- `references/resume-template.md`

### 5) Re-enter monitoring mode
After resuming, monitor using the same principles as `cli-coding-agent-orchestrator`:
- check every ~30 seconds when needed
- do not spam
- notify user on meaningful progress changes

## State model
Use the same state model as the orchestrator:
- `launching`
- `phase_1_inspect`
- `phase_2_implement`
- `phase_3_validate`
- `review_requested`
- `review_complete_fixing`
- `commit_requested`
- `blocked`
- `completed`

## Good output format
- Session
- Agent
- Reconstructed state
- What was last completed
- Resume action taken
- What should happen next

## Anti-patterns
Do not:
- start a fresh job when a recoverable one already exists
- send a giant new prompt when a short continuation prompt is enough
- assume the agent remembers the original objective without checking pane history
- resume a session already in `completed` state unless the user asked for more work

## Desired outcome
The user should be able to say "resume that coding agent" and have you:
- find the right tmux session
- understand where it left off
- nudge it back into motion cleanly
- continue the workflow without unnecessary restart friction
