from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = REPO_ROOT / "skills" / "autonomous-ai-agents" / "cli-coding-agent-orchestrator" / "scripts" / "tmux_cli_supervisor.py"
JOB_MANAGER = REPO_ROOT / "skills" / "autonomous-ai-agents" / "cli-coding-agent-orchestrator" / "scripts" / "codex_job.py"
FAKE_CODEX = REPO_ROOT / "tests" / "fixtures" / "fake_codex.py"


def tmux_cleanup(session: str) -> None:
    if not shutil.which("tmux"):
        return
    env = os.environ.copy()
    if hasattr(tmux_cleanup, "env"):
        env.update(tmux_cleanup.env)  # type: ignore[attr-defined]
    subprocess.run(["tmux", "kill-session", "-t", session], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)


@unittest.skipUnless(shutil.which("tmux"), "tmux is required for supervisor smoke tests")
class SupervisorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.hermes_home = self.root / "hermes-home"
        self.hermes_home.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.tmux_tmpdir = self.root / "tmux"
        self.tmux_tmpdir.mkdir()
        self.trace_file = self.root / "trace.log"
        self._write_fake_codex_wrapper()
        self.env = os.environ.copy()
        self.env.update(
            {
                "PATH": f"{self.bin_dir}:{self.env.get('PATH', '')}",
                "HERMES_HOME": str(self.hermes_home),
                "HERMES_SUPERVISOR_CODEX_BIN": str(self.bin_dir / "codex"),
                "FAKE_CODEX_TRACE_FILE": str(self.trace_file),
                "TMUX_TMPDIR": str(self.tmux_tmpdir),
                "HERMES_SUPERVISOR_READY_CHECK_SECONDS": "0.1",
                "HERMES_SUPERVISOR_MIN_READY_WAIT_CODEX": "0.2",
                "HERMES_SUPERVISOR_IDLE_NUDGE_UNCHANGED_POLLS": "2",
                "HERMES_SUPERVISOR_BLOCKED_UNCHANGED_POLLS": "4",
                "HERMES_SUPERVISOR_NUDGE_COOLDOWN_SECONDS": "0",
                "HERMES_SUPERVISOR_MAX_NUDGES": "2",
                "HERMES_SUPERVISOR_MIN_POLL_SECONDS": "0.1",
            }
        )
        tmux_cleanup.env = self.env  # type: ignore[attr-defined]
        self.sessions: list[str] = []

    def tearDown(self) -> None:
        for session in self.sessions:
            tmux_cleanup(session)
        self.tmp.cleanup()

    def _write_fake_codex_wrapper(self) -> None:
        wrapper = self.bin_dir / "codex"
        wrapper.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f'python3 "{FAKE_CODEX}" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

    def _run_supervisor(self, workdir: Path, scenario: str, *, substantial: bool = False, require_commit: bool = False, make_commit: bool = False, session: str = "test-session") -> subprocess.CompletedProcess[str]:
        self.sessions.append(session)
        extra = f"--scenario {scenario}"
        if make_commit:
            extra += " --make-commit"
        cmd = [
            "python3",
            str(SUPERVISOR),
            "--agent",
            "codex",
            "--workdir",
            str(workdir),
            "--prompt",
            "do the thing",
            "--session",
            session,
            "--poll-seconds",
            "0",
            "--ready-timeout",
            "2",
            "--notify-on-state",
            f"--extra-launch-args={extra}",
        ]
        if substantial:
            cmd.append("--substantial-job")
        if require_commit:
            cmd.append("--require-commit")
        return subprocess.run(cmd, check=True, text=True, capture_output=True, env=self.env, cwd=REPO_ROOT)

    def _run_supervisor_async(self, workdir: Path, scenario: str, *, substantial: bool = False, require_commit: bool = False, make_commit: bool = False, session: str = "test-session-async") -> subprocess.Popen[str]:
        self.sessions.append(session)
        extra = f"--scenario {scenario}"
        if make_commit:
            extra += " --make-commit"
        cmd = [
            "python3",
            str(SUPERVISOR),
            "--agent",
            "codex",
            "--workdir",
            str(workdir),
            "--prompt",
            "do the thing",
            "--session",
            session,
            "--poll-seconds",
            "0",
            "--ready-timeout",
            "2",
            "--notify-on-state",
            f"--extra-launch-args={extra}",
        ]
        if substantial:
            cmd.append("--substantial-job")
        if require_commit:
            cmd.append("--require-commit")
        return subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env, cwd=REPO_ROOT)

    def _status_path(self, session: str) -> Path:
        return self.hermes_home / "agent-supervisor" / session / "status.json"

    def _events_path(self, session: str) -> Path:
        return self.hermes_home / "agent-supervisor" / session / "events.jsonl"

    def _read_status(self, session: str) -> dict:
        return json.loads(self._status_path(session).read_text(encoding="utf-8"))

    def _read_events(self, session: str) -> list[dict]:
        lines = self._events_path(session).read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]

    def _wait_for_state(self, session: str, state: str, timeout: float = 5.0) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            path = self._status_path(session)
            if path.exists():
                payload = self._read_status(session)
                if payload.get("state") == state:
                    return payload
            time.sleep(0.1)
        raise AssertionError(f"timed out waiting for state {state}")

    def test_codex_startup_handles_trust_continue_and_readiness(self) -> None:
        workdir = self.root / "repo-startup"
        workdir.mkdir()
        result = self._run_supervisor(workdir, "steady-complete", session="startup-flow")
        self.assertIn("startup-flow", result.stdout)
        trace = self.trace_file.read_text(encoding="utf-8").splitlines()
        ready_index = next(i for i, line in enumerate(trace) if line.startswith("ready:"))
        prompt_index = next(i for i, line in enumerate(trace) if line.startswith("prompt:"))
        self.assertLess(ready_index, prompt_index)
        self.assertIn("codex_trust_prompt_accepted", result.stdout)
        self.assertIn("continue_prompt_confirmed", result.stdout)
        self.assertIn("agent_ready", result.stdout)

    def test_idle_session_gets_nudged_and_completes(self) -> None:
        workdir = self.root / "repo-idle"
        workdir.mkdir()
        self._run_supervisor(workdir, "idle-then-complete", session="idle-flow")
        events = self._read_events("idle-flow")
        self.assertIn("nudge_sent", [event["event"] for event in events])
        self.assertEqual(self._read_status("idle-flow")["state"], "completed")

    def test_active_output_with_idle_hint_does_not_nudge(self) -> None:
        workdir = self.root / "repo-active"
        workdir.mkdir()
        self._run_supervisor(workdir, "steady-complete", session="active-flow")
        events = self._read_events("active-flow")
        self.assertNotIn("nudge_sent", [event["event"] for event in events])

    def test_stalled_idle_transitions_to_blocked(self) -> None:
        workdir = self.root / "repo-blocked"
        workdir.mkdir()
        proc = self._run_supervisor_async(workdir, "stalled-idle", session="blocked-flow")
        try:
            payload = self._wait_for_state("blocked-flow", "blocked", timeout=5.0)
            self.assertEqual(payload["state"], "blocked")
        finally:
            proc.terminate()
            proc.communicate(timeout=5)

    def test_substantial_review_commit_flow_records_git_evidence(self) -> None:
        workdir = self.root / "repo-commit"
        workdir.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=workdir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=workdir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=workdir, check=True)
        (workdir / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", "seed.txt"], cwd=workdir, check=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=workdir, check=True)

        self._run_supervisor(workdir, "review-commit", substantial=True, require_commit=True, make_commit=True, session="review-commit-flow")
        status = self._read_status("review-commit-flow")
        self.assertTrue(status["commit_verified"])
        self.assertNotEqual(status["initial_head"], status["final_head"])
        self.assertIn("final_git_status", status)
        events = self._read_events("review-commit-flow")
        self.assertIn("review_requested", [event["event"] for event in events])
        self.assertIn("review_fix_prompt_sent", [event["event"] for event in events])
        self.assertIn("commit_requested", [event["event"] for event in events])

    def test_commit_marker_without_real_commit_stays_in_commit_requested(self) -> None:
        workdir = self.root / "repo-no-head"
        workdir.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=workdir, check=True)
        proc = self._run_supervisor_async(workdir, "commit-only", require_commit=True, session="commit-no-head")
        try:
            payload = self._wait_for_state("commit-no-head", "commit_requested", timeout=5.0)
            self.assertFalse(payload.get("completed", False))
            self.assertFalse(payload.get("commit_verified", False))
        finally:
            proc.terminate()
            proc.communicate(timeout=5)

    def test_job_manager_checkin_and_resume(self) -> None:
        workdir = self.root / "repo-job"
        workdir.mkdir()
        session = "job-flow"
        self.sessions.append(session)
        run_log = self.hermes_home / "agent-supervisor" / session / "run.log"
        run_log.parent.mkdir(parents=True, exist_ok=True)
        run_log.write_text("line 1\nline 2\n", encoding="utf-8")
        status = self.hermes_home / "agent-supervisor" / session / "status.json"
        status.write_text(json.dumps({"state": "phase_2_implement", "completed": False}), encoding="utf-8")
        events = self.hermes_home / "agent-supervisor" / session / "events.jsonl"
        events.write_text(json.dumps({"event": "launched"}) + "\n", encoding="utf-8")
        jobs_dir = self.hermes_home / "agent-supervisor" / "jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job_file = jobs_dir / "demo.json"
        job_file.write_text(
            json.dumps(
                {
                    "job": "demo",
                    "session": session,
                    "workdir": str(workdir),
                    "supervisor_pid": None,
                    "run_dir": str(run_log.parent),
                    "run_log": str(run_log),
                    "status_file": str(status),
                    "events_file": str(events),
                }
            ),
            encoding="utf-8",
        )

        subprocess.run(["tmux", "new-session", "-d", "-s", session, "-c", str(workdir)], check=True, env=self.env)
        subprocess.run(["tmux", "send-keys", "-t", session, "echo ready", "C-m"], check=True, env=self.env)
        time.sleep(0.1)

        checkin = subprocess.run(
            ["python3", str(JOB_MANAGER), "checkin", "demo"],
            check=True,
            text=True,
            capture_output=True,
            env=self.env,
            cwd=REPO_ROOT,
        )
        checkin_payload = json.loads(checkin.stdout)
        self.assertEqual(checkin_payload["job"], "demo")
        self.assertIn("pane_capture", checkin_payload)

        resume = subprocess.run(
            ["python3", str(JOB_MANAGER), "resume", "demo", "--prompt", "continue please"],
            check=True,
            text=True,
            capture_output=True,
            env=self.env,
            cwd=REPO_ROOT,
        )
        resume_payload = json.loads(resume.stdout)
        self.assertTrue(resume_payload["resumed"])
        updated_events = events.read_text(encoding="utf-8")
        self.assertIn("resume_prompt_sent", updated_events)


if __name__ == "__main__":
    unittest.main()
