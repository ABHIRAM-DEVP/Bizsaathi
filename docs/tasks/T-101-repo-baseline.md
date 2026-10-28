# TASK_ID: T-101
TITLE: Repository and environment baseline
PHASE: 1 (M0)
PRIORITY: MVP
OBJECTIVE: Record the real repo structure and installed tools and get `just guards` green.
BACKGROUND: AGENTS.md, docs/12-assumptions-risks-deps.md, justfile
FILES TO CREATE OR MODIFY: docs/12-assumptions-risks-deps.md (tool versions), .gitignore if needed
IMPLEMENTATION STEPS:
  1. Run `git status`, list the tree, check `python --version`, `node -v`, `uv --version`, `pnpm -v`, `docker --version`, `just --version`. Record results, mark missing tools.
  2. Run `just guards`. Fix only real findings.
  3. Update dependency register statuses with actual versions.
DEPENDS ON: none
ACCEPTANCE CRITERIA:
  - Given the repo, When `just guards` runs, Then exit 0 and output is quoted.
  - Given a missing tool, When recorded, Then it is listed as missing, not assumed present.
TEST COMMAND: just guards
SECURITY CONSIDERATIONS: .env must not be tracked.
OUT OF SCOPE: any application code
DEFINITION OF DONE: tool versions recorded with real command output
