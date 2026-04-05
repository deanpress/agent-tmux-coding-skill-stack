# OMX Tmux Routing Hardening

Use this reference when fixing or reviewing OMX notify-hook, auto-nudge, or tmux write-path behavior inside an `oh-my-codex` source checkout.

## Core rule

Treat "Codex-looking pane" and "OMX-managed pane" as different concepts. Any write or injection path must verify OMX-managed ownership first.

## Ownership hierarchy

1. Allow team-worker contexts explicitly.
2. Require a live, non-stale `.omx/state/session.json` for the current workspace.
3. Require invocation session identity (`session-id` / `session_id` payload, or propagated `OMX_SESSION_ID` / `CODEX_SESSION_ID` / `SESSION_ID`) to match the active OMX session id.
4. Prefer authoritative tmux bindings stored in session state:
   - exact `tmux_pane_id` match if present
   - otherwise exact `tmux_session_name` match if present
5. Only use PID ancestry as a fallback when no authoritative tmux binding is stored.

## Practical routing rules

- Do not use heuristic pane discovery as authorization for writes.
- Keep leader-session managed ownership checks out of team dispatch and worker routing.
- Preserve explicit team-session dispatch fallback when a request only has a team tmux session target.
- Team dispatch must still resolve panes inside `omx-team-*` sessions even when that session is different from the leader's managed session.

## Fixture guidance

- Simulate managed sessions fully in tmux tests:
  - realistic `.omx/state/session.json`
  - realistic `list-panes -t <session>` rows
  - tmux `#S` output that matches the managed session naming algorithm
- Do not leave fixtures on generic names like `session-test` or `devsess`.

## Operator note

If plain tmux `codex` sessions are being nudged unexpectedly, inspect notify-hook and auto-nudge first. If you need to disable auto-nudge entirely on the machine, use:

```json
{
  "autoNudge": { "enabled": false }
}
```
