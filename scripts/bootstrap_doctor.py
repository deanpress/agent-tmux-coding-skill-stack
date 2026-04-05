#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import shutil
from pathlib import Path


def check_binary(name: str) -> dict[str, str | bool | None]:
    path = shutil.which(name)
    return {
        "name": name,
        "found": path is not None,
        "path": path,
    }


def install_command(repo_root: Path, dest: Path, include_skills: list[str]) -> str:
    parts = [
        "python3",
        str(repo_root / "scripts" / "install_stack.py"),
        "--dest",
        str(dest),
    ]
    for skill in include_skills:
        parts.extend(["--include-skill", skill])
    return shlex.join(parts)


def launch_command(dest: Path) -> str:
    job = dest / "autonomous-ai-agents" / "cli-coding-agent-orchestrator" / "scripts" / "codex_job.py"
    return shlex.join(
        [
            "python3",
            str(job),
            "start",
            "--agent",
            "codex",
            "--name",
            "my-job",
            "--workdir",
            "/abs/path/to/repo",
            "--prompt-file",
            "/abs/path/to/prompt.txt",
            "--substantial-job",
            "--require-commit",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check local prerequisites and print the recommended install and launch commands for this skill stack."
    )
    parser.add_argument(
        "--dest",
        default=str(Path.home() / ".hermes" / "skills"),
        help="Destination skill directory. Default: ~/.hermes/skills",
    )
    parser.add_argument(
        "--include-skill",
        action="append",
        default=[],
        help="Optional skill to include in the recommended install command. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    dest = Path(args.dest).expanduser().resolve()
    binaries = [
        check_binary("python3"),
        check_binary("tmux"),
        check_binary("git"),
        check_binary("codex"),
        check_binary("opencode"),
        check_binary("omx"),
    ]
    payload = {
        "repo_root": str(repo_root),
        "dest": str(dest),
        "prerequisites": binaries,
        "recommended_install_command": install_command(repo_root, dest, args.include_skill),
        "recommended_supervised_launch": launch_command(dest),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Bootstrap doctor")
    print("Destination:", dest)
    print("Prerequisites:")
    for item in binaries:
        status = "ok" if item["found"] else "missing"
        location = item["path"] or "-"
        print(f"- {item['name']}: {status} ({location})")
    print("Recommended install command:")
    print(payload["recommended_install_command"])
    print("Recommended supervised launch:")
    print(payload["recommended_supervised_launch"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
