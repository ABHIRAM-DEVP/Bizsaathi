# Domain services

Services implement application behavior used by routers and background workflows. Current modules cover claim verification, customer accounts and replies, dashboard aggregation, demo orders, execution, policy gating, post generation, public rate limits, uploads, and orders.

## Architecture and use

Services coordinate repositories, models, and agent/model adapters. They are a key enforcement point for tenant scope and deterministic policy. Side effects must occur only through the execution boundary after approval bound to the exact proposal version.

## Stack, metrics, and impact

Python, SQLAlchemy-backed repositories, Pydantic domain data, and the model adapter where needed. No production impact or latency figures are recorded. This layer translates API operations into controlled business behavior.
