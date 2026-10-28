# T-304: Audit, guardrail and trace endpoints

- **PHASE:** 3  **PRIORITY:** P1
- **OBJECTIVE:** Expose sanitized, tenant-scoped audit, guardrail and workflow traces.
- **DEPENDS ON:** T-303
- **ACCEPTANCE:** Approval audit exists; traces contain no reasoning/secrets; operator reads but cannot write; tenant B sees no A data.
- **TEST COMMAND:** `just check`
- **SECURITY:** Recursive redaction tests enforce observable events only.
