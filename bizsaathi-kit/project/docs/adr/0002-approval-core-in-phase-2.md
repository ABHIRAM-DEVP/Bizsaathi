# ADR-0002: Minimal approval and execution core moves to Phase 2

- Status: proposed (accept or reject)
- Date: 2026-10-28

## Context
docs/PHASES.md places approvals in Phase 3. But a product cannot be created from an AI draft without the seller-confirmation path, and the brief forbids agents from writing confirmed facts. Building products first with a shortcut would create a write path that bypasses the execution service.

## Options considered
1. Keep approvals in Phase 3 and let Phase 2 create products directly from the API (shortcut): faster now, but a second write path to remove later.
2. Build the minimal approval and execution core (types product_create and product_update) in Phase 2 and generalize in Phase 3.

## Decision
Option 2, as in prompts 2.3 and 3.3 of docs/prompts/BUILD-PHASES.md.

## Consequences
Phase 2 is a little larger. The execution service is the single writer of confirmed facts from the start, and the boundary test (agents cannot import it) exists from day one. Update docs/PHASES.md when accepted.
