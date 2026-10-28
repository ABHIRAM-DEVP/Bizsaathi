# T-205: Voice intake (stretch)

- **PHASE:** 2  **PRIORITY:** P2
- **OBJECTIVE:** Transcribe seller voice and merge suggestions into a draft with transcript spans.
- **DEPENDS ON:** Prompt 9 verification of transcription access.
- **ACCEPTANCE:** Conflicting spoken price remains a high conflict; multilingual support is measured on real samples; oversized audio returns 413.
- **TEST COMMAND:** `just check`
- **SECURITY:** Transcript is untrusted input; no facts are overwritten.
- **STATUS:** Deferred: transcription access is UNVERIFIED and no live API call was approved.
