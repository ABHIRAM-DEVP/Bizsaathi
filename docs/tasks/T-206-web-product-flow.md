# T-206: Web product flow

- **PHASE:** 2  **PRIORITY:** P1
- **OBJECTIVE:** Provide responsive seller routes for catalogue intake, draft review and approvals in the single Next.js PWA.
- **FILES:** `frontend/app/{products,approvals}/`, `frontend/app/components/`
- **DEPENDS ON:** T-202, T-203
- **ACCEPTANCE:** AI values use explicit labels; conflicts require an explicit choice; price and stock are required; changed proposals cannot be approved; all six UI states have component coverage and Playwright covers 390/1280 px.
- **TEST COMMAND:** `cd frontend && npm run lint && npm run build`
- **SECURITY:** UI never marks AI suggestions as confirmed and never uses browser model credentials.
- **OUT OF SCOPE:** Live API wiring and Playwright/component tests (test tooling has not been added or approved).
- **STATUS:** Product-to-post workflow is wired; automated browser/component coverage and remaining six-state coverage remain.
