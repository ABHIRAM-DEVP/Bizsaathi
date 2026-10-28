---
paths:
  - "apps/api/app/ai/**"
  - "apps/api/tests/**/ai/**"
---

# Meta model adapter rules
- All model access goes through one adapter interface in app/ai: `generate_structured`, `transcribe`, `segment`, `generate_image`. Nodes depend on the interface, never on an SDK or URL.
- Model IDs, base URLs, timeouts and limits come from config. Credentials come from env on the server. Nothing hardcoded, nothing in the frontend.
- Never invent a model ID, endpoint, parameter, rate limit or price. Verify against official Meta docs and record the finding with its source in docs/12-assumptions-risks-deps.md. Unverified = mark UNVERIFIED in code comments and docs.
- Two implementations: `LiveMetaClient` and `MockModelClient` (deterministic fixtures, labelled as mock in every log line and eval report). Tests default to the mock.
- Every call: timeout, bounded retry on transient errors only, usage logged (model id, latency, tokens or media units if exposed), redaction of PII before sending, no secrets in logs.
- Live calls cost credits: `just meta-smoke` and `just eval-live` need human approval each run. Cache only deterministic, tenant-scoped, non-sensitive results.
- SAM segmentation gives masks and geometry, not product truth. Do not treat a mask as verification of material, quality or authenticity.
- Muse Image output must not silently change sale-relevant attributes (color, pattern, size). The critic compares generated visuals against the product record.
