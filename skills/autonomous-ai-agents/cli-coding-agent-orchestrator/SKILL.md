---
name: cli-coding-agent-orchestrator
description: Orchestrate Codex CLI, Gemini CLI, Claude Code, or OpenCode in a dedicated tmux session for autonomous coding work. Creates a strong initial prompt, monitors every 30 seconds, nudges when idle, splits work into phases when needed, and requires a final review/fix loop for substantial jobs.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tmux, codex, gemini, claude-code, opencode, orchestration, autonomous-agents, review]
    related_skills: [codex, claude-code, opencode, writing-plans, subagent-driven-development, deployment-readiness-pass]
---

# CLI Coding Agent Orchestrator

Use this skill when the user explicitly wants work done via a local coding CLI agent such as:
- Codex CLI
- Gemini CLI
- Claude Code
- OpenCode

This skill is for **interactive autonomous CLI agents running inside tmux**, not one-shot `codex exec` style jobs.

## Core behavior

When using this skill, do all of the following unless the user says otherwise:
1. Write a strong, contextual prompt for the chosen CLI agent.
2. Create a dedicated tmux session for the job.
3. Launch the requested agent in high-autonomy mode.
4. Monitor silently every ~30 seconds.
5. Detect idle states and send follow-up prompts when useful.
6. Decide whether the task should be run as a single phase or multi-phase plan.
7. For big/in-depth jobs, force a final review and fix pass before calling it done.
8. Proactively notify the user when there is meaningful progress.

## Progress-update policy

Do not stay completely silent for long-running jobs. Send the user a concise autonomous update when any of these happen:
- the job is being launched
- you decide the work requires multiple phases
- the agent clearly enters a new phase
- you send a substantive follow-up / steering prompt
- you trigger the final review pass
- the code review finishes
- the agent hits a meaningful blocker or major validation failure
- the job completes

Keep these updates short and operational. Good examples:
- "Started Codex in tmux session X and entered phase 1: inspection/planning."
- "Codex appeared idle; I nudged it to continue phase 2 implementation."
- "Claude Code has entered the review/fix phase."
- "Gemini finished review; I told it to fix all review findings and rerun checks."

Avoid noisy chatter for every 30-second poll. Only message on meaningful state changes.

## Supported agents and launch modes

### Codex CLI
Preferred high-autonomy invocation:
- `export TERM=xterm-256color && codex --yolo`

Use vanilla Codex as the default Codex surface in this skill stack. In tmux, Codex may still show an initial directory trust prompt; the supervisor handles that automatically, then waits for readiness before sending the task prompt.

Use model/reasoning flags when requested, e.g.:
- `-m gpt-5.4 -c model_reasoning_effort="xhigh"`

### Gemini CLI
Preferred launch when user requests it:
- `gemini --yolo`

If local version differs, check help and use the nearest equivalent full-autonomy flag.

### Claude Code
Preferred launch when user requests it:
- `claude --dangerously-skip-permissions`

If local version differs, check help and use the nearest equivalent high-autonomy flag.

### OpenCode
Preferred interactive launch when user requests it:
- `opencode`

For one-shot non-interactive work, use:
- `opencode run "prompt"`

## When to use one phase vs multi-phase

### Single-phase is appropriate when:
- the request is narrow and cohesive
- one implementation pass is likely enough
- all changes touch one main subsystem
- validation is straightforward

Examples:
- fix a bug in one service
- add one moderate feature
- refactor one module

### Multi-phase is appropriate when:
- the task touches multiple subsystems
- there is likely a sequence like audit -> core implementation -> integration -> cleanup
- there are backend + frontend + migration + tests concerns
- the work is in-depth, high-risk, or expected to take a long time

Examples:
- production-hardening pass
- major feature spanning backend/frontend/data model
- broad refactor with validation and follow-up fixes

