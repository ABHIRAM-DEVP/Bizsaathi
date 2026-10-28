# T-302: Critic and bounded repair

- **PHASE:** 3  **PRIORITY:** P0
- **OBJECTIVE:** Check cross-modal consistency separately from writing and cap repair at two attempts.
- **DEPENDS ON:** T-301
- **ACCEPTANCE:** Colour mismatch is high severity; exactly two failed repairs then `retry.cap_reached`; repaired text returns through verification.
- **TEST COMMAND:** `just check`
- **SECURITY:** Critic configuration is distinct from writer; no model certifies its own result.
