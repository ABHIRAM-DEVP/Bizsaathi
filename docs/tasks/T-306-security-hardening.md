# T-306: Security hardening pass

- **PHASE:** 3  **PRIORITY:** P0
- **OBJECTIVE:** Prove tenancy, injection and tool boundaries with generated route and evaluation tests.
- **DEPENDS ON:** T-301, T-302, T-303, T-304
- **ACCEPTANCE:** Tenant/unauthenticated contract tests pass; all listed injection cases pass; agents expose neither SQL nor payment/publish writes.
- **TEST COMMAND:** `just check && just eval-mock`
- **SECURITY:** Review every public and owner route and all trace/log surfaces.
