# TASK_ID: T-307
TITLE: Local account sign-in alongside demo access
PHASE: 3
PRIORITY: MVP
OBJECTIVE: Keep demo access and provide development-only registration and sign-in for isolated business owner accounts.
BACKGROUND: docs/14-endpoint-specs.md, docs/15-schema-and-formats.md, .claude/rules/api.md, .claude/rules/db-tenancy.md, .claude/rules/security.md
IMPLEMENTATION STEPS:
  1. Add tests for signed local sessions, credential validation, sign-in, environment gating, and cross-tenant isolation.
  2. Add development-only registration and sign-in endpoints with hashed passwords and a signed HttpOnly session cookie.
  3. Add reversible Alembic migrations for local-development identities and credentials; update the API contract and docs.
  4. Keep demo access available, let owners switch between registration and sign-in, and clear the local cookie on logout/demo switching.
ACCEPTANCE CRITERIA:
  - The login screen keeps the configured demo option and offers separate create-account and existing-account sign-in flows.
  - A valid local signup persists a distinct business and owner in PostgreSQL and enters that tenant.
  - A valid sign-in verifies the normalized email and password and enters that account's own tenant; invalid credentials fail closed.
  - The API accepts only signed development sessions; malformed cookies fail closed. The local signed token has no server-side expiry, and logout invalidates copied tokens by incrementing the account session version.
  - Local registration and sign-in are unavailable outside ENV=dev, and demo access continues to work.
  - A newly registered tenant cannot read another tenant's products.
  - Credentials are stored only as a password hash and are never placed in browser storage, logs, or frontend build variables.
TEST COMMAND: backend unit tests and focused PostgreSQL integration test; frontend lint/build; contract-check
SECURITY CONSIDERATIONS: Registration and sign-in are local-development only. Passwords are bcrypt-hashed. Use a persistent HttpOnly SameSite cookie signed by the server secret. Keep local account identity separate from phone-OTP accounts. Logout invalidates every local session for that owner without imposing an expiry. Existing accounts created before credentials were introduced cannot sign in until a safe recovery path is defined.
OUT OF SCOPE: Production authentication, phone verification, and SMS delivery.
DEFINITION OF DONE: Report the exact focused test and build outputs.
