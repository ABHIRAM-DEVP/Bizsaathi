# Single source of truth for commands (agents, humans, CI).
# Tools needed: uv, npm, docker, python3. Recipes assume backend and frontend exist.
set shell := ["bash", "-euo", "pipefail", "-c"]

api_url := env_var_or_default("API_URL", "http://localhost:8000")

default:
    @just --list

up:
    docker compose up -d postgres redis minio

down:
    docker compose down

dev-api:
    cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-web:
    cd frontend && npm run dev

# Repo-level guards that work before any app code exists.
guards:
    bash scripts/secret_scan.sh
    python -X utf8 scripts/eval_validate.py
    python -X utf8 scripts/check_docs.py

# Seconds-fast loop. Run constantly.
check-fast: guards
    cd backend && uv run ruff check . && uv run mypy . && uv run pytest tests/unit -x -q
    cd frontend && npm run lint && npm run build

# Full gate before reporting done.
check: check-fast
    cd backend && uv run pytest tests/integration -x -q
    just contract-check
    just eval-mock
    cd frontend && npm run build

export-openapi:
    cd backend && uv run python -m app.export_openapi > ../contracts/openapi.json

contract-check:
    cd backend && uv run python -m app.export_openapi | diff -u ../contracts/openapi.json -

migrate:
    cd backend && uv run alembic upgrade head

new-migration msg:
    cd backend && uv run alembic revision --autogenerate -m "{{msg}}"

# Evals with mocked models: free and deterministic. NOT a quality claim.
eval-mock:
    cd backend && uv run python -m app.evals.run --mode mock --split dev

# Evals against configured API (only if approved and configured via .env)
eval-live split="heldout":
    cd backend && uv run python -m app.evals.run --mode live --split {{split}}

# Verify model adapter access using .env configuration.
meta-smoke:
    cd backend && uv run python -m app.ai.smoke

e2e:
    cd frontend && npm run test

smoke:
    API_URL={{api_url}} bash scripts/api_smoke.sh
