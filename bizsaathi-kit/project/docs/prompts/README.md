# Prompt runbook

Prompts are files. Use docs/prompts/PROMPTS-1-8.md. One prompt per session; `/clear` between them. Review the output (`git diff`, `just check-fast`) before the next.

| Order | Prompt | When | Model advice |
|---|---|---|---|
| 1 | Reconcile kit with repo | once, today | strongest available (sets rules for everything) |
| 9 | Verify Meta API access | right after 1, before any model code | strongest; needs your credentials and approval for the live call |
| 2 | Verify stack vs official docs | after 1 and 9 | strongest |
| 3 | Skills/subagents/MCP review | after 2 | strongest |
| 4 | Review and improve docs 00-03 + PHASES | after 2 | strongest, then you edit by hand |
| 5 | Review/extend task files | after 4 | cheap model fine, you review |
| 10 | Implement one task (repeat) | each task | cheap or mid model is fine: the task file and checks carry the quality |
| 6 | Testing strategy + commands | before Phase 3 | mid model |
| 11 | A/B/C evaluation | Phase 5 | strongest for analysis; live run costs credits |
| 7 | Audit the setup | weekly | mid model |
| 8 | Capture lessons | when a mistake repeats | cheap model |

Build prompts for each phase (1.1 to 5.5, with phase gates) are in docs/prompts/BUILD-PHASES.md. They cite endpoint ids from docs/14 and formats from docs/15. Run them in order after Prompts 1, 9 and 2.

Never run all prompts in one go. If a prompt needs a fact that can only come from you (deadline, credits, team size, official docs a tool cannot fetch), it must stop and ask.
