#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPERVISOR="${SCRIPT_DIR}/tmux_cli_supervisor.py"
DEFAULT_HERMES_HOME="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
HERMES_HOME="${HERMES_HOME:-${DEFAULT_HERMES_HOME}}"

usage() {
  cat <<'EOF'
Usage:
  run_opencode_supervised.sh --workdir /abs/path --prompt-file /abs/path/prompt.txt [options]
  run_opencode_supervised.sh --workdir /abs/path --prompt 'do the thing' [options]

Options:
  --session NAME           Optional tmux session name
  --poll-seconds N         Poll interval for supervisor (default: 30)
  --ready-timeout N        Readiness timeout in seconds (default: supervisor default)
  --substantial-job        Trigger automated review/fix loop
  --require-commit         Require a final git commit before completion
  --notify-on-state        Print meaningful supervisor state updates
  --launch-only            Launch and exit after startup
  --extra-launch-args ARG  Extra args appended to the OpenCode launch command

Notes:
  - OpenCode is launched directly in tmux with: export TERM=xterm-256color && opencode
  - Logs/status are written under ${HERMES_HOME}/agent-supervisor/<session>/
  - For job-name based management, use codex_job.py --agent opencode instead of this thin wrapper.
EOF
}

args=(--agent opencode)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir|--prompt|--prompt-file|--session|--poll-seconds|--ready-timeout|--extra-launch-args)
      args+=("$1" "$2")
      shift 2
      ;;
    --substantial-job|--require-commit|--notify-on-state|--launch-only)
      args+=("$1")
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

HERMES_HOME="$HERMES_HOME" python3 "$SUPERVISOR" "${args[@]}"
