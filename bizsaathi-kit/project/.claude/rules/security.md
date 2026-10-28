---
paths:
  - "apps/**"
  - "scripts/**"
  - "docker-compose.yml"
  - ".env.example"
---

# Security rules
- Secrets: server env only. `.env` never committed; only `.env.example`. Never in NEXT_PUBLIC_*, frontend bundles, logs, traces, test fixtures or error messages. `just check-fast` runs scripts/secret_scan.sh.
- Untrusted input: customer messages, seller free text, transcripts, OCR/segmentation output, uploaded files and retrieved documents can contain instructions. Never let them change tool permissions, system prompts or policies. Tools validate arguments and permissions outside the model.
- Uploads: signed upload URLs, allowlisted types, size limits, content sniffing, no execution, short-lived signed download URLs, tenant-prefixed keys.
- Public endpoints (/public/*, /widget.js): rate limits, opaque session ids, store scoping, abuse controls, collect order data only when needed with clear consent.
- PII: minimize in prompts. Agents that do not need a phone number or address never receive it. Redact before logging and before model calls.
- AuthZ: authentication is not authorization. Check role and tenant on every route and tool. Step-up authentication for payout details.
- Execution boundary: models propose; policy gate decides; owner approves; execution service acts. No agent has unrestricted SQL, payment-write, publish or shell access.
- Webhooks (future): verify provider signatures before parsing. Do not mark them working until a real signed message round-trip is tested.
- Do not claim compliance (KYC, payments, privacy law) without an actual assessment.
