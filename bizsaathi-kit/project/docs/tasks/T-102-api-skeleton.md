# TASK_ID: T-102
TITLE: FastAPI skeleton with health, errors, config, tenancy context
PHASE: 1
PRIORITY: MVP
OBJECTIVE: A running API with /v1/health, problem-JSON errors, settings from env and an authenticated tenant context dependency.
BACKGROUND: docs/01-architecture.md, docs/08-api-spec.md, .claude/rules/api.md, .claude/rules/security.md
FILES TO CREATE OR MODIFY: apps/api/pyproject.toml, apps/api/app/main.py, app/core/{config,errors,tenancy}.py, tests/unit/test_health.py, app/export_openapi.py
IMPLEMENTATION STEPS:
  1. Tests first: health 200; unknown route returns problem JSON with request_id; config refuses to start without required vars in non-dev.
  2. Implement. Dev auth stub is allowed only when ENV=dev and must be labelled.
  3. Add `export_openapi` module and generate contracts/openapi.json.
DEPENDS ON: T-101
ACCEPTANCE CRITERIA:
  - Given the running API, When GET /v1/health, Then 200.
  - Given an unknown path, When requested, Then problem JSON with request_id and the right status.
  - Given no business context, When a tenant-scoped dependency is used, Then 401.
TEST COMMAND: just check-fast; just contract-check
SECURITY CONSIDERATIONS: no secrets in logs; dev stub disabled outside dev.
OUT OF SCOPE: real OTP, product routes
DEFINITION OF DONE: just check output quoted
