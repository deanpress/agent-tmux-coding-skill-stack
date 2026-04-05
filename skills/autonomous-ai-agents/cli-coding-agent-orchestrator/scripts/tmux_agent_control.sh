#!/usr/bin/env bash
set -euo pipefail

cmd="${1:-}"
shift || true

create_session() {
  local session="$1"
  local workdir="$2"
  tmux new-session -d -s "$session" -c "$workdir"
}

has_session() {
  local session="$1"
  tmux has-session -t "$session" 2>/dev/null
}

kill_session() {
  local session="$1"
  tmux kill-session -t "$session"
}

list_sessions() {
  tmux list-sessions -F '#{session_name}\t#{session_windows}\t#{session_created_string}'
}

capture() {
  local session="$1"
  local start="${2:--200}"
  tmux capture-pane -pt "$session" -S "$start"
}

send_prompt() {
  local session="$1"
  shift
  local prompt="$*"
  tmux send-keys -t "$session" "$prompt" C-m
}

launch_in_session() {
  local session="$1"
  shift
  local launch_cmd="$*"
  tmux send-keys -t "$session" "$launch_cmd" C-m
}

pane_tty() {
  local session="$1"
  tmux display-message -p -t "$session" '#{pane_tty}'
}

case "$cmd" in
  create_session) create_session "$@" ;;
  has_session) has_session "$@" ;;
  kill_session) kill_session "$@" ;;
  list_sessions) list_sessions ;;
  capture) capture "$@" ;;
  send_prompt) send_prompt "$@" ;;
  launch_in_session) launch_in_session "$@" ;;
  pane_tty) pane_tty "$@" ;;
  *)
    echo "Usage: $0 {create_session|has_session|kill_session|list_sessions|capture|send_prompt|launch_in_session|pane_tty} ..." >&2
    exit 1
    ;;
esac
