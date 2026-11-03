# API contracts

`openapi.json` is the checked-in OpenAPI 3.1 contract for the BizSaathi API. It describes endpoint paths, operations, request/response schemas, and service errors for frontend and API consumers.

## Architecture and use

Backend routes and Pydantic schemas implement behavior; [endpoint specifications](../docs/14-endpoint-specs.md) define intended semantics. This file is the API/web source of truth. Regenerate or update the contract through the repository workflow after intentional API changes. Do not hand-edit generated frontend API client files.

## Metrics and impact

The OpenAPI document currently declares version `0.1.0`; this is a contract version, not an API performance metric. No client compatibility or usage metrics are recorded. A shared contract reduces frontend/backend shape drift.
