# ADR-0001: Modular monolith plus worker

- Status: proposed (accept after you review)
- Date: 2026-10-28

## Context
Solo or very small team, short deadline, many moving parts (API, agents, jobs, PWA). Microservices would add deployment and debugging overhead without demo value.

## Options considered
1. Modular monolith (FastAPI) + one worker process - least overhead; clear module boundaries.
2. Several services (agents, API, execution) - cleaner isolation, much more infrastructure.

## Decision
Option 1. Keep the execution service as a separate module with its own permissions so the approval boundary stays explicit and could be split later.

## Consequences
Faster to build and test. Must enforce module boundaries by convention and tests (no agent imports from execution internals).
