# OMX Source-Checkout Validation

Use these commands only when you are working inside an `oh-my-codex` source checkout. They do not apply to a normal target-machine global install.

## Build and targeted regression checks

- `npm run build`
- targeted tests at minimum:
  - `dist/hooks/__tests__/notify-hook-auto-nudge.test.js`
  - `dist/hooks/__tests__/notify-hook-tmux-heal.test.js`
  - `dist/hooks/__tests__/notify-hook-team-tmux-guard.test.js`
  - `dist/hooks/__tests__/notify-hook-team-dispatch.test.js`
  - `dist/hooks/__tests__/notify-hook-team-worker.test.js`

## Review workflow fallback

- If `omx exec "/review ..."` fails because Codex sandboxing is broken in the environment, fall back to a manual git diff review, fix concrete issues found there, then rerun the targeted tests before opening the PR.
