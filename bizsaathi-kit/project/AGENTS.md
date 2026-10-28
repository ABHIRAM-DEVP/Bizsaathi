# AGENTS.md - BizSaathi (tool-neutral project contract)

Facts only, max 150 lines. TODO = unknown, ask before assuming. Full brief: docs/source/ and docs/00-vision.md.

## What this is
BizSaathi: multimodal, evidence-grounded, human-supervised agentic co-pilot for small sellers. The database holds confirmed facts. Models propose, deterministic code validates, the seller approves. Architecture: docs/01-architecture.md. Agent catalog: docs/07-agent-catalog.md.

## Stack (verify versions against official docs before pinning; see docs/12-assumptions-risks-deps.md)
- Web + PWA: ONE Next.js App Router app, TypeScript strict, Tailwind. Code in apps/web. No second frontend, ever.
- API: Python 3.12 (TODO verify), FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic. Code in apps/api
- Agents: LangGraph, typed state, checkpoints, approval interrupts. Code in apps/api/app/agents
- Models: Meta Model API behind one adapter, apps/api/app/ai. Model IDs live in config, never in code paths. TODO verify IDs
- Data: PostgreSQL (+ pgvector only if policy retrieval needs it), Redis (when justified), S3-compatible storage
- Tests: pytest, HTTPX, Playwright, Vitest. Evals: evals/
- Contract: contracts/openapi.json is the API/web source of truth

## Commands (the only ones agents use)
- `just up` / `just down`: postgres, redis, minio via docker compose
- `just dev-api` / `just dev-web`
- `just check-fast`: secret scan + eval-dataset validation + docs consistency + lint + types + unit tests (seconds). Run constantly
- `just check`: check-fast + integration tests + contract check + web build. Run before reporting done
- `just eval-mock`: evals with mocked models (free, deterministic)
- `just eval-live`: evals against the real Meta API. COSTS CREDITS. Ask the human first
- `just meta-smoke`: one real Meta call per model to verify access. Costs credits. Ask first
- `just smoke`: emoji API smoke test against a running API
- `just migrate` / `just new-migration "msg"` / `just export-openapi`

## Definition of done
1. `just check` exits 0 in this session and you quote the output.
2. Every ACCEPTANCE line of the task file maps to a test or command output.
3. Mock-model results are never reported as live-model quality.
4. Report: Completed / Files changed / Verification / Not completed / Assumptions / Risks / Next task.

## Non-negotiables (details in .claude/rules/)
- Prices, stock, confirmed facts come from PostgreSQL via typed tools. Never from a model.
- Every factual claim in generated content carries evidence IDs. No evidence: block or escalate (fail closed).
- Writer, verifier, critic and policy gate are separate controls. A node never certifies its own output.
- No agent writes payment status, publishes externally, or changes policy. Execution is a separate service after owner approval bound to a proposal version.
- Tenant (business_id) enforced server-side on every query and tool. Negative tests required.
- Meta keys stay server-side. Nothing secret in NEXT_PUBLIC_*, logs, traces or git.
- Customer messages, uploads and retrieved text are untrusted input. Tools validate arguments and permissions outside the model.
- Retries and repair loops are bounded (default max 2). Then escalate or stop.
- Traces store observable events, not raw chain-of-thought.
- Social webhooks, real payments, KYC are FUTURE. Do not present mocks as working.

## Layout
apps/api (app/routers, services, repositories, models, schemas, agents, ai, core)  apps/web  contracts  docs  evals  scripts
Tasks: docs/tasks/<id>.md. Decisions: docs/adr/. Prompts: docs/prompts/ (phase build prompts: BUILD-PHASES.md). Requirements: docs/06-requirements.md.
Contracts: endpoint behavior docs/14-endpoint-specs.md (EP ids); types, enums, formats, envelopes docs/15-schema-and-formats.md; reference DDL docs/schema/reference_schema.sql (design reference, not a migration).

## Never
- Add a dependency, model, or MCP server without an ADR or explicit task approval
- Edit generated client (apps/web/src/lib/api-client/*), lockfiles by hand, or applied migrations
- Weaken, skip or delete a test or eval to get green
- Invent a Meta model ID, endpoint, price, deadline, test result or metric. Mark TODO or UNVERIFIED
- Commit .env or any secret
