#!/usr/bin/env bash
set -euo pipefail

allow_external=0

if [[ "${1:-}" == "--allow-external" ]]; then
  allow_external=1
  shift
fi

session="${1:-}"
start="${2:--200}"
if [[ -z "$session" ]]; then
  echo "usage: $0 [--allow-external] <session> [start_line]" >&2
  exit 1
fi

if ! tmux has-session -t "$session" 2>/dev/null; then
  echo "SESSION_NOT_FOUND"
  exit 2
fi

run_root="${HERMES_HOME:-$HOME/.hermes}/agent-supervisor"
if [[ "$allow_external" -ne 1 && ! -d "$run_root/$session" ]]; then
  echo "EXTERNAL_SESSION_REQUIRES_ALLOW_EXTERNAL"
  exit 3
fi

tmux capture-pane -pt "$session" -S "$start"
