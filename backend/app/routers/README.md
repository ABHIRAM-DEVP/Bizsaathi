# HTTP routers

> [Back to BizSaathi overview](../../../README.md)

This package exposes the versioned FastAPI endpoints for authentication, businesses, products, uploads, jobs, approvals, posts, conversations, orders, public stores, audit, and health.

## Architecture and use

Routers validate HTTP input and delegate business behavior to services. Pydantic schemas define request/response shapes. Endpoint behavior is documented in [docs/14-endpoint-specs.md](../../../docs/14-endpoint-specs.md), and the shared OpenAPI contract is [contracts/openapi.json](../../../contracts/openapi.json).

## Stack, metrics, and impact

FastAPI and Pydantic v2. No production request-volume or latency values are recorded. The routers provide a stable, typed boundary for the web app and public store clients.
