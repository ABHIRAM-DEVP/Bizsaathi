---
name: add-migration
description: Create and verify an Alembic migration with business_id tenancy, upgrade/downgrade and an integration test on real Postgres. Use when changing database schema.
argument-hint: "[what changes]"
disable-model-invocation: true
---

# Migration: $ARGUMENTS

1. Read .claude/rules/db-tenancy.md and docs/02-data-model.md. Update the data model doc first if the design changes.
2. Change the SQLAlchemy model. Business-owned tables need `business_id` and a tenant index. Keep AI suggestions separate from confirmed facts.
3. `just up`, then `just new-migration "$ARGUMENTS"`. Open the generated file and fix types, indexes, constraints, defaults and backfills.
4. Verify on real Postgres: `just migrate`, downgrade one step, upgrade again.
5. Add or update an integration test, including a cross-tenant negative test for new tables.
6. `just check`. Report changed files, commands run, and any lock or backfill risk.