When multi-phase is needed, explicitly tell the CLI agent to complete one phase, summarize, then continue to the next. Prefer phases like:
1. inspect / plan
2. core implementation
3. integration / validation
4. review / cleanup

## Tmux operating model

Always run the coding CLI in a dedicated tmux session.

Default ownership boundary:
- only monitor, resume, or steer tmux sessions that this skill launched itself
- only adopt or inspect unrelated tmux sessions when the user explicitly asks for that

### Session naming
Use a deterministic session name, e.g.:
- `ai-codex-<project>-<shortid>`
- `ai-gemini-<project>-<shortid>`
- `ai-claude-<project>-<shortid>`
- `ai-opencode-<project>-<shortid>`

Sanitize project names to shell-safe/tmux-safe strings.

### Start pattern
1. `tmux new-session -d -s <session_name> -c <workdir>`
2. Start the CLI inside that session with `TERM=xterm-256color`.
3. Wait for the CLI to become ready before sending the task prompt.
   - For Codex, allow MCP startup time first; do not send the prompt immediately after launch.
4. Send the prompt only after the readiness gate passes or the explicit timeout is reached.

### Capture pattern
Use tmux capture commands to inspect the pane without interrupting the run, e.g.:
- `tmux capture-pane -pt <session_name> -S -200`

## Prompt construction standard

Every initial prompt should include:
1. Goal
2. Repo/workdir
3. Constraints
4. Relevant files/paths if known
5. Validation expectations
6. Whether this is single-phase or multi-phase
7. Finish criteria
8. Instruction not to stop early without completing the assignment
9. Supervisor markers for phase/completion transitions

Use the bundled templates in:
- `references/prompt-template.md`
- `references/supervisor-prompt-addendum.md`

### Good prompt shape
- short opening objective
- explicit repo path
- exact user complaint/request
- expected output/deliverables
- required validations
- whether to proceed autonomously

### If task is large
Explicitly say something like:
- "Treat this as a multi-phase job: phase 1 inspect/plan, phase 2 implementation, phase 3 validation/review. Continue autonomously through all phases until finished."

## Silent monitoring loop
After launch, monitor every ~30 seconds.

### What to inspect
Use tmux capture to look for:
- active generation / ongoing work
- waiting-for-input state
- completion markers
- errors
- test failures
- review completion markers

### Idle heuristic
The user-defined idle heuristic is the presence of text like:
- `(esc to interrupt)`

Interpret this carefully:
- If this appears while new output is still streaming, do nothing.
- If it appears and the pane has been unchanged across checks, treat the agent as potentially idle / waiting.
- If the content shows a summary with no further action, decide whether to prompt it onward.

### Nudge behavior
When idle and more work is clearly required, send a concise follow-up prompt into the tmux session.
Examples:
- continue to the next phase
- run the required validation
- fix the failing tests
- proceed with remaining implementation
- summarize current blockers and resolve them autonomously

Do not spam. Only nudge when the pane appears stalled or phase-complete but not goal-complete.

## Review protocol for substantial jobs
For any in-depth, broad, or high-impact job, require a review/fix loop before declaring success.

### Trigger condition
Use this review pass when:
- job was multi-phase
- touched many files
- implemented a significant feature/refactor
- was described as production-ready / hardening / major integration

### Review command
Prompt the CLI agent with:
- `/review unstaged changes`

### Review completion marker
The user-defined completion signal is:
- `<< Code review finished >>`

Once that appears:
1. inspect review findings
2. prompt the agent to fix all substantive issues
3. keep monitoring until fixes are applied and validations rerun

Suggested follow-up:
- `Please fix all substantive issues from the review, rerun relevant validation, and only stop when the reviewed result is clean.`

## Error handling

### If the CLI exits early
- capture final pane content
- determine whether task actually completed
- if not, restart or resume in the same tmux session or a fresh one

### If the CLI is confused
Send a clarifying nudge with:
- repo path
- current objective
- immediate next step

### If tool flags differ from expected
Check local help output and use the closest equivalent autonomy mode.

