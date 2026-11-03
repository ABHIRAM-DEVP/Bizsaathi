# T-308: Demo inbox and widget

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Provide an owner inbox and interactive, clearly synthetic widget demo using only tenant catalog facts.
- **FILES:** `backend/app/routers/{conversations,public_store}.py`, `backend/app/services/customer_replies.py`, `frontend/app/messages/`
- **DEPENDS ON:** T-203, T-205
- **ACCEPTANCE:**
  - Owner conversation list/detail and reply-draft APIs enforce owner role and tenant isolation.
  - Development/test demo seeding is idempotent and uses synthetic labels; production cannot seed demo data.
  - Customer replies use confirmed catalog facts with evidence IDs; critical or unknown requests escalate to the seller.
  - The synthetic widget preview and demo inbox never send externally; demo owner replies are stored as drafts. Public owner replies are shown only inside the authenticated in-app customer chat.
  - Messages opens the demo automatically in local development; filters, errors, empty states, and mobile layouts remain usable.
  - Browser speech recognition can add text to an owner reply draft, with an explicit unsupported-browser state.
- **TEST COMMAND:** `python scripts/runner.py check`; `cd backend && uv run pytest tests/integration -x -q`; mock evaluation and OpenAPI contract comparison
- **SECURITY:** Every conversation query is tenant-scoped; customer messages are untrusted; no PII, model secrets, or external sends.
- **OUT OF SCOPE:** Real messaging-provider delivery, customer identification, payment/order actions, and live model quality claims.
- **STATUS:** Implemented; unit, integration, contract, mock-evaluation, runtime, and security verification passed.
