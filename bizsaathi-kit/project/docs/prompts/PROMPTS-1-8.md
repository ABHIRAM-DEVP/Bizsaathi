# BizSaathi prompts 1-8 (your originals, kept intact) + 9-11 (added)

Use one prompt per session, `/clear` between them. Read the committed brief (docs/source/ and docs/00-vision.md) instead of pasting it. Final report format for every task is in AGENTS.md.

Kit state note: this kit already contains a first adaptation of the files Prompt 1 rewrites (AGENTS.md, justfile, rules, skills). Run Prompt 1 as a reconcile-against-reality pass: compare the kit with the actual repo, fix mismatches, run each recipe once. Prompts 2 to 8 still apply as written.

---
## Prompt 1 - Adapt the kit to BizSaathi
Read the brief and the repository's committed project brief. Read the agentic kit at `<KIT_PATH>` (README, global/, project/). First inspect the repository and report its actual structure, installed tools, conventions and Git status. Do not modify global kit files. Adapt only project-level configuration.

Required actions
1. Rewrite `AGENTS.md`: verified architecture and stack; exact setup/dev/lint/type-check/test/build commands; definition of done; security requirements and forbidden practices; concise architecture map; unknowns marked TODO; max 150 lines.
2. Rewrite the `justfile` so `check-fast` and `check` invoke real commands supported by the repository. `check-fast`: fast format, lint, type checks. `check`: full tests and production build. Run each recipe once. Report actual output and failures. Never claim success if a command was skipped or unavailable.
3. Replace `.claude/rules/*.md` with narrowly scoped rules for the actual frameworks and directories. Remove irrelevant rules only after inspecting their purpose.
4. Inspect the existing project skills. Rewrite or replace them only when they address repeated, project-specific work.
5. Keep `CLAUDE.md` minimal: `@AGENTS.md` plus necessary Claude-specific workflow lines.
6. Enforce the shared frontend architecture: one Next.js codebase for web and PWA; no duplicate frontend project.
7. Protect secrets. Never commit `.env`, put secrets in frontend variables, or expose Meta credentials to the browser.

Acceptance: every changed file listed; `just check-fast` and `just check` verified against the actual environment; unknown facts and unavailable tools listed; no global kit files modified; no application feature code implemented; all edits summarized with a diff. Stop and report blockers rather than inventing commands or configuration.

---
## Prompt 2 - Verify the stack against current official documentation
Read the brief, `AGENTS.md`, `.claude/rules/`, dependency manifests and code. Use current official documentation, not memory, to verify every version-sensitive technology and API.

Verify: Next.js App Router, metadata, routing, caching, production build; PWA manifest, service worker, installation, caching, offline; TypeScript and lint compatibility; FastAPI request handling and lifecycle; Pydantic validation and settings; LangGraph state, checkpointing, interrupts, human approval; PostgreSQL, SQLAlchemy, Alembic practices; Redis if present; Meta model identifiers, supported inputs, authentication, endpoint formats, rate limits, pricing; SAM 3.1 or other capabilities only when official docs confirm access; Docker and deployment configuration.

Output a table: `Technology | Assumption | Official documentation finding | Required action | Source URL`. For each discrepancy: cite the official doc, explain the practical effect, make the smallest justified correction to AGENTS.md, rules or dependency config. Do not upgrade or replace dependencies without checking compatibility. No broad application changes. If docs are unavailable or account-specific access cannot be verified, mark the item unverified. Record Meta findings in docs/12-assumptions-risks-deps.md.

---
## Prompt 3 - Skills, subagents and MCP servers
Inspect recurring workflows and the current agent configuration. Start with zero new skills, subagents and MCP servers beyond the kit. Recommend an addition only when it removes meaningful repeated work or enables a necessary capability.

For each proposal report: name and purpose; repeated task removed; expected frequency; context/token cost or qualitative overhead; security implications and permissions; install/config instructions; why an existing capability is insufficient.
Limits: max 5 skills, max 3 subagents, max 2 MCP servers (the kit already uses 5 project skills and 3 project subagents, so propose replacements, not additions, unless justified). Candidates: official docs lookup, read-only PostgreSQL, GitHub.
Approval workflow: present the list first; do not install or create until I approve; then write only the approved items; every skill has a `Use when...` description under 300 characters; subagents get the narrowest tools; never put keys in `.mcp.json`; run available config checks; run `/context` and report before/after token counts only if the environment exposes them. If not measurable, say so.

---
## Prompt 4 - Draft the documentation and diagrams
Read the brief, repository and verified stack findings. Do not implement application code. The kit ships drafts of these; review and improve them instead of starting over.

Files: docs/00-vision.md (problem, users, solution, principles, MVP vs future, measurable success metrics, limitations); docs/01-architecture.md (overview, context and component diagrams, sequence diagrams for product ingestion, content generation and customer queries, auth and tenant isolation, model adapter, workflow state/approval/retries/errors, deployment, observability); docs/02-data-model.md (ER diagram, entities, keys, constraints, indexes, tenant strategy, migration strategy, retention/privacy; MVP-justified entities only); docs/03-ui.md (web+PWA strategy, navigation, routes, desktop/mobile layouts, seller workflows, loading/empty/error/offline/permission-denied states, accessibility, PWA install and update; one Next.js app); docs/PHASES.md (phases, priorities, dependencies, acceptance criteria, milestone exits, risks, deferred work).
Rules: prefix unverified assumptions with `ASSUMPTION:` and end with questions to resolve each. Mermaid diagrams validated with `mmdc` if installed; otherwise state rendering was not verified. No application code.

