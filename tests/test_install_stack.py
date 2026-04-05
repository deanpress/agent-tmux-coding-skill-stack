from __future__ import annotations

import json
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install_stack.py"
MANIFEST = REPO_ROOT / "skills" / "install-manifest.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap_doctor = load_module(REPO_ROOT / "scripts" / "bootstrap_doctor.py", "bootstrap_doctor")
tmux_cli_supervisor = load_module(
    REPO_ROOT / "skills" / "autonomous-ai-agents" / "cli-coding-agent-orchestrator" / "scripts" / "tmux_cli_supervisor.py",
    "tmux_cli_supervisor",
)


class InstallStackTests(unittest.TestCase):
    def test_manifest_has_core_and_optional_skills(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(payload["skills"]["oh-my-codex"]["tier"], "optional")
        self.assertEqual(payload["skills"]["codex"]["tier"], "core")
        self.assertEqual(payload["skills"]["opencode"]["tier"], "core")

    def test_default_install_skips_optional_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            subprocess.run(
                ["python3", str(INSTALLER), "--dest", str(dest)],
                check=True,
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,
            )
            self.assertFalse((dest / "autonomous-ai-agents" / "oh-my-codex").exists())
            self.assertTrue((dest / "autonomous-ai-agents" / "codex").exists())

    def test_include_skill_installs_optional_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            subprocess.run(
                ["python3", str(INSTALLER), "--dest", str(dest), "--include-skill", "oh-my-codex"],
                check=True,
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,
            )
            self.assertTrue((dest / "autonomous-ai-agents" / "oh-my-codex").exists())

    def test_default_reinstall_preserves_existing_optional_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            opt = dest / "autonomous-ai-agents" / "oh-my-codex"
            opt.mkdir(parents=True)
            marker = opt / "marker.txt"
            marker.write_text("keep\n", encoding="utf-8")
            subprocess.run(
                ["python3", str(INSTALLER), "--dest", str(dest)],
                check=True,
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,
            )
            self.assertTrue(marker.exists())

    def test_bootstrap_install_command_is_shell_quoted(self) -> None:
        repo_root = Path("/tmp/repo with spaces")
        dest = Path("/tmp/dest with spaces")
        cmd = bootstrap_doctor.install_command(repo_root, dest, ["oh-my-codex"])
        self.assertIn("'/tmp/repo with spaces/scripts/install_stack.py'", cmd)
        self.assertIn("'/tmp/dest with spaces'", cmd)

    def test_bootstrap_launch_command_includes_explicit_agent(self) -> None:
        dest = Path("/tmp/hermes-skills")
        cmd = bootstrap_doctor.launch_command(dest)
        self.assertIn("--agent codex", cmd)

    def test_commit_phase_requires_new_head_after_prompt(self) -> None:
        self.assertFalse(tmux_cli_supervisor.commit_phase_completed(None, None))
        self.assertTrue(tmux_cli_supervisor.commit_phase_completed(None, "abc"))
        self.assertFalse(tmux_cli_supervisor.commit_phase_completed("abc", "abc"))
        self.assertTrue(tmux_cli_supervisor.commit_phase_completed("abc", "def"))


if __name__ == "__main__":
    unittest.main()
