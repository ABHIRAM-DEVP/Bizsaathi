# Public store routes

> [Back to BizSaathi overview](../../../README.md)

This route group serves customer-facing storefront pages and in-app chat for a store slug.

## Architecture and use

Public page data and chat are fetched from backend public-store endpoints. Customer input is untrusted; the backend derives business scope from the store and applies rate limits and data-access rules. Replies must be grounded in retrieved facts or safely escalated.

## Metrics and impact

No customer engagement, answer accuracy, or resolution metrics are recorded. The intended value is a direct customer-to-store interaction path; it does not imply external channel delivery.
