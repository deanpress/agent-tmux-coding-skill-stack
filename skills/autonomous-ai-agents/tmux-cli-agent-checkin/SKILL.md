---
name: tmux-cli-agent-checkin
description: Check in on an existing tmux-based coding CLI agent session (Codex, Gemini CLI, or Claude Code), summarize progress, detect idleness, and optionally send a steering prompt.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tmux, monitoring, codex, gemini, claude-code, checkin, orchestration]
    related_skills: [cli-coding-agent-orchestrator]
---

# Tmux CLI Agent Check-In

Use this skill when the user asks you to check on an already-running tmux-based coding agent session.

Typical requests:
- "check in on codex"
- "see how the tmux coding job is doing"
- "check the gemini session"
- "is claude code idle?"
- "send it a follow-up if needed"

## Purpose

This skill is the companion to `cli-coding-agent-orchestrator`.
It is for inspecting and optionally steering an existing tmux session that is already running one of:
- Codex CLI
- Gemini CLI
- Claude Code

Default ownership boundary:
- only inspect or steer tmux sessions that this skill stack launched and recorded under `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/`
- only inspect unrelated tmux sessions when the user explicitly asks you to adopt or inspect an external session

## Inputs you should identify

Try to determine:
- tmux session name
- workdir/project
- agent type (codex / gemini / claude)
- original goal if available

If the session name is not given, first look for owned supervisor sessions under the runtime log root and infer the best candidate from those artifacts.
Only broaden the search to arbitrary tmux sessions when the user explicitly asks you to inspect or adopt an external session.

## Standard check-in workflow

### 1) List tmux sessions
Inspect owned supervisor sessions first and identify the likely coding-agent session from runtime artifacts and matching tmux sessions.
Useful clues:
- session names containing project/agent labels
- pane text showing `codex`, `gemini`, or `claude`
- repo path visible in prompt output

Important: if a Hermes background `process` handle for the supervisor returns `not_found`, do not treat that as completion. The process registry entry may have expired while the tmux session is still alive. In that case, fall back immediately to the owned supervisor artifacts under the runtime log root, typically `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/`, and verify the matching tmux session directly.

Only use raw `tmux ls` to search beyond the owned supervisor set when the user explicitly asked for an external session check.

### 2) Prefer tmux evidence over stale wrapper handles
If a session was launched through a supervisor/wrapper, do not rely only on the original process/session ID returned by the launcher. Those handles can become stale or disappear from the registry even while the tmux session is still alive.

Instead, verify the live tmux session directly with:
- `tmux ls`
- `tmux capture-pane -pt <session> -S -200`
- `tmux display-message -p -t <session> '#{pane_current_command} #{pane_dead} #{pane_pid}'`

### 3) Check supervisor artifacts if present
If the session was launched by the Hermessupervisor infrastructure, also inspect:
- `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/status.json`
- `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/events.jsonl`

These are strong evidence for whether the agent is still launching, implementing, validating, or completed.

### 4) Capture the active pane
Use tmux capture to inspect recent output without interrupting the agent.
Capture enough history to determine:
- current phase
- whether work is ongoing
- whether the agent is waiting/idling
- whether review is running/finished
- whether the task appears complete or blocked

If the capture only shows the original prompt text and no new output over multiple checks, treat that as a stall signal.

### 5) Infer the current state
Classify into one of:
- actively working
- likely idle / waiting
- waiting after a phase summary
- in review
- review complete, fix pass still needed
- blocked / failing
- likely complete
- stuck at launch / not progressing

### 6) Idle heuristic
The user-defined idle clue is text like:
- `(esc to interrupt)`

Treat this as a possible idle state only if:
- pane content appears unchanged across checks, or
- it looks like the agent is waiting after a summary or decision point

Do not assume every occurrence means true idleness.

### 7) Review heuristic
For substantial jobs, also look for:
- `/review unstaged changes`
- `<< Code review finished >>`
- `<< REVIEW FIXES COMPLETE >>`
- `<< COMMIT COMPLETE >>` when a final commit was requested

If review is finished and no fix prompt was sent yet, recommend or send a follow-up to fix all review findings.

### 8) Optional steering
If the user asked you to do more than inspect, you may send a concise follow-up prompt into the tmux session.

Good follow-up prompts:
- "Continue to the next phase and complete the remaining work autonomously."
- "You appear idle. Please continue until the original objective is fully complete."
- "Run the required validation now and fix any failing checks."
- "Code review is finished. Please fix all substantive findings, rerun checks, and continue until clean."
- "If you are stalled, report the exact blocker and then proceed with the next actionable step."

### 9) Report back cleanly
Return a concise summary with:
- session name
- agent type
- apparent state
- latest meaningful activity
- whether you sent a follow-up prompt
- what to expect next

## Good output format
- Session: `...`
- Agent: `Codex/Gemini/Claude Code`
- Status: `working / idle / blocked / review / complete-ish / stuck`
- Latest activity: `...`
- Action taken: `none / sent follow-up prompt`
- Recommendation: `...`

## Tmux techniques
Typical commands you may need:
- `tmux ls`
- `tmux capture-pane -pt <session> -S -200`
- `tmux send-keys -t <session> "..." C-m`

Always inspect before sending keys.

For repeatability, prefer using the bundled helper script:
- `scripts/tmux_checkin.sh <session> [-200]`
- `scripts/tmux_checkin.sh --allow-external <session> [-200]` only when the user explicitly asked you to inspect a tmux session this stack did not spawn

## Anti-patterns
Do not:
- assume the newest tmux session is the correct one without checking pane content
- inspect unrelated tmux sessions by default
- spam follow-up prompts
- misclassify `esc to interrupt` as idle when output is still progressing
- declare completion before checking for unfinished review/fix work

## State inference model (v2)

When checking in, classify the session into one of these states:
- `launching`
- `phase_1_inspect`
- `phase_2_implement`
- `phase_3_validate`
- `review_requested`
- `review_complete_fixing`
- `commit_requested`
- `blocked`
- `completed`

Use the most conservative plausible classification.

## Anti-nag policy (v2)

If you are asked to send a follow-up prompt:
- avoid repeating the same prompt too frequently
- do not send multiple nudges unless there is evidence the previous one did not move the job forward
- if repeated checks show unchanged output for ~10 minutes, classify as `blocked`

## Standard concise output (v2)

Prefer output in this shape:
- Session
- Agent
- State
- Latest meaningful activity
- Whether pane looks idle or active
- Whether review is pending/finished
- Action taken (if any)
- Next likely step

## Desired outcome
The user should be able to ask for a quick check-in at any time and get:
- a trustworthy status summary
- an informed judgment on whether the agent is stalled or progressing
- a useful nudge sent only when appropriate
