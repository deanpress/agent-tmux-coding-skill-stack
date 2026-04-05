# Optional OMX Extension

This repository is vanilla-Codex-first by default.

That means the core tmux orchestration path uses:

```bash
export TERM=xterm-256color && codex --yolo
```

However, if your environment already uses `oh-my-codex` (OMX), you can layer it on top as an optional extension.

## When to use OMX

Use OMX if you specifically want:
- OMX prompt/routing surfaces
- `$plan`, `$architect`, `$ralph`, `$team`
- an OMX-native Codex workflow already adopted by your team

Do not require OMX if your main priority is:
- portability
- lowest-friction setup
- easiest third-party adoption
- minimal moving parts

## Recommended policy

- Core stack: vanilla Codex + tmux supervisor
- Optional extension: OMX for environments that already want it

## Optional launch swap

If OMX is installed and configured, you may change the Codex interactive launch command from:

```bash
export TERM=xterm-256color && codex --yolo
```

to:

```bash
export TERM=xterm-256color && omx --madmax --high
```

You should also restore any readiness handling needed for OMX-specific startup prompts.

## Included optional skill

This repository includes the `skills/autonomous-ai-agents/oh-my-codex` skill as an optional companion.
It is not required by the default stack and should be treated as a user-selectable extension.
The default installer skips it; opt in with:

```bash
python3 scripts/install_stack.py --dest /home/USER/.hermes/skills --include-skill oh-my-codex
```

## Suggested agent instruction

"Install the core tmux coding stack in vanilla Codex mode. If OMX is already present or explicitly desired, also install the optional `oh-my-codex` skill and document how to swap the Codex launch command to `omx --madmax --high`. Do not make OMX mandatory."
