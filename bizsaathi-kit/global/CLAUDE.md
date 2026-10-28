# Global rules (every project)

## Completion means evidence
- Never say "done", "fixed" or "working" unless you ran the project's check command in this turn and can quote its output.
- If you could not run it, write "NOT VERIFIED" and say why. Do not guess that it works.
- End every task with this report:
  1. Completed: exact changes made
  2. Files changed: full paths
  3. Verification: commands actually run and real results (pass/fail + key output line)
  4. Not completed: failures and blockers
  5. Assumptions: new or unresolved
  6. Risks: security, correctness, scope
  7. Next task: the single next recommended task

## Working style
- Read the task file (docs/tasks/<slug>.md) and the docs it names before writing code.
- If something is ambiguous, ask ONE question. Otherwise pick the simplest option and state the assumption.
- Tests first for new behavior and bug fixes: write the failing test, show it fail, then implement.
- Smallest diff that satisfies the task. No unrelated refactors, renames, formatting sweeps or new dependencies unless the task says so.
- Copy the repo's existing patterns. Find a similar file before inventing structure.
- Do not invent APIs. If unsure that a function or option exists, check the installed package or its docs.

## Two strikes, then stop
- The same check fails twice: stop retrying. Run /debug-fast, state the root cause with evidence, change approach.
- Three failed attempts: write docs/tasks/<slug>.stuck.md (what you tried, exact errors, hypotheses) and stop.
- When code gets polluted by repeated patching, revert to the last green commit and rewrite the task instead of patching more.

## Style
- No emojis in code, comments, commit messages or docs. The only exception is the API smoke-test reporter output.
- Conventional commits (feat:, fix:, test:, docs:, chore:), one concern per commit.
- Never print, log or commit secrets. Do not read .env files.
