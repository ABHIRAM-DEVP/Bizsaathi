# T-301: Claim verification

- **PHASE:** 3  **PRIORITY:** P0
- **OBJECTIVE:** Verify every claim against versioned evidence, fail closed, and expose tenant-scoped verdicts.
- **DEPENDS ON:** T-204
- **ACCEPTANCE:** Contradicted material, unsupported origin and superlatives return a verdict with evidence IDs; stale versions return 409; nonexistent model evidence is overridden.
- **TEST COMMAND:** `just check`
- **SECURITY:** Never return a bare safe flag; evidence lookup is tenant-scoped.
- **STATUS:** Started: deterministic post claim-check endpoint and evidence snapshot creation implemented. Evidence retrieval, guardrail events, migration assessment and acceptance tests remain.
