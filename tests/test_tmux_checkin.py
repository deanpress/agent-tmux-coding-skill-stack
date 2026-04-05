from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKIN = REPO_ROOT / "skills" / "autonomous-ai-agents" / "tmux-cli-agent-checkin" / "scripts" / "tmux_checkin.sh"


class TmuxCheckinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self._write_fake_tmux()
        self.env = os.environ.copy()
        self.env.update(
            {
                "HOME": str(self.home),
                "PATH": f"{self.bin_dir}:{self.env.get('PATH', '')}",
            }
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_fake_tmux(self) -> None:
        wrapper = self.bin_dir / "tmux"
        wrapper.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "cmd=\"$1\"\n"
            "shift\n"
            "case \"$cmd\" in\n"
            "  has-session)\n"
            "    if [[ \"${1:-}\" == \"-t\" && \"${2:-}\" == \"missing\" ]]; then\n"
            "      exit 1\n"
            "    fi\n"
            "    exit 0\n"
            "    ;;\n"
            "  capture-pane)\n"
            "    echo \"CAPTURE:$*\"\n"
            "    ;;\n"
            "  *)\n"
            "    echo \"unexpected tmux command: $cmd\" >&2\n"
            "    exit 1\n"
            "    ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

    def test_owned_session_is_allowed_by_default(self) -> None:
        owned = self.home / ".hermes" / "agent-supervisor" / "owned-session"
        owned.mkdir(parents=True)
        result = subprocess.run(
            ["bash", str(CHECKIN), "owned-session"],
            text=True,
            capture_output=True,
            check=False,
            env=self.env,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("CAPTURE:-pt owned-session -S -200", result.stdout)

    def test_external_session_requires_explicit_opt_in(self) -> None:
        result = subprocess.run(
            ["bash", str(CHECKIN), "external-session"],
            text=True,
            capture_output=True,
            check=False,
            env=self.env,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("EXTERNAL_SESSION_REQUIRES_ALLOW_EXTERNAL", result.stdout)

    def test_external_session_can_be_checked_with_allow_external(self) -> None:
        result = subprocess.run(
            ["bash", str(CHECKIN), "--allow-external", "external-session"],
            text=True,
            capture_output=True,
            check=False,
            env=self.env,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("CAPTURE:-pt external-session -S -200", result.stdout)


if __name__ == "__main__":
    unittest.main()
