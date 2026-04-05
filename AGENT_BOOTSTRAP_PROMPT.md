Use this repository as the source of truth for a tmux-based coding orchestration skill stack.

Tasks:
1. Run `python3 scripts/bootstrap_doctor.py --dest ~/.hermes/skills` first and report any missing prerequisites.
2. Install the core stack with `python3 scripts/install_stack.py --dest ~/.hermes/skills`. If OMX is explicitly requested or already standard in the environment, install it with `--include-skill oh-my-codex` and keep it documented as optional.
3. Keep the bundled helper scripts and prompt templates in the same relative locations used by the skills.
4. Ensure the default Codex path uses vanilla `codex --yolo` for interactive tmux-supervised runs.
5. For substantial coding tasks, use the Codex tmux supervisor/job-manager flow rather than a one-shot `codex exec`.
6. If the user wants the full implement -> review -> fix -> commit workflow, launch the supervised job with the equivalent of `--substantial-job --require-commit`.
7. Verify the supervisor, check-in, resume, and Codex initialization docs are internally consistent.
8. Do not introduce any credentials, tokens, auth files, or machine-specific runtime state.
9. Report what was installed, which workflow you will use for substantial jobs, and any machine-specific prerequisites still needed.