## Standard operating sequence

1. Determine agent: Codex / Gemini / Claude Code.
2. Decide single-phase vs multi-phase.
3. Build a high-quality prompt.
4. Create tmux session.
5. Launch the requested agent in high-autonomy mode with `TERM=xterm-256color`.
6. Wait for the CLI readiness gate before sending the prompt.
   - Codex needs a longer launch window because MCP startup often takes 15-20+ seconds.
7. Send prompt only after readiness or an explicit timeout fallback.
8. Monitor silently every ~30 seconds.
9. Nudge only when the run appears idle or phase-complete but unfinished.
10. For substantial jobs, run `/review unstaged changes`.
11. Wait for `<< Code review finished >>`.
12. Instruct agent to fix review findings and rerun validation.
13. If the user asked for a commit, require a final git commit before completion.
14. Only stop when the original goal is complete.

## Good follow-up prompts
Examples of useful nudges:
- `Continue autonomously. Complete the remaining implementation and rerun validation.`
- `Proceed to the next phase now.`
- `You appear idle. Please continue until the original goal is fully complete.`
- `Run the requested build/tests now and fix any failures.`
- `Review is complete. Fix all substantive issues, rerun checks, and continue until clean.`

## Anti-patterns
Do not:
- use plain terminal tabs instead of tmux for long jobs
- treat a temporary idle state as job completion
- skip the review loop on big jobs
- spam follow-up prompts every check
- declare success before validation and review are complete
- rely on raw `--yolo` spelling if the installed CLI uses a different equivalent flag; adapt based on local help

## Execution state machine (v2)

Track the job mentally using these states:
- `launching`
- `phase_1_inspect`
- `phase_2_implement`
- `phase_3_validate`
- `review_requested`
- `review_complete_fixing`
- `commit_requested`
- `blocked`
- `completed`

Update the user only when state changes in a meaningful way.

## Session naming convention (v2)

Use a deterministic tmux session name:
- `ai-<agent>-<project>-<timestamp>`

Examples:
- `ai-codex-treasuries-api-1430`
- `ai-gemini-wildcard-golf-0915`
- `ai-claude-bcp-dashboard-2210`
- `ai-opencode-analytics-api-1030`

Use lowercase, hyphenated project names.

## Minimal tmux command playbook (v2)

Typical patterns:
- create session:
  - `tmux new-session -d -s <session_name> -c <workdir>`
- capture pane:
  - `tmux capture-pane -pt <session_name> -S -200`
- send prompt:
  - `tmux send-keys -t <session_name> "<prompt>" C-m`
- list sessions:
  - `tmux ls`

Always inspect before sending new keys.

For repeatability, prefer using the bundled helper script:
- `scripts/tmux_agent_control.sh`

It provides stable wrappers for:
- create_session
- list_sessions
- capture
- send_prompt
- launch_in_session
- kill_session
- pane_tty

## Completion-criteria extraction (v2)

Before launch, explicitly derive:
1. what counts as done
2. what validations must pass
3. whether this is single-phase or multi-phase
4. whether final review is mandatory
5. whether a final git commit is required
6. what would count as blocked

Include these criteria in the initial prompt when possible.

## Anti-loop / anti-nag policy (v2)

Monitoring cadence may be every ~30 seconds, but nudging must be conservative.

Rules:
- do not send the same follow-up prompt twice within 5 minutes
- do not send more than 3 follow-up nudges without meaningful new output
- if output is unchanged for ~10 minutes and goal is clearly unfinished, classify as `blocked` rather than endlessly `idle`
- if blocked after repeated nudges, notify the user instead of spamming the agent

## Agent-specific prompt adjustments (v2)

### Codex
- prefer concise, execution-heavy prompting
- emphasize exact finish criteria and autonomous continuation
- use the exact launch form requested by the user; in this skill stack default to `codex --yolo`

