# Order routes

This route group presents order-related owner workflows supported by the backend.

## Architecture and use

Order state and payment facts must come from authorized backend records or verified providers. The model and client UI must not set payment status. Any action that changes order state follows the backend's policy and approval boundaries.

## Metrics and impact

No order conversion, fulfillment, or payment metrics are recorded here. The UI provides a place to review the available order workflow without claiming that future integrations are active.