---
## Prompt 5 - Convert the plan into task files
Read docs/PHASES.md and supporting docs. Generate task files for Phase 1 only (the kit seeds T-101 to T-106; review, fix, extend). Do not implement.
Template fields: TASK_ID, TITLE, PHASE, PRIORITY, OBJECTIVE, BACKGROUND, FILES TO CREATE OR MODIFY, IMPLEMENTATION STEPS, DEPENDS ON, ACCEPTANCE CRITERIA, TEST COMMAND, SECURITY CONSIDERATIONS, OUT OF SCOPE, DEFINITION OF DONE.
Constraints: one concern per task; about 5 files max; dependencies reference existing ids; Given/When/Then criteria; executable verification command; identify missing prerequisites rather than guessing; respect the shared Next.js web/PWA architecture; keep API credentials server-side; valid dependency order; no tasks for unapproved stretch features. End with execution order and blockers.

---
## Prompt 6 - Testing strategy
Read the brief, code, tasks and test config. Create or update docs/04-test-strategy.md (the kit ships a draft).
Categories: Frontend (TS and lint; component tests for critical states; Playwright for seller workflows; responsive and PWA install checks; offline and reconnection; accessibility). Backend (unit; API contract and validation; DB integration; authorization and tenant isolation; upload validation; retry, timeout, failure paths). Agent workflows (state schema; deterministic tools; routing; approval interrupts; retry limits and repair termination; evidence and claim verification; prompt injection and untrusted input; protection against unauthorized payment or publishing). AI evaluation: labelled dataset (photos with uncertain attributes, conflicting details, unsupported claims, ambiguous customer questions, wrong stock/price assumptions, injections, escalation requests, unauthorized-action attempts); compare the simplest viable workflow with the structured-tool and verification workflow; metrics (field correctness, evidence coverage, claim-verification false positives/negatives, escalation rate, unauthorized-action prevention, latency and cost per workflow). Set thresholds before running; if unjustifiable, TODO and baseline first.
Execution: add commands to the justfile; run applicable ones; report actual pass/fail counts and environment limits; keep mock and live Meta tests separate; never claim live-model quality from mocks; document how to run evals locally and in CI.

---
## Prompt 7 - Audit the agent setup
Inspect: AGENTS.md length and accuracy; CLAUDE.md duplication; conflicting or irrelevant rules; overlapping or non-triggering skills; subagents with unnecessary tools; unused or overprivileged MCP servers; failing hooks; stale commands and dependency instructions; secret and untrusted-content risks; docs contradicting implementation. Run `/context` and `/hooks` only if available.
Output a table `Item | Keep/Fix/Delete proposal | Evidence | Reason | Risk | Recommended change`, then verified defects, potential improvements, missing information, and commands actually executed with output. Do not delete files, uninstall plugins, remove MCP servers or change hooks until I approve. Apply only approved changes, show the diff, rerun checks.

---
## Prompt 8 - Capture lessons
Session lesson: `<WHAT FAILED, WHAT WORKED, OR WHAT CHANGED>`.
Decide where it belongs: `.claude/rules/` (recurring path-specific constraint), AGENTS.md (stable project-wide instruction), docs/05-troubleshooting.md (failure, diagnosis, recovery), a project skill only if repeated at least 3 times.
Procedure: reproduce or verify; inspect existing docs to avoid duplication; choose the smallest change; keep one-off incidents distinct from recurring rules; update only the relevant file; show the exact diff; run the relevant check; report evidence and uncertainty. Do not create skills, install tools or add broad rules for one isolated failure.

---
## Prompt 9 (added) - Verify Meta API access and record it
```
Goal: replace assumptions A-03 to A-07 in docs/12 with verified findings.
1. Read the official Meta Model API documentation (I will paste URLs or pages if your tools cannot reach them). Do not guess. If you cannot reach it, stop and say so.
2. Record: base URL, auth scheme, exact model ids for reasoning, image, transcribe, segmentation; image input format and limits; rate limits; pricing; whether OpenAI- or Anthropic-style client SDKs are supported. Each with source URL and date.
3. Update .env.example variable names only if the docs require different ones. Never write a key.
4. Ask me before running `just meta-smoke`. After approval run it once; record model id, date, latency, usage, or the exact failure.
5. Report using the AGENTS.md final report format. Mark anything unreachable as UNVERIFIED.
```

## Prompt 10 (added) - Implement one task
```
Use the implementer subagent on docs/tasks/<ID>.md. When it reports, run the reviewer subagent on the diff against the same file. If the task touches auth, tenants, tools, agents, uploads, public routes or orders, also run security-reviewer. Then /verify-done. Do not run live Meta calls without asking me.
```

## Prompt 11 (added) - Run the A/B/C evaluation
```
Read evals/README.md, evals/thresholds.yaml and .claude/rules/evals.md. Confirm thresholds are set (TODO means baseline run only, say so). Ask me before `just eval-live`. After approval run it on the heldout split once; do not tune anything on heldout. Then use the eval-analyst subagent on the report. Output A vs B vs C metrics, failure clusters, cases where C is worse, model ids, date, usage and cost. Never present mock numbers as quality.
```
