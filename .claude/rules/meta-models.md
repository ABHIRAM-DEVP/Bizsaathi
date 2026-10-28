---
paths:
  - "backend/app/ai/**"
  - "backend/tests/**/ai/**"
---

# Model adapter rules (zero paid API usage)
- All model access goes through one adapter interface in app/ai: `generate_structured`, `transcribe`, `segment`, `generate_image`. Nodes depend on the interface, never directly on an external provider SDK or hardcoded URL.
- Zero paid API usage policy: Never make paid Meta API calls or configure paid subscriptions. Default operation mode is mock (`MockModelClient`).
- When live model calls are enabled, credentials and base URLs are strictly read from server-side environment variables in `.env` (e.g. `MODEL_API_KEY`).
- Never invent a model ID, endpoint, parameter, rate limit or price. Mark UNVERIFIED in code comments and docs when unverified.
- Two implementations: `LiveClient` and `MockModelClient` (deterministic fixtures, labelled as mock in every log line and eval report). Tests default to the mock.
- Every call: timeout, bounded retry on transient errors only, usage logged (model id, latency, tokens or units), redaction of PII before sending, no secrets in logs.
- Live calls require explicit user authorization. Cache only deterministic, tenant-scoped, non-sensitive results.
- SAM segmentation gives masks and geometry, not product truth. Do not treat a mask as verification of material, quality or authenticity.
- Image generation output must not silently change sale-relevant attributes (color, pattern, size). The critic compares generated visuals against the product record.
