---
name: codex
description: Delegate coding tasks to OpenAI Codex CLI agent. Use for building features, refactoring, PR reviews, and batch issue fixing. Requires the codex CLI and a git repository.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) directly via the Hermes terminal. In this stack, vanilla `codex --yolo` is the default interactive surface for autonomous coding work.

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- Codex installed: `npm install -g @openai/codex`
- OpenAI auth configured for Codex
- **Must run inside a git repository** for normal coding workflows unless you explicitly pass `--skip-git-repo-check`
- Use `pty=true` for interactive `codex` launches

## One-Shot Tasks

Use `codex exec` by default for non-interactive Codex jobs.

```
terminal(command="codex exec --yolo -c model_reasoning_effort=\"high\" 'Add dark mode toggle to settings'", workdir="$HOME/project", pty=true)
```

For scratch work:
```
terminal(command="TMP=$(mktemp -d) && cd \"$TMP\" && git init && codex exec --yolo --skip-git-repo-check 'Build a snake game in Python'", pty=true)
```

For interactive work, launch Codex directly:
```
terminal(command="codex --yolo", workdir="$HOME/project", pty=true)
```

## Background Mode (Long Tasks)

For long non-interactive runs, prefer `codex exec` in the background. For long interactive/autonomous work, prefer the tmux supervisor skill instead of a plain background process.

```
# Start Codex exec in background with PTY
terminal(command="codex exec --yolo -c model_reasoning_effort=\"high\" 'Refactor the auth module'", workdir="$HOME/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if the process asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags / Surfaces

| Surface | Effect |
|------|--------|
| `codex --yolo` | Preferred interactive launch for autonomous Codex work |
| `codex exec --yolo "prompt"` | Preferred one-shot execution |
| `--dangerously-bypass-approvals-and-sandbox` | Alternative raw Codex exec flag when you want no sandbox / no approvals |

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git \"$REVIEW\" && cd \"$REVIEW\" && gh pr checkout 42 && codex exec --yolo 'Review PR #42 against origin/main and summarize findings with file references'", pty=true)
```

## Parallel Issue Fixing with Worktrees

For this class of task, use multiple supervised tmux Codex sessions or separate worktrees you control explicitly.

```
terminal(command="codex exec --yolo 'Fix the assigned issue set, verify each change, and report completion evidence'", workdir="$HOME/project", background=true, pty=true)
```

If you specifically need separate worktrees you control yourself, create them manually and run `codex exec --yolo` inside each worktree.

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="$HOME/project")

# Review multiple PRs in parallel
terminal(command="codex exec --yolo 'Review PR #86. Use git diff origin/main...origin/pr/86 and summarize the most important findings.'", workdir="$HOME/project", background=true, pty=true)
terminal(command="codex exec --yolo 'Review PR #87. Use git diff origin/main...origin/pr/87 and summarize the most important findings.'", workdir="$HOME/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="$HOME/project")
```

## Rules

1. **Prefer vanilla Codex in this stack** — use `codex --yolo` and `codex exec --yolo` as the primary surfaces
2. **Always use `pty=true` for interactive launches** — `codex` is an interactive terminal app
3. **Use `codex exec --yolo` for one-shots** — it exits cleanly for non-interactive jobs
4. **For long autonomous work, prefer the tmux supervisor stack** — better than ad hoc multiple background Codex jobs
5. **Git repo strongly preferred** — unless you intentionally use `--skip-git-repo-check`
