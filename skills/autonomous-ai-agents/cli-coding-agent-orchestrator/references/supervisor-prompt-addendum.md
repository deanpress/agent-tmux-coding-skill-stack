# Supervisor prompt addendum

When using the automated tmux supervisor, add these instructions to the coding-agent prompt:

1. Print phase markers on their own line when phases change:
- `<< PHASE: INSPECT >>`
- `<< PHASE: IMPLEMENT >>`
- `<< PHASE: VALIDATE >>`

2. When the main work is complete and ready for review, print:
- `<< TASK COMPLETE >>`

3. After review fixes are fully complete and validation has been rerun, print:
- `<< REVIEW FIXES COMPLETE >>`

4. Do not stop after partial progress. Continue autonomously until the original objective is complete.

5. If the supervisor requires a final git commit, create it and then print:
- `<< COMMIT COMPLETE >>`
  Only print this after the new commit exists.

These markers are used by the supervisor to automate state tracking, review triggering, and fix-loop completion.
