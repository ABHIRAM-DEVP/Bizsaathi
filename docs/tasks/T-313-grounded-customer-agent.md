# T-313: Grounded public customer agent

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Add structured AI intent planning to public customer chat without weakening deterministic evidence checks, and keep escalated conversations responsive.
- **FILES:** `backend/app/services/customer_replies.py`, `backend/app/routers/public_store.py`, `backend/tests/unit/test_customer_replies.py`, `backend/tests/integration/test_conversations_flow.py`
- **DEPENDS ON:** T-312
- **ACCEPTANCE:**
  - The public chat workflow uses one bounded structured model plan to interpret intent, product references, and requested facts; only tenant-retrieved product, profile, and policy records may ground the final answer.
  - Product candidates are ranked from the tenant catalog using names, descriptions, attributes, and recent conversation context; plural price requests, bare product names, and plural follow-ups return relevant grounded listings instead of generic greetings.
  - Model output is schema-validated and constrained to retrieved IDs and allowed fields; deterministic evidence verification remains the final gate.
  - If the shop profile description is absent, the assistant can summarize available catalog listings with product evidence; if neither profile nor catalog can answer, it asks a useful follow-up without falsely escalating.
  - An escalated conversation can still receive replies to later customer messages; sensitive requests remain escalated and no order, payment, or policy action is performed.
  - Closed sessions and conversations reject new messages without storing them; the storefront opens a fresh session and retries once so customers receive a reply.
  - Resuming a session recovers all trailing stored customer messages that have no assistant reply, without duplicating customer messages or generating repeated replies.
  - Ordinary unsupported questions receive a useful non-blocking clarification rather than a terminal response.
  - Product-shopping questions are not mistaken for requests to place or manage an order.
- **TEST COMMAND:** Targeted backend unit and public-chat integration tests; backend Ruff and mypy.
- **SECURITY:** Preserve tenant-scoped retrieval, customer-data minimization, untrusted-input handling, evidence IDs for factual replies, and seller escalation for sensitive requests.
- **OUT OF SCOPE:** External order/payment execution, live-provider requests during tests, and changes to account/session authorization.
- **STATUS:** Implemented; targeted unit/integration tests, repository fast checks, and local backend readiness passed.
