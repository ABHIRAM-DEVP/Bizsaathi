# T-303: Policy gate and post approvals

- **PHASE:** 3  **PRIORITY:** P0
- **OBJECTIVE:** Route post actions through deterministic policy, version-bound approval and execution.
- **DEPENDS ON:** T-301, T-203
- **ACCEPTANCE:** Payment writes deny; stale checked posts cannot submit; unapproved posts cannot export; share-status makes no network call.
- **TEST COMMAND:** `just check`
- **SECURITY:** Agents cannot publish or write payment state.
