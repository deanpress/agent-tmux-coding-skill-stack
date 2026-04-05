# CLI coding agent prompt template

Use this structure when launching Codex, Gemini CLI, or Claude Code.

## Required fields
- Objective
- Repo/workdir
- Constraints
- Relevant files/modules
- Validation required
- Single-phase or multi-phase
- Completion criteria
- Instruction to continue autonomously until complete

## Template

You are working in: `<workdir>`

Objective:
`<goal>`

Important context:
- `<repo/project facts>`
- `<user complaint or target outcome>`
- `<constraints / do-not-touch areas>`

Execution mode:
- This is a `<single-phase|multi-phase>` job.
- If multi-phase, use phases:
  1. inspect/plan
  2. implement
  3. validate
  4. review/fix

Validation required before stopping:
- `<tests/build/typecheck/etc>`

Completion criteria:
- `<what done actually means>`
- `<whether a final git commit is required>`
- `<what evidence to report if commit-required work finishes with remaining worktree changes>`

Autonomy instruction:
Continue autonomously until the original objective is fully complete. Do not stop after partial progress. If you become idle after a summary, continue to the next necessary step.
