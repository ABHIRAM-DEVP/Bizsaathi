# BizSaathi

BizSaathi is a seller co-pilot for managing product information, customer conversations, and content drafts. It is designed so that database records remain the source of confirmed facts: AI can propose work, deterministic controls validate it, and owner approval gates consequential actions.

## System architecture

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

## Main folders

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

## Technology

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

## Metrics and impact

Evaluation thresholds are defined in [evals/thresholds.yaml](evals/thresholds.yaml). Current hard safety targets include `unauthorized_actions_blocked: 1.0`, `cross_tenant_leaks: 0`, and `duplicate_side_effects: 0`. Several quality, latency, and cost thresholds remain `TODO`; they are not measured results.

No measured production business impact, user outcomes, or service-level performance is recorded here. The intended value is reduced manual work for product intake and content preparation, with safer customer replies and owner-controlled decisions; these outcomes require real-world measurement before being claimed as achieved.
