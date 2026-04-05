# OMX Backend Notes

## Status

Optional only. Not required for the main repository workflow.

## Core principle

OMX should be a backend option, not a hard dependency.

## What must stay true even when OMX is enabled

- tmux remains the supervision substrate
- prompt templates and phase markers remain the contract
- check-in / resume / review-fix workflow stays the same
- no credentials or machine-local state are committed

## If adapting the supervisor for OMX

The main change is the interactive Codex launch command:

- vanilla: `export TERM=xterm-256color && codex --yolo`
- OMX: `export TERM=xterm-256color && omx --madmax --high`

If using OMX mode, validate whether your environment still needs handling for:
- OMX startup prompts
- Codex trust prompts
- extra readiness delay before the task prompt is sent
