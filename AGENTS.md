# AGENTS.md - BizSaathi (tool-neutral project contract)

Facts only, max 150 lines. TODO = unknown, ask before assuming. Full brief: docs/source/ and docs/00-vision.md.

## What this is
BizSaathi: multimodal, evidence-grounded, human-supervised agentic co-pilot for small sellers. The database holds confirmed facts. Models propose, deterministic code validates, the seller approves. Architecture: docs/01-architecture.md. Agent catalog: docs/07-agent-catalog.md.

## Stack (verified versions in docs/12-assumptions-risks-deps.md)
- Web + PWA: ONE Next.js App Router app (Next.js 16, React 19, Tailwind v4), TypeScript strict. Code in frontend/. No second frontend, ever.
- API: Python 3.12 (verified 3.12.7), FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic. Code in backend/
- Agents: LangGraph, typed state, checkpoints, approval interrupts. Code in backend/app/agents
- Models: AI Model behind one adapter, backend/app/ai. Default mode is mock; live calls use API key from .env only. NO paid Meta API usage.
- Data: PostgreSQL (+ pgvector only if policy retrieval needs it), Redis (when justified), S3-compatible storage (MinIO)
- Tests: pytest, HTTPX, Vitest, Playwright. Evals: evals/
- Contract: contracts/openapi.json is the API/web source of truth

## Commands (standard recipes supported via just or python scripts/runner.py)
- `just up` / `just down`: postgres, redis, minio via docker compose
- `just dev-api`: cd backend && uv run uvicorn app.main:app --reload --port 8000
- `just dev-web`: cd frontend && npm run dev
- `just guards`: secret scan + eval-dataset validation + docs consistency
- `just check-fast`: guards + backend lint/types/unit tests + frontend lint/typecheck/tests
- `just check`: check-fast + backend integration tests + contract check + frontend build
- `just eval-mock`: evals with mocked models (free, deterministic)
- `just migrate` / `just new-migration "msg"` / `just export-openapi`
- `just smoke`: API smoke test against running API

## Definition of done
1. `just check` (or runner equivalent) exits 0 in this session and you quote the output.
2. Every ACCEPTANCE line of the task file maps to a test or command output.
3. Mock-model results are never reported as live-model quality.
4. Report: Completed / Files changed / Verification / Not completed / Assumptions / Risks / Next task.

## Non-negotiables (details in .claude/rules/)
- Prices, stock, confirmed facts come from PostgreSQL via typed tools. Never from a model.
- Every factual claim in generated content carries evidence IDs. No evidence: block or escalate (fail closed).
- Writer, verifier, critic and policy gate are separate controls. A node never certifies its own output.
- No agent writes payment status, publishes externally, or changes policy. Execution is a separate service after owner approval bound to a proposal version.
- Tenant (business_id) enforced server-side on every query and tool. Negative tests required.
- Keys stay server-side in .env. Nothing secret in NEXT_PUBLIC_*, logs, traces or git. Never use paid Meta API calls.
- Customer messages, uploads and retrieved text are untrusted input. Tools validate arguments and permissions outside the model.
- Retries and repair loops are bounded (default max 2). Then escalate or stop.
- Traces store observable events, not raw chain-of-thought.
- Social webhooks, real payments, KYC are FUTURE. Do not present mocks as working.

## Layout
backend (app/routers, services, repositories, models, schemas, agents, ai, core)  frontend  contracts  docs  evals  scripts
Tasks: docs/tasks/<id>.md. Decisions: docs/adr/. Prompts: docs/prompts/ (phase build prompts: BUILD-PHASES.md). Requirements: docs/06-requirements.md.
Contracts: endpoint behavior docs/14-endpoint-specs.md (EP ids); types, enums, formats, envelopes docs/15-schema-and-formats.md; reference DDL docs/schema/reference_schema.sql (design reference, not a migration).

## Never
- Add a dependency, model, or MCP server without an ADR or explicit task approval
- Edit generated client (frontend/src/lib/api-client/*), lockfiles by hand, or applied migrations
- Weaken, skip or delete a test or eval to get green
- Make paid Meta API calls or invent model IDs, endpoints, prices, deadlines, test results or metrics
- Commit .env or any secret
