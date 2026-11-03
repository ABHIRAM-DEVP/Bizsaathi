# T-312: Customer accounts and chat agent

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Require customer accounts for public chat and deliver safe, catalog-grounded automated conversations.
- **FILES:** `backend/app/models/domain.py`, `backend/app/routers/public_store.py`, `backend/app/services/customer_replies.py`, `backend/alembic/versions/`, `frontend/app/store/`
- **DEPENDS ON:** T-308, T-311
- **ACCEPTANCE:**
  - Customers can register and log in with normalized email and a securely hashed password; chat access requires an authenticated account.
  - Customer chat sessions and conversation history are bound to the account and store tenant.
  - Customer messages are persisted to the owner inbox and surfaced through in-app inbox updates.
  - Owner replies to public conversations are visible to the authenticated customer in the saved chat history and in-app live stream; synthetic demo replies remain undelivered.
  - The chat workflow answers only confirmed catalog price, stock, and description facts, can recommend catalog products, and attaches evidence to factual responses.
  - The chat workflow can answer questions about the saved shop profile and latest tenant-owned delivery, returns, discount, and payment policies with evidence; missing profile/policy facts are not invented.
  - Product matching considers saved names, descriptions, and attributes; multi-part questions are answered together, and follow-up questions resolve against recent conversation context.
  - Refunds, payment/order actions, safety claims, and unsupported facts escalate; no agent performs external or consequential actions.
  - The shared public chat page supports account registration/login and authenticated chat.
- **TEST COMMAND:** Targeted backend unit/integration tests; frontend lint, typecheck, and build.
- **SECURITY:** Argon/bcrypt-class password hashes, opaque revocable customer sessions, tenant ownership checks, origin-validated mutation requests, shared rate limits, no PII in model prompts/logs.
- **OUT OF SCOPE:** Email/SMS verification, provider delivery, payment or order execution, customer PII beyond email and display name.
- **STATUS:** Implemented; targeted unit/integration tests and migration upgrade/downgrade passed.
