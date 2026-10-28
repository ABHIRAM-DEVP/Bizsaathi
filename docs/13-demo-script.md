# 13 Demo script (3 minutes)

Only show what was built and tested. Label mocks on screen. Adjust to the official submission requirements (TODO verify).

| Time | Beat | Show | Must be real |
|---|---|---|---|
| 0:00-0:30 | Problem | Seller uploads a handloom product photo (and a mixed-language voice note if voice is built); plan appears | upload + job |
| 0:30-1:15 | Multimodal intelligence | extracted fields with uncertainty flags; spoken price vs DB conflict flagged, not silently chosen; segmentation only if built | conflict record |
| 1:15-2:00 | Verifiable agents | generate caption with an unsupported claim; verifier rejects; repair proposes supported wording; evidence ids shown | verifier + repair |
| 2:00-2:35 | Human-controlled execution | customer asks an ambiguous stock/delivery question; assistant checks facts, escalates; seller approves a diff | escalation + approval |
| 2:35-3:00 | Technical proof | trace, evidence refs, a blocked action, eval scorecard from a real run, honest limits slide | eval report |

## Pre-flight checklist
- [ ] `just check` green; `just guards` clean
- [ ] Live Meta call verified today; credits remaining noted
- [ ] Demo data seeded; tenant A and B accounts ready for the isolation moment
- [ ] Offline/PWA install shown only if verified on a phone-size viewport
- [ ] Mock items identified on screen
- [ ] Fallback: screen recording of the happy path if the live API is slow
