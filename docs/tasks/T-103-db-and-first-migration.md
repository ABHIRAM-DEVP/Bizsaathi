# TASK_ID: T-103
TITLE: PostgreSQL schema v1 and first migration (business, user, product, job, audit)
PHASE: 1
PRIORITY: MVP
OBJECTIVE: Core tables with business_id tenancy, applied by Alembic on real Postgres.
BACKGROUND: docs/02-data-model.md, .claude/rules/db-tenancy.md, /add-migration
FILES TO CREATE OR MODIFY: apps/api/app/models/*.py, apps/api/alembic/versions/<new>.py, tests/integration/test_tenancy.py, app/repositories/product.py
IMPLEMENTATION STEPS:
  1. `just up`. Tests first: tenant B cannot read/update/delete tenant A product.
  2. Models and migration; verify upgrade, downgrade -1, upgrade.
DEPENDS ON: T-102
ACCEPTANCE CRITERIA:
  - Given an empty database, When `just migrate`, Then schema created; downgrade -1 then upgrade succeeds.
  - Given tenant B, When reading tenant A's product id, Then not found.
  - Given an audit event write, When queried, Then it carries business_id and actor.
TEST COMMAND: just check
SECURITY CONSIDERATIONS: every repository method filters business_id.
OUT OF SCOPE: proposals, claims, orders (later tasks)
DEFINITION OF DONE: integration test output quoted
