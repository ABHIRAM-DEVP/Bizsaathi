# backend

- Run here: `uv run pytest tests/unit -x -q`, `uv run ruff check .`, `uv run mypy .`
- Layout: app/routers, app/services, app/repositories, app/models, app/schemas, app/agents (LangGraph), app/ai (Model adapter), app/core (config, db, errors, auth, tenancy), tests/unit, tests/integration
- Router -> service -> repository. Authorization and tenant scoping live in services and repositories, not routers.
- Photo and voice endpoints create async jobs and return a job id immediately (see docs/08-api-spec.md).
- Every endpoint: response_model, status codes, tags, error shape from docs/01-architecture.md.
- After any API change: `just export-openapi` (or runner), regenerate the web client, confirm the contract diff is intended.
- Config only via app/core/config.py (pydantic-settings). Model provider settings are config, credentials are env. No paid API calls.
