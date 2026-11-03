# 02 Data model

ASSUMPTION: entity set is a starting point; include only what the MVP needs. Every business-owned table has `business_id`.

Authoritative column types, enums and formats: docs/15-schema-and-formats.md. Reference DDL: docs/schema/reference_schema.sql (adds sessions, OTP, jobs, proposals, executions, evidence, orders, audit, idempotency, usage and eval tables that this overview diagram omits; `order` is `customer_order`, `user` is `app_user`, money columns are `*_inr numeric(12,2)`). Where this file and docs/15 differ, docs/15 wins.

```mermaid
erDiagram
  BUSINESS ||--o{ USER : has
  BUSINESS ||--o{ PRODUCT : owns
  PRODUCT ||--o{ PRODUCT_VARIANT : has
  PRODUCT ||--o{ MEDIA : has
  BUSINESS ||--o{ POLICY : defines
  BUSINESS ||--o{ JOB : runs
  JOB ||--o{ PROPOSAL : produces
  PROPOSAL ||--o{ APPROVAL : receives
  PROPOSAL ||--o{ CLAIM : contains
  CLAIM ||--o{ EVIDENCE : cites
  PRODUCT ||--o{ POST : promoted_by
  BUSINESS ||--o{ CONVERSATION : receives
  CONVERSATION ||--o{ MESSAGE : has
  BUSINESS ||--o{ ORDER : receives
  ORDER ||--o{ ORDER_ITEM : contains
  BUSINESS ||--o{ AUDIT_EVENT : logs
  CUSTOMER_ACCOUNT ||--o{ CUSTOMER_AUTH_SESSION : signs_in_with
  CUSTOMER_ACCOUNT ||--o{ PUBLIC_SESSION : chats_as
  PUBLIC_SESSION ||--o| CONVERSATION : owns
  BUSINESS { uuid id PK  text name  text slug }
  USER { uuid id PK  uuid business_id FK  text role }
  PRODUCT { uuid id PK  uuid business_id FK  text sku  text name  numeric price_inr  text status }
  PRODUCT_VARIANT { uuid id PK  uuid product_id FK  text color  int stock  int stock_version }
  MEDIA { uuid id PK  uuid business_id FK  text storage_key  text kind }
  POLICY { uuid id PK  uuid business_id FK  text kind  text body  int version }
  JOB { uuid id PK  uuid business_id FK  text kind  text status  jsonb state_ref }
  PROPOSAL { uuid id PK  uuid job_id FK  int version  jsonb payload  text status }
  APPROVAL { uuid id PK  uuid proposal_id FK  int proposal_version  uuid decided_by  text decision }
  CLAIM { uuid id PK  uuid proposal_id FK  text text  text verdict  text severity }
  EVIDENCE { uuid id PK  uuid claim_id FK  text source_kind  text source_id  int source_version }
  POST { uuid id PK  uuid product_id FK  text channel  text status  int version }
  CONVERSATION { uuid id PK  uuid business_id FK  text session_id  text status }
  MESSAGE { uuid id PK  uuid conversation_id FK  text role  text body }
  CUSTOMER_ACCOUNT { uuid id PK  text email  text display_name  bytea password_hash }
  CUSTOMER_AUTH_SESSION { uuid id PK  uuid customer_account_id FK  text token_hash  timestamptz expires_at }
  PUBLIC_SESSION { uuid id PK  uuid business_id FK  uuid customer_account_id FK  timestamptz expires_at }
  PUBLIC_RATE_LIMIT_BUCKET { text key_hash PK  timestamptz window_start  int request_count }
  ORDER { uuid id PK  uuid business_id FK  text status  text idempotency_key }
  ORDER_ITEM { uuid id PK  uuid order_id FK  uuid variant_id FK  int qty  numeric unit_price_inr }
  AUDIT_EVENT { uuid id PK  uuid business_id FK  text actor  text action  jsonb detail  timestamptz at }
```

## Conventions
- Keys: uuid. Timestamps: timestamptz UTC; `created_at`/`updated_at` everywhere.
- Facts vs suggestions: `PRODUCT` holds confirmed facts. AI output lives in `PROPOSAL.payload` until an approved write by the execution service.
- Evidence references business profile, product id, stock_version, policy version and source span.
- Orders: DRAFT -> AWAITING_PAYMENT -> PAID -> FULFILLED, plus CANCELLED and FAILED. Only the execution service transitions state.
- Tenant: repositories always filter `business_id`; consider RLS (needs ADR). Negative tests for every table.
- Public chat requires a customer account. Store sessions are bound to both the customer account and business; authentication tokens are stored as hashes.
- Public rate limits use shared, fixed-window PostgreSQL counters keyed by a SHA-256 digest; expired buckets are cleaned up opportunistically.
- Retention: TODO define for media, transcripts, conversations. Redact PII before logs and model calls.

## Redis keys (ASSUMPTION)
| Pattern | Purpose | TTL |
|---|---|---|
| `job:{id}:events` | progress stream | 1h |
| `cache:{business_id}:product:{id}` | safe read cache | 60s |

## Indexes
| Table | Index | Serves |
|---|---|---|
| all tenant tables | (business_id, ...) | tenant-scoped queries |
| PRODUCT | (business_id, sku) unique | reconciliation |
| ORDER | (business_id, idempotency_key) unique | safe retries |
| AUDIT_EVENT | (business_id, at) | audit views |
| PUBLIC_RATE_LIMIT_BUCKET | (window_start) | expire old rate-limit counters |
