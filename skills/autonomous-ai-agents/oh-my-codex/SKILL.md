---
name: oh-my-codex
description: Use oh-my-codex (OMX) as the primary Codex CLI surface. Covers setup, direct OMX launches, omx exec, omx ralph, and omx team routing.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [omx, oh-my-codex, codex, tmux, team, ralph]
    related_skills: [codex, cli-coding-agent-orchestrator, tmux-cli-agent-supervisor]
---

# oh-my-codex (OMX)

Use this skill whenever the user wants Codex work done through OMX instead of raw `codex`.

## What OMX is

OMX is a workflow layer around Codex CLI.

Mental model:
- Codex = execution engine
- OMX = routing, prompts, skills, AGENTS overlays, persistence helpers, and team runtime

Prefer OMX as the default Codex surface on this machine.

## Install / health check

Expected setup:
- `npm install -g oh-my-codex`
- `omx setup --scope user --skill-target codex-home`
- `omx doctor`

Interactive default launch:
- `omx --madmax --high`

Global-install smoke checks:
- `omx --help`
- `omx doctor`
- `omx exec "Print the current working directory"`

Use the repo-specific build and `dist/hooks/__tests__/...` commands in this skill only when you are working inside an `oh-my-codex` source checkout. See:
- `references/source-checkout-validation.md`

## Primary surfaces and when to use them

### 1) `omx --madmax --high`
Use when:
- you want a normal interactive Codex session, but with OMX loaded
- you want OMX skills like `$plan`, `$ralph`, `$team`, `$architect`
- you are launching Codex in tmux for autonomous work

Typical tmux launch:
- `export TERM=xterm-256color && omx --madmax --high`

### 2) `omx exec "..."`
Use when:
- you want a one-shot non-interactive task
- you want to run Codex from Hermes terminal/process tooling
- you want OMX overlays injected without an interactive session

Prefer this over raw `codex exec` unless you intentionally want to bypass OMX.

### 3) `omx ralph "..."`
Use when:
- the task must keep going until genuinely complete
- you want a persistent single-owner loop
- persistence matters more than parallelism

### 4) `omx team N:executor "..."`
Use when:
- the task is large enough for coordinated parallel work
- you want durable tmux workers, shared task state, and lifecycle commands
- you may want status/resume/shutdown controls later

Simple rule:
- single thread, must finish -> `$ralph`
- multi-lane, durable parallel execution -> `$team`

## Recommended routing policy for Hermes

Default order:
1. For interactive Codex sessions, launch `omx --madmax --high`
2. For one-shot terminal jobs, use `omx exec`
3. For persistent single-owner completion work, use `omx ralph`
4. For durable tmux-based parallel work, use `omx team`

## Tmux integration guidance

When updating or using Codex tmux supervisor flows:
- launch Codex through OMX, not raw `codex`
- preferred launch command: `export TERM=xterm-256color && omx --madmax --high`
- still expect Codex trust prompt behavior underneath OMX in some repos
- keep readiness gating because Codex/MCP startup time still matters

## Operational cautions

- Do not default to `$team` for small tasks; it is heavier-weight than a direct OMX session.
- Do not use raw `codex` unless OMX is unavailable or there is a specific reason to bypass OMX.
- Keep using tmux supervision for unattended interactive runs; OMX improves the runtime surface, but supervision still matters.
- OMX setup installs a global Codex `notify` hook in `/home/devuser/.codex/config.toml`, so notify-hook code is active for this Codex home even in plain `codex` sessions, not just `omx` launches.
- OMX auto-nudge defaults to injecting `yes, proceed [OMX_TMUX_INJECT]` when it detects stall phrasing in tmux Codex panes.

For tmux routing, notify-hook, and auto-nudge hardening guidance inside an `oh-my-codex` source checkout, see:
- `references/tmux-routing-hardening.md`

## Desired outcome

Use OMX as the primary Codex interface, and choose the right surface:
- `omx --madmax --high` for normal interactive work
- `omx exec` for one-shot jobs
- `omx ralph` for persistence
- `omx team` for durable parallel execution
