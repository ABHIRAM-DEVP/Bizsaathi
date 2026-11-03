# Backend application

`app/` contains the FastAPI application modules. The main flow is router → service → repository/model, with shared settings and controls in `core/`. Agent workflows are invoked by services or job handling rather than owning database truth.

## Modules

| Folder | Responsibility |
|---|---|
| `agents/` | Typed LangGraph state, workflow construction, nodes, and tools |
| `ai/` | Shared model interface and mock/live adapters |
| `core/` | Configuration, tenancy, errors, formats, and structured logging |
| `evals/` | Backend evaluation runner integration |
| `models/` and `repositories/` | SQLAlchemy records and data access |
| `routers/` and `schemas/` | HTTP endpoints and Pydantic request/response types |
| `services/` | Domain operations, policy checks, and execution boundaries |

## Metrics and value

No per-module performance or business metrics are recorded. These modules create value by separating transport, business rules, persistence, and AI proposals so they can be independently validated and tested.
