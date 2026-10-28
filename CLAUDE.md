@AGENTS.md

## Claude Code workflow for BizSaathi
- One task per session. Start from a task file in docs/tasks/. No task file: run `/spec-task <idea>` first.
- Before writing code, read the task, its DEPENDS ON tasks and the docs it names. Inspect the repo before editing; preserve unrelated changes.
- Tests first. Show the failing test, then implement, then `just check-fast` (or `python scripts/runner.py check-fast`), then `just check`.
- Same failure twice: `/debug-fast` (or the `debugger` subagent). Three failures: write docs/tasks/<id>.stuck.md and stop.
- Before saying done: `/verify-done`.
- Never make paid Meta API calls. Live calls use `.env` keys only when explicitly requested.
- After implementation, run the `reviewer` subagent; for anything touching auth, tenants, uploads, prompts, tools or payments also run `security-reviewer`.
- Specialized subagents: `implementer` (build from a task file), `security-reviewer`, `eval-analyst` (read eval output, never edits code).
- Folder files load on demand: backend/CLAUDE.md, backend/app/agents/CLAUDE.md, frontend/CLAUDE.md.
- End each task with the final report format in AGENTS.md. Compact keeping: task id, failing command, changed files, open assumptions.
