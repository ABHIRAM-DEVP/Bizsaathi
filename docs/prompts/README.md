# Prompt Runbook

> A guided sequence for building, reviewing, and validating BizSaathi.

> [Back to BizSaathi overview](../../README.md)

Run one prompt per session. Clear the session between prompts, then review the resulting diff and checks before continuing.

## Recommended sequence

| Step | Prompt | When to run | Guidance |
|---:|---|---|---|
| 1 | Reconcile kit with repository | Before implementation | Establish project-specific rules |
| 9 | Verify model API access | Before model integration | Requires credentials and approval for a live call |
| 2 | Verify stack against official docs | After prompts 1 and 9 | Confirm versions and supported APIs |
| 3 | Review skills, agents, and MCP | After prompt 2 | Review development tooling |
| 4 | Review core docs and phases | After prompt 2 | Review the output before adopting it |
| 5 | Review and extend task files | After prompt 4 | Keep tasks bounded and testable |
| 10 | Implement one task | For each task | Follow its acceptance criteria and checks |
| 6 | Review testing strategy and commands | Before Phase 3 | Confirm validation coverage |
| 11 | Run the A/B/C evaluation | Phase 5 | Live evaluations may incur provider costs |
| 7 | Audit the setup | Weekly | Recheck project configuration |
| 8 | Capture recurring lessons | When a mistake repeats | Update instructions based on evidence |

## Build-phase prompts

Detailed prompts for Phases 1.1–5.5, including phase gates, are in [BUILD-PHASES.md](BUILD-PHASES.md). They reference endpoint IDs in `docs/14-endpoint-specs.md` and formats in `docs/15-schema-and-formats.md`. Run them in sequence after prompts 1, 9, and 2.

> **Important:** Do not run every prompt at once. If required information is unavailable—such as a deadline, credits, team size, or official documentation—stop and ask rather than guessing.
