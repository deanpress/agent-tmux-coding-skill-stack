#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

STATE_LAUNCHING = "launching"
STATE_PHASE_1 = "phase_1_inspect"
STATE_PHASE_2 = "phase_2_implement"
STATE_PHASE_3 = "phase_3_validate"
STATE_REVIEW_REQUESTED = "review_requested"
STATE_REVIEW_FIXING = "review_complete_fixing"
STATE_COMMIT_REQUESTED = "commit_requested"
STATE_BLOCKED = "blocked"
STATE_COMPLETED = "completed"

READY_CHECK_SECONDS = 2.0
DEFAULT_READY_TIMEOUTS = {
    "codex": 45,
    "gemini": 20,
    "claude": 20,
}
MIN_READY_WAIT = {
    "codex": 18,
    "gemini": 5,
    "claude": 5,
}
TRUST_PROMPT_HINTS = [
    "do you trust the contents of this directory",
    "working with untrusted contents comes with higher risk of prompt injection",
]
CONTINUE_PROMPT_HINTS = [
    "press enter to continue",
]
READY_HINTS = {
    "codex": [
        "esc to interrupt",
        "thinking",
        "model",
        "context",
        "approval",
        "sandbox",
        "mcp",
        "gpt-",
    ],
    "gemini": [
        "esc to interrupt",
        "gemini",
        "model",
        "thinking",
    ],
    "claude": [
        "esc to interrupt",
        "claude",
        "sonnet",
        "opus",
        "thinking",
    ],
}

PHASE_MARKERS = {
    "INSPECT": STATE_PHASE_1,
    "IMPLEMENT": STATE_PHASE_2,
    "VALIDATE": STATE_PHASE_3,
}
PHASE_RE = re.compile(r"<<\s*PHASE:\s*([A-Z0-9_ -]+)\s*>>")
TASK_COMPLETE = "<< TASK COMPLETE >>"
REVIEW_FINISHED = "<< Code review finished >>"
REVIEW_FIXES_COMPLETE = "<< REVIEW FIXES COMPLETE >>"
COMMIT_COMPLETE = "<< COMMIT COMPLETE >>"
IDLE_HINT = "(esc to interrupt)"
DEFAULT_HERMES_HOME = Path(__file__).resolve().parents[4]
DEFAULT_LOG_ROOT = Path(os.environ.get("HERMES_HOME", str(DEFAULT_HERMES_HOME))).expanduser().resolve() / "agent-supervisor"


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return float(value)


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    return int(value)


def run(cmd: list[str], check: bool = True) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")
    return p.stdout


