# BizSaathi

> **Evidence-grounded AI co-pilot for small sellers**
>
> AI proposes. Deterministic controls validate. Sellers approve.

BizSaathi is a seller co-pilot for managing product information, customer conversations, and content drafts. It is designed so that database records remain the source of confirmed facts: AI can propose work, deterministic controls validate it, and owner approval gates consequential actions.

**Explore:** [Architecture](docs/01-architecture.md) · [Backend](backend/README.md) · [Frontend](frontend/README.md) · [API contract](contracts/README.md) · [Evaluations](evals/README.md) · [Verification report](#verification-report)

---

## Architecture

```text
Seller PWA / public store chat
             |
        Next.js web app
             |
     FastAPI modular API
       /       |       \
 PostgreSQL  Redis   S3-compatible media
       \       |       /
     LangGraph jobs and workflows
             |
      Model adapter (mock/live)
```

The backend is a modular monolith with asynchronous jobs. Agent workflows use typed state and bounded repair; fact retrieval is tenant-scoped; evidence, policy checks, and owner approval are separate controls. External side effects belong to the execution service after approval. See [docs/01-architecture.md](docs/01-architecture.md) for the authoritative diagrams and [docs/00-vision.md](docs/00-vision.md) for product intent.

## Explore the repository

| Folder | Purpose |
|---|---|
| [backend/](backend/README.md) | FastAPI API, domain services, persistence, and agent workflows |
| [frontend/](frontend/README.md) | The single Next.js owner and customer web/PWA app |
| [contracts/](contracts/README.md) | OpenAPI contract shared by API and web |
| [docs/](docs/README.md) | Architecture, requirements, decisions, tasks, and operational guidance |
| [evals/](evals/README.md) | Synthetic evaluation cases, thresholds, and reports |
| [scripts/](scripts/README.md) | Cross-platform checks and repository utilities |
| [.claude/](.claude/README.md) | Repository-scoped agent instructions, hooks, and skills |
| [bizsaathi-kit/](bizsaathi-kit/README.md) | Reusable agent-workflow setup kit; not application runtime |
| [reference-ui/](reference-ui/README.md) | Static visual design references; not production UI |

## Technology stack

- Web/PWA: Next.js App Router, React, TypeScript, Tailwind CSS.
- API and agents: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, LangGraph.
- Data and local services: PostgreSQL, Redis, and S3-compatible storage as described in the architecture and Compose configuration.
- AI: one backend adapter with mock and environment-configured live implementations.
- Tests and checks: pytest, ESLint, Python lint/type checks, OpenAPI and documentation checks, and evaluation scripts.

See [docs/12-assumptions-risks-deps.md](docs/12-assumptions-risks-deps.md) for verified versions and unresolved assumptions. Do not treat a configured option as proof that an external service is deployed or live.

## Run and verify

Use the repository's [justfile](justfile) or the cross-platform runner:

```powershell
python scripts/runner.py check-fast
python scripts/runner.py check
```

Local services and environment setup are described in [STARTUP_GUIDE.md](STARTUP_GUIDE.md). Keep credentials in local environment files; never commit them.

## Product metrics and impact

Evaluation thresholds are defined in [evals/thresholds.yaml](evals/thresholds.yaml). Current hard safety targets include `unauthorized_actions_blocked: 1.0`, `cross_tenant_leaks: 0`, and `duplicate_side_effects: 0`. Several quality, latency, and cost thresholds remain `TODO`; they are not measured results.

No measured production business impact, user outcomes, or service-level performance is recorded here. The intended value is reduced manual work for product intake and content preparation, with safer customer replies and owner-controlled decisions; these outcomes require real-world measurement before being claimed as achieved.

## Verification report

Run on 2026-11-03 against the local working tree. This report records actual command output; it is not a production certification.

### Results

| Area | Result |
|---|---|
| Repository guards | **Pass** — secret scan clean; evaluation dataset valid (16 cases); docs consistent (69 API paths cross-checked, 79 endpoint IDs, 32 reference-schema tables structurally checked). |
| Backend unit tests | **221 passed, 9 failed**, 4 warnings, 143.87 s (`backend/`, `uv run pytest tests/unit -q`; 28 test files). Eight failures are test doubles that do not implement the now-required `ModelClient.analyze_image` method. One public-chat test attempted to connect to an unavailable PostgreSQL service. |
| Backend integration tests | **1 passed, 1 failed, 9 skipped**, 8.24 s (`backend/`, `uv run pytest tests/integration -q`). The failure is a PostgreSQL connection timeout; database-dependent tests were skipped because the local database was unavailable. |
| Backend Ruff | **Fail** — 7 findings: five import-order violations, one `zip()` without `strict=`, and one overlong line. |
| Backend mypy | **Fail** — 7 type errors in 3 files: `app/ai/mock.py` (3), `app/services/public_rate_limits.py` (1), and `tests/unit/test_customer_replies.py` (3). |
| Frontend ESLint | **Pass** — `npm run lint`. |
| Frontend production build | **Pass** — `npm run build`; TypeScript completed and Next.js generated 18 static pages. |
| OpenAPI contract | **Pass** — generated backend OpenAPI matched `contracts/openapi.json` byte-for-byte; the contract contains 48 paths and 51 HTTP operations. |
| Mock evaluations | **Pass, plumbing only** — dev 12/12 and held-out 4/4. Reports: [dev](evals/reports/mock-dev.json) and [held-out](evals/reports/mock-heldout.json). These use deterministic mock decisions, not a live model, and do not establish model quality. |
| End-to-end tests | **Not runnable** — `just e2e` fails because `frontend/package.json` has no `test` script. No frontend test files or E2E runner are configured in that package. |

The normal runner's fast check stops at the first unit-test failure. The full unit suite, lint/type checks, integration suite, build, contract comparison, and both mock-evaluation splits were therefore run separately to collect results. The integration environment was not provisioned with a reachable local PostgreSQL service.

**Log handling:** A PostgreSQL connection failure traceback included connection parameters from the local environment. Do not publish unredacted raw test logs. If that local password is a real or reused credential, rotate it and ensure database connection details are redacted from logs.

### Technical inventory and local versions

| Metric | Observed value |
|---|---:|
| Logical workflow nodes in the agent catalog | 15 |
| OpenAPI paths / HTTP operations | 48 / 51 |
| Tables in the reference SQL schema | 32 |
| Synthetic evaluation cases | 16 (12 dev, 4 held-out) |
| Local Python / Node.js / npm | 3.12.10 / 24.22.1 / 11.6.4 |
| Local uv / Docker / just | 0.13.6 / 29.9.2 / 1.59.0 |
| Backend FastAPI / Pydantic / SQLAlchemy / Alembic / LangGraph | 0.162.0 / 2.14.1 / 2.1.6 / 1.20.1 / 1.2.18 |
| Backend pytest / pytest-asyncio / Ruff / mypy | 9.2.0 / 1.4.1 / 0.17.3 / 2.4.0 |
| Frontend Next.js / React / Tailwind CSS / TypeScript / ESLint | 16.4.3 / 19.3.0 / 4.3.3 / 5.9.3 / 9.39.5 |
| Compose database/cache images | PostgreSQL-compatible `pgvector/pgvector:pg16`; Redis `7-alpine` (configured, not running during tests) |
| Test coverage percentage | Not collected |

These are local tool and repository inventory values, not production throughput, availability, or user-outcome measurements. Earlier version entries in [docs/12-assumptions-risks-deps.md](docs/12-assumptions-risks-deps.md) may reflect a different verification date.

The configured `just` recipes could not locate `uv` in their Bash environment in this session. Backend commands were run directly from PowerShell in `backend/`; the OpenAPI contract was then compared using the generated output directly.

### Savings and cost

**Time saved: not measured. Cost saved: not measured.** The repository has no before/after workflow timings, user study, production usage, model-token billing, or cost baseline from which to calculate savings.

The product is intended to assist with photo-based product entry, content drafts, and grounded customer replies, while preserving owner review. Those are potential areas of time savings, not demonstrated results. The two mock evaluation runs made no provider-model calls, so their provider API usage cost was **$0**; this is not a measured saving versus a live-model baseline and says nothing about total development or hosting costs.

To establish savings, measure matched manual and assisted workflows, including owner review and corrections: `time saved = manual median duration - assisted median duration`. For cost, compare labor plus model/API and allocated hosting/storage costs for the same completed workflow. No such baseline or matched production sample is currently recorded.

### Evaluation targets (not achieved-result claims)

Configured in `evals/thresholds.yaml`:

| Metric | Configured target | Measurement status |
|---|---:|---|
| Unauthorized actions blocked | 1.0 (100%) | Target only; mock fixture pass is not system-wide validation |
| Cross-tenant leaks | 0 | Target only; integration validation incomplete without PostgreSQL |
| Duplicate side effects | 0 | Target only; no production measurement |
| False approval rate | TODO | No baseline |
| Missed escalation rate | TODO | No baseline |
| Evidence coverage | TODO | No baseline |
| Claim verification precision / recall | TODO / TODO | No baseline |
| Field extraction accuracy | TODO | No live labelled measurement |
| Cross-modal mismatch accuracy | TODO | No live labelled measurement |
| p95 latency | TODO | No production workload measurement |
| Cost per workflow | TODO | No live usage/billing measurement |

**Overall status: not all checks pass.** The frontend lint/build, repository guards, OpenAPI comparison, and deterministic mock evaluation passed. Backend unit tests, integration tests, Ruff, and mypy have outstanding failures; database-backed verification and frontend E2E are incomplete.
