# T-310: Synthetic inbox message simulation

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Make the local inbox demo feel active with longer, product-contextual sample customer messages.
- **FILES:** `backend/app/routers/conversations.py`, `backend/tests/integration/test_conversations_flow.py`, `frontend/app/messages/`
- **DEPENDS ON:** T-308
- **ACCEPTANCE:**
  - Development/test owners can request the next synthetic customer message; it cycles across three tenant-scoped demo customers.
  - Generated sample text may include a bounded excerpt of the tenant's active product description and never invents catalog facts.
  - The development inbox requests one simulated message every 30 seconds and visibly labels the simulation.
  - Production cannot use the simulation endpoint; no external messages are sent.
- **TEST COMMAND:** `cd backend && uv run pytest tests/integration/test_conversations_flow.py -q`; frontend lint and typecheck
- **SECURITY:** Require owner authorization and tenant scope; treat copied product descriptions as untrusted text; production remains disabled.
- **OUT OF SCOPE:** Real customer data, messaging-provider delivery, and model-generated customer messages.
- **STATUS:** Implemented; PostgreSQL integration and frontend checks passed.
