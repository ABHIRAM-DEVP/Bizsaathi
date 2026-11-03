# Persistence models

This package defines SQLAlchemy's shared base and application domain models. Models represent persisted business records and relationships; confirmed product, stock, and account facts come from these records, not from generated text.

## Architecture and use

Schema evolution is managed through Alembic in `backend/alembic/`. Do not edit an applied migration. Keep tenant ownership explicit and enforce tenant scope in the corresponding service/repository queries.

## Stack, metrics, and impact

SQLAlchemy 2 and PostgreSQL. There are no independent model performance metrics. This layer gives services durable, typed records and supports auditability and tenant-scoped access.
