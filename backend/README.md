# Backend

The backend is the application's Python API and workflow runtime. It accepts owner and public-store requests, applies authentication and tenant scope, reads and writes domain records, and coordinates asynchronous work.

## Architecture

HTTP routes delegate to services; services use repositories and SQLAlchemy models. LangGraph workflows coordinate typed agent state and approval interrupts. AI calls go through one adapter. Database-backed facts and deterministic policy checks remain authoritative; model output is a proposal, not a confirmed record.

## Contents

- `app/routers/`: HTTP endpoints.
- `app/services/`: business operations, policy, execution, and response generation.
- `app/repositories/`, `app/models/`, `app/schemas/`: persistence and typed domain/API data.
- `app/agents/`, `app/ai/`: workflow graph and model adapters.
- `app/core/`: configuration, tenancy, errors, formats, and logging.
- `alembic/`: database migration history.
- `tests/`: unit and integration coverage.

## Stack and checks

Python 3.12; FastAPI; Pydantic v2; SQLAlchemy 2; Alembic; PostgreSQL; LangGraph; pytest; Ruff; mypy. From this directory:

```powershell
uv run pytest tests/unit -x -q
uv run ruff check .
uv run mypy .
```

## Metrics and impact

The repository defines safety/evaluation targets in [../evals/thresholds.yaml](../evals/thresholds.yaml); it does not provide production latency, availability, cost, or business-impact measurements. The backend's intended impact is to provide a single validated boundary for business data and AI-assisted workflows.
