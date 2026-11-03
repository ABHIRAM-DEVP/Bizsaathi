# Alembic migrations

This folder contains database migration configuration and versioned schema changes for the backend's PostgreSQL database.

## Architecture and use

Alembic revisions describe schema evolution; application SQLAlchemy models describe the current domain mapping. Add a new revision for schema changes and preserve already-applied revisions. The reference schema in `docs/schema/` is design documentation, not an applied migration.

## Metrics and impact

No migration-duration or database-size metrics are recorded. Migration history enables repeatable database setup and controlled upgrades.
