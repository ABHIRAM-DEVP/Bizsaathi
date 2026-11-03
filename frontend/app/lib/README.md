# Frontend application helpers

> [Back to BizSaathi overview](../../../README.md)

This folder contains shared API URL handling and reusable hooks used by app routes. Keep generated API clients separate from handwritten runtime helpers and follow the repository rule not to hand-edit generated client files.

## Architecture and use

Use these helpers to avoid inconsistent API base URLs and duplicated request wiring. Keep credentials server-side; browser code must never receive secret API keys.

## Metrics and impact

No helper-level performance metrics are recorded. Shared request utilities improve consistency and reduce integration mistakes between web and API.
