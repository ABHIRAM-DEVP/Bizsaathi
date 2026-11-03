# API schemas

> [Back to BizSaathi overview](../../../README.md)

Pydantic models in this package define API request and response data for authentication, businesses, products, uploads, jobs, approvals, conversations, customers, orders, posts, and dashboards.

## Architecture and use

Schemas validate external input and serialize endpoint output. Keep them aligned with endpoint specifications and the generated OpenAPI contract. Do not weaken validation to accommodate model-generated data; validate model output at its own boundary.

## Stack, metrics, and impact

Pydantic v2 and FastAPI. No independent schema-quality metric is recorded. Explicit schemas keep the API contract reviewable and help reject malformed input before it reaches business logic.