def tmux_has(session: str) -> bool:
    p = subprocess.run(["tmux", "has-session", "-t", session], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode == 0


def tmux_new(session: str, workdir: str) -> None:
    run(["tmux", "new-session", "-d", "-s", session, "-c", workdir])


def tmux_send(session: str, text: str) -> None:
    run(["tmux", "send-keys", "-t", session, text, "C-m"])


def tmux_enter(session: str) -> None:
    run(["tmux", "send-keys", "-t", session, "C-m"])


def tmux_capture(session: str, start: str = "-200") -> str:
    return run(["tmux", "capture-pane", "-pt", session, "-S", start])


def is_agent_ready(agent: str, capture: str) -> bool:
    text = capture.lower()
    hints = READY_HINTS.get(agent, [])
    return any(hint in text for hint in hints)


def has_trust_prompt(capture: str) -> bool:
    text = capture.lower()
    return any(hint in text for hint in TRUST_PROMPT_HINTS)


def has_continue_prompt(capture: str) -> bool:
    text = capture.lower()
    return any(hint in text for hint in CONTINUE_PROMPT_HINTS)


def wait_for_agent_ready(session: str, agent: str, timeout_seconds: int, notify_on_state: bool) -> str:
    min_wait = env_float(f"HERMES_SUPERVISOR_MIN_READY_WAIT_{agent.upper()}", float(MIN_READY_WAIT.get(agent, 5)))
    ready_check_seconds = env_float("HERMES_SUPERVISOR_READY_CHECK_SECONDS", READY_CHECK_SECONDS)
    started = time.time()
    trust_prompt_handled = False
    if notify_on_state:
        emit(f"[supervisor] waiting_for_agent_ready session={session} agent={agent} min_wait={min_wait}s timeout={timeout_seconds}s")
    while True:
        elapsed = time.time() - started
        capture = tmux_capture(session)
        if agent == "codex" and has_trust_prompt(capture) and not trust_prompt_handled:
            tmux_send(session, "1")
            trust_prompt_handled = True
            if notify_on_state:
                emit(f"[supervisor] codex_trust_prompt_accepted session={session} elapsed={int(elapsed)}s")
            time.sleep(ready_check_seconds)
            continue
        if agent == "codex" and has_continue_prompt(capture) and not is_agent_ready(agent, capture):
            tmux_enter(session)
            if notify_on_state:
                emit(f"[supervisor] continue_prompt_confirmed session={session} elapsed={int(elapsed)}s")
            time.sleep(ready_check_seconds)
            continue
        if elapsed >= min_wait and is_agent_ready(agent, capture):
            if notify_on_state:
                emit(f"[supervisor] agent_ready session={session} agent={agent} elapsed={int(elapsed)}s")
            return capture
        if elapsed >= timeout_seconds:
            if notify_on_state:
                emit(f"[supervisor] agent_ready_timeout session={session} agent={agent} elapsed={int(elapsed)}s proceeding_with_prompt=true")
            return capture
        time.sleep(ready_check_seconds)


def sanitize(value: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return out or "job"


def default_session(agent: str, workdir: str) -> str:
    project = sanitize(Path(workdir).name)
    ts = datetime.now().strftime("%H%M")
    return f"ai-{agent}-{project}-{ts}"


def agent_launch_command(agent: str, extra: str | None = None) -> str:
    if agent == "codex":
        codex_bin = os.environ.get("HERMES_SUPERVISOR_CODEX_BIN", "codex")
        base = f"export TERM=xterm-256color && {codex_bin} --yolo"
    elif agent == "gemini":
        gemini_bin = os.environ.get("HERMES_SUPERVISOR_GEMINI_BIN", "gemini")
        base = f"export TERM=xterm-256color && {gemini_bin} --yolo"
    elif agent == "claude":
        claude_bin = os.environ.get("HERMES_SUPERVISOR_CLAUDE_BIN", "claude")
        base = f"export TERM=xterm-256color && {claude_bin} --dangerously-skip-permissions"
    else:
        raise ValueError(f"unknown agent: {agent}")
    if extra:
        return f"{base} {extra}"
    return base


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def emit(message: str) -> None:
    print(message, flush=True)


def write_status(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def git_head(workdir: str) -> str | None:
    p = subprocess.run(
        ["git", "-C", workdir, "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if p.returncode != 0:
        return None
    return p.stdout.strip() or None


def git_status_short(workdir: str) -> str | None:
    p = subprocess.run(
        ["git", "-C", workdir, "status", "--short"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def commit_phase_completed(commit_phase_base_head: str | None, current_head: str | None) -> bool:
    if current_head is None:
        return False
    if commit_phase_base_head is None:
        return True
    return current_head != commit_phase_base_head


def infer_marker_state(capture: str) -> str | None:
    matches = PHASE_RE.findall(capture)
    if matches:
        phase = matches[-1].strip().upper().replace(" ", "_").replace("-", "_")
        return PHASE_MARKERS.get(phase)
    if COMMIT_COMPLETE in capture:
        return STATE_COMPLETED
    if REVIEW_FINISHED in capture:
        return STATE_REVIEW_FIXING
    if TASK_COMPLETE in capture:
        return STATE_REVIEW_REQUESTED
    return None


def nudge_text(current_state: str) -> str:
    if current_state == STATE_PHASE_1:
        return "Continue autonomously from inspection into implementation. Print << PHASE: IMPLEMENT >> when implementation begins."
    if current_state == STATE_PHASE_2:
        return "Continue the implementation. If core work is done, move to validation and print << PHASE: VALIDATE >>."
    if current_state == STATE_PHASE_3:
        return "Run the required validation now, fix failures, and only print << TASK COMPLETE >> when the task is truly complete and ready for review."
    if current_state == STATE_REVIEW_FIXING:
        return "Finish fixing all substantive review findings, rerun validation, and print << REVIEW FIXES COMPLETE >> when done."
    if current_state == STATE_COMMIT_REQUESTED:
        return "Create the requested git commit now, then print << COMMIT COMPLETE >> only after the commit exists."
    return "Continue autonomously until the original objective is fully complete. If you change phase, print the correct phase marker."


def main() -> int:
    ap = argparse.ArgumentParser(description="Launch and supervise a tmux-based coding CLI agent.")
    ap.add_argument("--agent", choices=["codex", "gemini", "claude"], required=True)
    ap.add_argument("--workdir", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt")
    group.add_argument("--prompt-file")
    ap.add_argument("--session")
    ap.add_argument("--extra-launch-args", default="")
    ap.add_argument("--poll-seconds", type=float, default=30)
    ap.add_argument("--ready-timeout", type=int, default=None, help="Seconds to wait for the CLI to become ready before sending the task prompt")
    ap.add_argument("--substantial-job", action="store_true")
    ap.add_argument("--require-commit", action="store_true", help="Require the session to finish with a git commit before completing")
    ap.add_argument("--launch-only", action="store_true")
    ap.add_argument("--notify-on-state", action="store_true", dest="notify_on_state", help="Print milestone updates to stdout on meaningful state changes")
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir)
    if not os.path.isdir(workdir):
        raise SystemExit(f"workdir does not exist: {workdir}")

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(os.path.abspath(args.prompt_file)).read_text(encoding="utf-8")
    assert prompt is not None

    session = args.session or default_session(args.agent, workdir)
    log_dir = DEFAULT_LOG_ROOT / session
    event_log = log_dir / "events.jsonl"
    status_file = log_dir / "status.json"
    initial_head = git_head(workdir)
    initial_git_status = git_status_short(workdir)
    blocked_unchanged_polls = env_int("HERMES_SUPERVISOR_BLOCKED_UNCHANGED_POLLS", 20)
    nudge_unchanged_polls = env_int("HERMES_SUPERVISOR_IDLE_NUDGE_UNCHANGED_POLLS", 2)
    nudge_cooldown = env_float("HERMES_SUPERVISOR_NUDGE_COOLDOWN_SECONDS", 300.0)
    max_nudges = env_int("HERMES_SUPERVISOR_MAX_NUDGES", 3)
    min_poll_seconds = env_float("HERMES_SUPERVISOR_MIN_POLL_SECONDS", 5.0)

    if not tmux_has(session):
        tmux_new(session, workdir)
        append_jsonl(event_log, {"ts": time.time(), "event": "session_created", "session": session, "workdir": workdir})
        if args.notify_on_state:
            emit(f"[supervisor] session_created session={session} workdir={workdir}")

    launch_cmd = agent_launch_command(args.agent, args.extra_launch_args.strip() or None)
    ready_timeout = args.ready_timeout or DEFAULT_READY_TIMEOUTS[args.agent]
    tmux_send(session, launch_cmd)
    ready_capture = wait_for_agent_ready(session, args.agent, ready_timeout, args.notify_on_state)
    tmux_send(session, prompt)

    state = STATE_LAUNCHING
    review_requested = False
    fix_prompt_sent = False
    commit_prompt_sent = False
    commit_verified = False
    unchanged_polls = 0
    nudge_count = 0
    last_nudge_at = 0.0
    last_hash = None
    last_state = None
    final_head: str | None = None
    final_git_status: str | None = None
    commit_phase_base_head: str | None = None

    def status_payload(current_state: str, **extra: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "session": session,
            "agent": args.agent,
            "state": current_state,
            "workdir": workdir,
            "require_commit": args.require_commit,
            "initial_head": initial_head,
            "initial_git_status": initial_git_status,
            "current_head": git_head(workdir),
            "current_git_status": git_status_short(workdir),
            "commit_verified": commit_verified,
        }
        if final_head is not None:
            payload["final_head"] = final_head
        if final_git_status is not None:
            payload["final_git_status"] = final_git_status
        payload.update(extra)
        return payload

    append_jsonl(
        event_log,
        {
            "ts": time.time(),
            "event": "launched",
            "agent": args.agent,
            "session": session,
            "launch_cmd": launch_cmd,
            "ready_timeout": ready_timeout,
            "ready_detected": is_agent_ready(args.agent, ready_capture),
            "require_commit": args.require_commit,
            "initial_head": initial_head,
            "initial_git_status": initial_git_status,
        },
    )
    write_status(status_file, status_payload(state, ready_timeout=ready_timeout, ready_detected=is_agent_ready(args.agent, ready_capture)))
    if args.notify_on_state:
        emit(f"[supervisor] launched agent={args.agent} session={session} state={state} ready_detected={is_agent_ready(args.agent, ready_capture)}")

    if args.launch_only:
        print(session)
        return 0

    while True:
        capture = tmux_capture(session)
        h = hash_text(capture)
        changed = h != last_hash
        if changed:
            unchanged_polls = 0
        else:
            unchanged_polls += 1
        last_hash = h

        inferred = infer_marker_state(capture)
        if inferred:
            state = inferred
        if TASK_COMPLETE in capture and args.substantial_job and not review_requested:
            state = STATE_REVIEW_REQUESTED
        if REVIEW_FIXES_COMPLETE in capture and args.require_commit:
            state = STATE_COMMIT_REQUESTED
        if TASK_COMPLETE in capture and not args.substantial_job and args.require_commit:
            state = STATE_COMMIT_REQUESTED
        if REVIEW_FIXES_COMPLETE in capture and not args.require_commit:
            state = STATE_COMPLETED
        if TASK_COMPLETE in capture and not args.substantial_job and not args.require_commit:
            state = STATE_COMPLETED
        if IDLE_HINT in capture and unchanged_polls >= blocked_unchanged_polls and state != STATE_COMPLETED:
            state = STATE_BLOCKED
        if COMMIT_COMPLETE in capture and args.require_commit:
            current_head = git_head(workdir)
            if commit_phase_completed(commit_phase_base_head, current_head):
                commit_verified = True
                final_head = current_head
                final_git_status = git_status_short(workdir)
                state = STATE_COMPLETED
            else:
                state = STATE_COMMIT_REQUESTED

        if state != last_state:
            append_jsonl(event_log, {"ts": time.time(), "event": "state_changed", "state": state})
            write_status(status_file, status_payload(state))
            if args.notify_on_state:
                emit(f"[supervisor] state_changed session={session} state={state}")
            last_state = state

        if state == STATE_REVIEW_REQUESTED and args.substantial_job and not review_requested:
            tmux_send(session, "/review unstaged changes")
            review_requested = True
            append_jsonl(event_log, {"ts": time.time(), "event": "review_requested"})
            if args.notify_on_state:
                emit(f"[supervisor] review_requested session={session}")
            write_status(status_file, status_payload(state, review_requested=True))

        if REVIEW_FINISHED in capture and not fix_prompt_sent:
            tmux_send(session, "Please fix all substantive issues from the review, rerun relevant validation, and print << REVIEW FIXES COMPLETE >> when done.")
            fix_prompt_sent = True
            state = STATE_REVIEW_FIXING
            append_jsonl(event_log, {"ts": time.time(), "event": "review_fix_prompt_sent"})
            if args.notify_on_state:
                emit(f"[supervisor] review_finished_fix_prompt_sent session={session}")
            write_status(status_file, status_payload(state, review_requested=True, fix_prompt_sent=True))

        if state == STATE_COMMIT_REQUESTED and args.require_commit and not commit_prompt_sent:
            commit_phase_base_head = git_head(workdir)
            tmux_send(session, "Stage the intended changes, create the requested git commit with a clear message, verify it exists, and print << COMMIT COMPLETE >> when the commit is complete.")
            commit_prompt_sent = True
            append_jsonl(
                event_log,
                {
                    "ts": time.time(),
                    "event": "commit_requested",
                    "current_head": commit_phase_base_head,
                    "current_git_status": git_status_short(workdir),
                },
            )
            if args.notify_on_state:
                emit(f"[supervisor] commit_requested session={session}")
            write_status(
                status_file,
                status_payload(
                    state,
                    review_requested=review_requested,
                    fix_prompt_sent=fix_prompt_sent,
                    commit_requested=True,
                    commit_phase_base_head=commit_phase_base_head,
                ),
            )

        now = time.time()
        should_nudge = (
            IDLE_HINT in capture and
            unchanged_polls >= nudge_unchanged_polls and
            state not in {STATE_COMPLETED, STATE_REVIEW_REQUESTED} and
            (now - last_nudge_at) >= nudge_cooldown and
            nudge_count < max_nudges
        )
        if should_nudge:
            txt = nudge_text(state)
            tmux_send(session, txt)
            last_nudge_at = now
            nudge_count += 1
            append_jsonl(event_log, {"ts": now, "event": "nudge_sent", "count": nudge_count, "text": txt, "state": state})
            if args.notify_on_state:
                emit(f"[supervisor] nudge_sent session={session} state={state} count={nudge_count}")

        if state == STATE_COMPLETED:
            final_git_status = git_status_short(workdir)
            if final_head is None:
                final_head = git_head(workdir)
            append_jsonl(
                event_log,
                {
                    "ts": time.time(),
                    "event": "completed",
                    "require_commit": args.require_commit,
                    "commit_verified": commit_verified,
                    "final_head": final_head,
                    "final_git_status": final_git_status,
                },
            )
            write_status(status_file, status_payload(state, completed=True))
            if args.notify_on_state:
                emit(f"[supervisor] completed session={session}")
            print(session)
            return 0

        time.sleep(max(args.poll_seconds, min_poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
