# Reference schema

> [Back to BizSaathi overview](../../README.md)

`reference_schema.sql` is a design reference for the relational domain model. It documents tables, relationships, and tenant ownership for planning and review.

## Architecture and use

This file is not an Alembic revision and must not be applied as a substitute for backend migrations. Runtime schema changes belong in a new Alembic migration, with corresponding SQLAlchemy model and repository updates.

## Metrics and impact

The current reference SQL contains 32 `CREATE TABLE` statements; this is a design inventory, not a live database table count. The schema's value is making data ownership and relationships reviewable.