### Gemini CLI
- keep reprompts concise and explicit
- restate immediate next step clearly when nudging
- use `gemini --yolo`

### Claude Code
- give slightly more planning structure upfront
- explicitly mark phases for larger jobs
- use `claude --dangerously-skip-permissions`

### OpenCode
- prefer plain `opencode` for interactive tmux work
- use `opencode run` for one-shot automation instead of the TUI
- keep the same supervisor markers and completion protocol as the other agents

## Review severity policy (v2)

After `/review unstaged changes` and `<< Code review finished >>`:
- fix all critical issues
- fix important issues unless clearly out of scope or disproportional
- summarize minor issues if they do not justify another long cleanup loop
- rerun relevant validation after fixes

Do not get trapped in infinite polishing over trivial review comments.

## Run-log convention (v2)

Maintain a lightweight mental or local run log with:
- session name
- agent type
- workdir
- original objective
- completion criteria
- phase transitions
- follow-up prompts sent
- review requested / completed
- blockers encountered
- final outcome

If helpful and low-friction, store it in a local scratch note/file associated with the session.

## Automated supervision infrastructure (v3)

This skill now includes actual automation infrastructure via:
- `scripts/tmux_cli_supervisor.py`
- `scripts/run_codex_supervised.sh` (thin Codex supervisor wrapper)
- `scripts/run_opencode_supervised.sh` (thin OpenCode supervisor wrapper)
- `scripts/codex_job.py` (job-name based start/status/checkin/resume/tail/list/kill manager)

The supervisor is intended to:
- launch the chosen coding CLI in tmux
- wait for a readiness gate before sending the initial prompt
- use `TERM=xterm-256color` for the launched CLI
- poll tmux automatically every ~30 seconds
- track state transitions
- detect likely idle states using `(esc to interrupt)` plus unchanged output
- request `/review unstaged changes` automatically for substantial jobs
- detect `<< Code review finished >>`
- send the fix/rerun prompt automatically
- optionally require a final git commit and wait for `<< COMMIT COMPLETE >>`
- finish only after `<< REVIEW FIXES COMPLETE >>` or `<< COMMIT COMPLETE >>` when those phases are required
- log events and status under the runtime log root, typically `${HERMES_HOME:-$HOME/.hermes}/agent-supervisor/<session>/`
- supervise only the specific tmux session it launched unless the user explicitly asks to inspect or adopt an external one

## Operational definition of done (v3)

This skillset counts as operational when you actually use it as a protocol and the supervisor script where appropriate:
- launch via tmux every time
- use deterministic session naming
- derive completion criteria before launch
- add machine-readable phase/completion markers to the prompt
- use the automated supervisor for standalone execution when appropriate
- only send meaningful progress updates to the user
- trigger review on substantial jobs
- wait for `<< Code review finished >>`
- force a fix-and-rerun pass after review
- require a final git commit when the task calls for one
- only stop when validation and completion criteria are satisfied

## Named Codex job manager

For Codex, prefer the named job manager when you want easy lifecycle operations without remembering tmux session names.

Script:
- `scripts/codex_job.py`

Supported commands:
- `start` — create a named job and launch the tmux supervisor in the background
- `status <job>` — show current state, tmux/session liveness, and completion
- `checkin <job>` — show job summary, recent pane capture, and supervisor log tail
- `resume <job> --prompt ...` — send a continuation prompt into the running tmux job and record the event
- `tail <job>` — show recent supervisor log output
- `list` — list recent jobs
- `kill <job> --remove-files` — stop the supervisor, kill the tmux session, and optionally delete job metadata/logs

This is the preferred Codex convenience layer for me to use by default.

## Desired outcome
The CLI agent should behave like a supervised autonomous worker:
- well-briefed at the start
- quietly monitored during execution
- gently redirected when stalled
- forced through a review/fix pass for serious work
- forced through a commit pass when the user asked for a commit
- only considered finished when the real user goal is done
