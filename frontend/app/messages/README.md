# Owner messages

> [Back to BizSaathi overview](../../../README.md)

This route group provides the seller inbox for customer conversations and owner replies.

## Architecture and use

The frontend reads conversations and sends replies through backend APIs. Persisted customer-visible messages must be distinguished from drafts or local-only states; delivery claims should reflect backend results. Customer access and tenant scope are enforced server-side.

## Metrics and impact

No response-time, delivery, or customer-resolution metrics are recorded. The intended value is a shared conversation surface for owners and customers, not a claim that every response is delivered through external messaging channels.
