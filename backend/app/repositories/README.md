# Repositories

> [Back to BizSaathi overview](../../../README.md)

Repositories encapsulate persistence queries used by domain services. The current package contains product and variant data-access modules.

## Architecture and use

Services should call repositories rather than duplicate SQLAlchemy query construction. Every tenant-owned read or write must include server-derived business scope; callers must not be able to select another tenant by supplying an arbitrary identifier.

## Stack, metrics, and impact

Python, SQLAlchemy 2, and PostgreSQL. No query latency or throughput measurements are recorded here. Centralized queries make access rules easier to review and regression-test.
