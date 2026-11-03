# ADR-0004: Structured intent planning for customer chat

- Status: accepted
- Date: 2026-11-02

## Context
Public customer chat used only keyword matching, so natural product questions and follow-ups were poorly understood. The system must keep shop facts in PostgreSQL, protect customer data, and remain responsive when the model is unavailable.

## Decision
Add one bounded structured intent-planning call through the existing model adapter after tenant-scoped knowledge retrieval. Rank active catalog records against the current question and recent product mentions before placing a bounded set in model context. The planner may select only retrieved product IDs, allowed product fields, and known policy kinds. Deterministic code writes the response and the existing evidence verifier records every factual source. Short product-name messages, plural price terms, and plural follow-ups use the same catalog retrieval; unmatched product names receive a focused clarification rather than a generic welcome. Critical-request triage stays before the model. Escalated conversations may continue receiving replies.

## Consequences
- Live model mode can resolve semantic product references and follow-ups without generating unverified shop facts.
- Catalog retrieval is tenant-scoped and locally ranked over product names, descriptions, attributes, and recent conversation references; it requires no new embedding provider or vector-store dependency.
- Mock mode remains deterministic and is not reported as live model quality; planner failures use the same deterministic, evidence-checked routing.
- The planner has one call, a 15-second maximum timeout, no retry, bounded context, and no authority to perform actions.
- Unsupported shop-overview questions use saved catalog names when profile text is absent; otherwise the assistant asks a useful follow-up.
