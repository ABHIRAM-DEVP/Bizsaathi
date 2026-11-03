-- BizSaathi reference schema (PostgreSQL 16). DESIGN REFERENCE, not a migration.
-- Real schema changes go through Alembic (see .claude/rules/db-tenancy.md and /add-migration).
-- UNVERIFIED: this file was not executed against a database when the kit was built; scripts/check_docs.py only checks
-- structure (balanced parentheses, referenced tables exist, tenant column present). Run it on real Postgres in T-103.
-- Conventions: uuid keys via gen_random_uuid(); timestamptz UTC; enums as text + CHECK; money numeric(12,2) named *_inr;
-- every business-owned table has business_id; repositories always filter on it.

CREATE TABLE business (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name          text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 120),
  slug          text NOT NULL CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'),
  description   text CHECK (char_length(description) <= 2000),
  languages     text[] NOT NULL DEFAULT ARRAY['en'],
  status        text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX business_slug_uq ON business (lower(slug));

CREATE TABLE app_user (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  phone_e164    text CHECK (phone_e164 IS NULL OR phone_e164 ~ '^\+[1-9][0-9]{7,14}$'),
  local_email   text UNIQUE CHECK (char_length(local_email) <= 320),
  local_password_hash bytea,
  local_session_version integer NOT NULL DEFAULT 0 CHECK (local_session_version >= 0),
  identity_type text NOT NULL DEFAULT 'phone' CHECK (identity_type IN ('phone','local_dev')),
  role          text NOT NULL CHECK (role IN ('owner','operator')),
  display_name  text CHECK (char_length(display_name) <= 120),
  language      text NOT NULL DEFAULT 'en' CHECK (language IN ('en','hi','mr')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  CHECK ((identity_type = 'phone' AND phone_e164 IS NOT NULL AND local_email IS NULL AND local_password_hash IS NULL)
      OR (identity_type = 'local_dev' AND phone_e164 IS NULL
          AND ((local_email IS NULL AND local_password_hash IS NULL)
            OR (local_email IS NOT NULL AND local_password_hash IS NOT NULL))))
);
CREATE UNIQUE INDEX app_user_phone_uq ON app_user (phone_e164);
CREATE INDEX app_user_business_ix ON app_user (business_id);

CREATE TABLE auth_session (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL REFERENCES app_user(id),
  business_id   uuid NOT NULL REFERENCES business(id),
  token_hash    bytea NOT NULL,              -- sha-256 of the opaque token; the token itself is never stored
  rotated_from  uuid REFERENCES auth_session(id),
  created_at    timestamptz NOT NULL DEFAULT now(),
  expires_at    timestamptz NOT NULL,
  revoked_at    timestamptz
);
CREATE UNIQUE INDEX auth_session_token_uq ON auth_session (token_hash);
CREATE INDEX auth_session_user_ix ON auth_session (user_id);

CREATE TABLE otp_challenge (                  -- not tenant-owned: exists before a business does
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_e164    text NOT NULL CHECK (phone_e164 ~ '^\+[1-9][0-9]{7,14}$'),
  code_hash     bytea NOT NULL,
  attempts      integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  locked_until  timestamptz,
  expires_at    timestamptz NOT NULL,
  consumed_at   timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX otp_challenge_phone_ix ON otp_challenge (phone_e164, created_at DESC);

CREATE TABLE policy (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  kind          text NOT NULL CHECK (kind IN ('delivery','returns','discounts','payment','other')),
  version       integer NOT NULL CHECK (version >= 1),
  body          text NOT NULL CHECK (char_length(body) <= 5000),
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (business_id, kind, version)         -- a change creates a new version; old versions stay for evidence
);

CREATE TABLE product (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  sku           text NOT NULL CHECK (sku ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$'),
  name          text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 200),
  description   text CHECK (char_length(description) <= 5000),
  price_inr     numeric(12,2) NOT NULL CHECK (price_inr >= 0),
  field_sources jsonb NOT NULL DEFAULT '{}'::jsonb,  -- per-field provenance: {"material":{"source":"confirmed"}}
  attributes    jsonb NOT NULL DEFAULT '{}'::jsonb,  -- confirmed free attributes: material, origin, care, ...
  status        text NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived')),
  version       integer NOT NULL DEFAULT 1 CHECK (version >= 1),   -- optimistic concurrency (If-Match)
  created_by    uuid REFERENCES app_user(id),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  archived_at   timestamptz,
  UNIQUE (business_id, sku)
);
CREATE INDEX product_business_status_ix ON product (business_id, status, created_at DESC);

CREATE TABLE product_variant (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  product_id    uuid NOT NULL REFERENCES product(id),
  color         text CHECK (char_length(color) <= 60),
  size          text CHECK (char_length(size) <= 60),
  stock         integer NOT NULL DEFAULT 0 CHECK (stock >= 0),
  stock_version integer NOT NULL DEFAULT 1 CHECK (stock_version >= 1),
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX product_variant_uq ON product_variant (product_id, coalesce(color,''), coalesce(size,''));
CREATE INDEX product_variant_business_ix ON product_variant (business_id, product_id);

CREATE TABLE media (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  product_id    uuid REFERENCES product(id),
  kind          text NOT NULL CHECK (kind IN ('photo','audio','generated_image')),
  storage_key   text NOT NULL,               -- '<business_id>/uploads/<uuid>' server-generated
  mime          text NOT NULL,
  size_bytes    bigint NOT NULL CHECK (size_bytes > 0),
  sha256        text CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  status        text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','verified','rejected')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (storage_key)
);
CREATE INDEX media_business_ix ON media (business_id, created_at DESC);

CREATE TABLE job (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id     uuid NOT NULL REFERENCES business(id),
  kind            text NOT NULL CHECK (kind IN ('product_from_photo','product_from_voice','post_generate','claim_check','customer_reply','eval_run','proposal_revalidate')),
  status          text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','awaiting_approval','succeeded','blocked','failed','cancelled')),
  created_by      uuid REFERENCES app_user(id),
  idempotency_key text,
  progress_step   integer NOT NULL DEFAULT 0,
  progress_total  integer NOT NULL DEFAULT 0,
  result_ref      jsonb,                      -- {"type":"proposal","id":"<uuid>","version":1}
  error_code      text,
  error_message   text,                       -- user-readable, no secrets
  model_calls     integer NOT NULL DEFAULT 0 CHECK (model_calls >= 0),
  max_model_calls integer NOT NULL DEFAULT 8 CHECK (max_model_calls >= 0),
  checkpoint_ref  text,                       -- LangGraph checkpoint thread id
  created_at      timestamptz NOT NULL DEFAULT now(),
  started_at      timestamptz,
  finished_at     timestamptz
);
CREATE INDEX job_business_ix ON job (business_id, created_at DESC);
CREATE UNIQUE INDEX job_idem_uq ON job (business_id, idempotency_key) WHERE idempotency_key IS NOT NULL;

CREATE TABLE job_event (                      -- sanitized trace; never raw reasoning
  id              bigserial PRIMARY KEY,
  business_id     uuid NOT NULL REFERENCES business(id),
  job_id          uuid NOT NULL REFERENCES job(id),
  seq             integer NOT NULL CHECK (seq >= 1),
  node            text NOT NULL,
  event           text NOT NULL CHECK (event IN ('step_started','step_finished','conflict_found','awaiting_approval','blocked','retry','done','error')),
  tool            text,
  redacted_input  jsonb,
  redacted_output jsonb,
  evidence_ids    uuid[] NOT NULL DEFAULT '{}',
  decision        text,
  retry           integer,
  duration_ms     integer CHECK (duration_ms >= 0),
  error_code      text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (job_id, seq)
);
CREATE INDEX job_event_business_ix ON job_event (business_id, job_id);

CREATE TABLE proposal (                       -- one row per version; AI output lives here until approved
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  root_id       uuid NOT NULL,                -- id of version 1; groups versions
  job_id        uuid REFERENCES job(id),
  type          text NOT NULL CHECK (type IN ('product_draft','product_create','product_update','post_publish','order_action','reply')),
  version       integer NOT NULL CHECK (version >= 1),
  payload       jsonb NOT NULL,               -- shape per type: docs/15-schema-and-formats.md section 6
  status        text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','pending','approved','rejected','invalidated','expired','executed')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (root_id, version)
);
CREATE INDEX proposal_business_ix ON proposal (business_id, type, status);

CREATE TABLE approval (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  proposal_id   uuid NOT NULL REFERENCES proposal(id),   -- the exact version row
  type          text NOT NULL CHECK (type IN ('product_create','product_update','post_publish','order_action','reply')),
  status        text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','expired','invalidated')),
  warnings      jsonb NOT NULL DEFAULT '[]'::jsonb,
  risk          text NOT NULL DEFAULT 'low' CHECK (risk IN ('low','medium','high')),
  side_effect   jsonb NOT NULL,               -- {"description": "...", "reversible": true}
  expires_at    timestamptz NOT NULL,
  decided_by    uuid REFERENCES app_user(id),
  decided_at    timestamptz,
  decision_reason text,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX approval_business_ix ON approval (business_id, status, created_at DESC);

CREATE TABLE execution (                      -- written only by the execution service
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id     uuid NOT NULL REFERENCES business(id),
  approval_id     uuid NOT NULL REFERENCES approval(id),
  idempotency_key text NOT NULL,
  status          text NOT NULL CHECK (status IN ('succeeded','failed')),
  result_ref      jsonb,
  error_code      text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (approval_id),
  UNIQUE (business_id, idempotency_key)
);

CREATE TABLE post (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  product_id    uuid NOT NULL REFERENCES product(id),
  channel       text NOT NULL CHECK (channel IN ('instagram','whatsapp_status','facebook','generic')),
  language      text NOT NULL CHECK (language IN ('en','hi','mr')),
  text          text NOT NULL CHECK (char_length(text) <= 4000),
  version       integer NOT NULL DEFAULT 1 CHECK (version >= 1),
  status        text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','checked','pending_approval','approved','exported')),
  provenance    jsonb NOT NULL,               -- {"model_id","prompt_version","generated_at","mode":"live|mock"}
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX post_business_ix ON post (business_id, product_id, status);

CREATE TABLE post_revision (
  post_id       uuid NOT NULL REFERENCES post(id),
  business_id   uuid NOT NULL REFERENCES business(id),
  version       integer NOT NULL CHECK (version >= 1),
  text          text NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (post_id, version)
);

CREATE TABLE claim (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  post_id       uuid NOT NULL REFERENCES post(id),
  post_version  integer NOT NULL CHECK (post_version >= 1),
  text          text NOT NULL,
  kind          text NOT NULL CHECK (kind IN ('fact','opinion')),
  verdict       text CHECK (verdict IN ('supported','contradicted','unverified')),   -- NULL until checked
  severity      text CHECK (severity IN ('low','medium','high')),
  repair_suggestion text,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX claim_post_ix ON claim (business_id, post_id, post_version);

CREATE TABLE evidence (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id    uuid NOT NULL REFERENCES business(id),
  claim_id       uuid REFERENCES claim(id),
  message_id     uuid,                         -- set when evidence supports a chat answer (FK added below)
  source_kind    text NOT NULL CHECK (source_kind IN ('business','product','variant','policy','order','transcript','media')),
  source_id      uuid NOT NULL,
  source_version integer NOT NULL CHECK (source_version >= 1),
  snapshot       jsonb NOT NULL,               -- redacted copy of the cited fact at check time
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX evidence_business_ix ON evidence (business_id, claim_id);

CREATE TABLE customer_account (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email         text NOT NULL UNIQUE CHECK (char_length(email) BETWEEN 3 AND 320),
  display_name  text NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120),
  password_hash bytea NOT NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE customer_auth_session (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_account_id uuid NOT NULL REFERENCES customer_account(id) ON DELETE CASCADE,
  token_hash          varchar(64) NOT NULL UNIQUE,
  created_at          timestamptz NOT NULL DEFAULT now(),
  expires_at          timestamptz NOT NULL,
  revoked_at          timestamptz
);
CREATE INDEX customer_auth_session_account_ix ON customer_auth_session (customer_account_id, expires_at);

CREATE TABLE public_session (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  customer_account_id uuid REFERENCES customer_account(id) ON DELETE CASCADE,
  token_hash    bytea,
  status        text NOT NULL DEFAULT 'open' CHECK (status IN ('open','escalated','closed','blocked')),
  ip_hash       text,                          -- salted hash, for rate limiting only
  created_at    timestamptz NOT NULL DEFAULT now(),
  expires_at    timestamptz NOT NULL
);
CREATE UNIQUE INDEX public_session_token_uq ON public_session (token_hash);
CREATE INDEX public_session_business_ix ON public_session (business_id, created_at DESC);

CREATE TABLE conversation (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id        uuid NOT NULL REFERENCES business(id),
  public_session_id  uuid NOT NULL REFERENCES public_session(id),
  status             text NOT NULL DEFAULT 'open' CHECK (status IN ('open','escalated','closed')),
  escalation_reason  text,
  source             text NOT NULL DEFAULT 'public' CHECK (source IN ('public','demo')),
  customer_label     text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (public_session_id)
);
CREATE INDEX conversation_business_ix ON conversation (business_id, status, updated_at DESC);

CREATE TABLE message (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id      uuid NOT NULL REFERENCES business(id),
  conversation_id  uuid NOT NULL REFERENCES conversation(id),
  role             text NOT NULL CHECK (role IN ('customer','assistant','owner','system')),
  body             text NOT NULL CHECK (char_length(body) <= 4000),
  evidence_ids     uuid[] NOT NULL DEFAULT '{}',
  read_by_owner_at timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX message_conversation_ix ON message (business_id, conversation_id, created_at);
ALTER TABLE evidence ADD CONSTRAINT evidence_message_fk FOREIGN KEY (message_id) REFERENCES message(id);

CREATE TABLE public_rate_limit_bucket (
  key_hash     varchar(64) PRIMARY KEY,
  window_start timestamptz NOT NULL,
  request_count integer NOT NULL CHECK (request_count > 0)
);
CREATE INDEX public_rate_limit_window_ix ON public_rate_limit_bucket (window_start);

CREATE TABLE customer_order (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id       uuid NOT NULL REFERENCES business(id),
  public_session_id uuid REFERENCES public_session(id),
  status            text NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','AWAITING_PAYMENT','PAID','FULFILLED','CANCELLED','FAILED')),
  customer_name     text NOT NULL CHECK (char_length(customer_name) BETWEEN 1 AND 120),
  delivery_note     text CHECK (char_length(delivery_note) <= 500),
  total_inr         numeric(12,2) NOT NULL CHECK (total_inr >= 0),
  payment_method    text CHECK (payment_method IN ('cash','upi','bank','other')),
  payment_reference text,
  payment_recorded_by uuid REFERENCES app_user(id),   -- owner-recorded; never an agent
  idempotency_key   text NOT NULL,
  version           integer NOT NULL DEFAULT 1,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (business_id, idempotency_key)
);
CREATE INDEX customer_order_business_ix ON customer_order (business_id, status, created_at DESC);

CREATE TABLE order_item (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id     uuid NOT NULL REFERENCES business(id),
  order_id        uuid NOT NULL REFERENCES customer_order(id),
  variant_id      uuid NOT NULL REFERENCES product_variant(id),
  qty             integer NOT NULL CHECK (qty > 0 AND qty <= 100),
  unit_price_inr  numeric(12,2) NOT NULL CHECK (unit_price_inr >= 0)   -- copied from the database at order time
);
CREATE INDEX order_item_order_ix ON order_item (business_id, order_id);

CREATE TABLE order_status_history (
  id            bigserial PRIMARY KEY,
  business_id   uuid NOT NULL REFERENCES business(id),
  order_id      uuid NOT NULL REFERENCES customer_order(id),
  from_status   text,
  to_status     text NOT NULL,
  actor_type    text NOT NULL CHECK (actor_type IN ('user','system','execution_service')),
  actor_id      text,
  detail        jsonb NOT NULL DEFAULT '{}'::jsonb,
  at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX order_status_history_ix ON order_status_history (business_id, order_id, at);

CREATE TABLE audit_event (                    -- append-only
  id            bigserial PRIMARY KEY,
  business_id   uuid NOT NULL REFERENCES business(id),
  actor_type    text NOT NULL CHECK (actor_type IN ('user','agent','system','public')),
  actor_id      text,
  action        text NOT NULL,                -- dotted: 'product.price_changed', 'approval.approved', 'agent.action_denied'
  entity_type   text NOT NULL,
  entity_id     text,
  detail        jsonb NOT NULL DEFAULT '{}'::jsonb,   -- redacted
  request_id    text,
  at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_event_business_ix ON audit_event (business_id, at DESC);
CREATE INDEX audit_event_entity_ix ON audit_event (business_id, entity_type, entity_id);

CREATE FUNCTION audit_event_block_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_event is append-only';
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER audit_event_no_update BEFORE UPDATE OR DELETE ON audit_event
  FOR EACH ROW EXECUTE FUNCTION audit_event_block_mutation();

CREATE TABLE guardrail_event (
  id            bigserial PRIMARY KEY,
  business_id   uuid NOT NULL REFERENCES business(id),
  job_id        uuid REFERENCES job(id),
  node          text NOT NULL,
  rule          text NOT NULL,                -- e.g. 'claim.unverified', 'policy.payment_write_denied', 'injection.suspected'
  decision      text NOT NULL CHECK (decision IN ('allow','require_approval','deny','block','escalate')),
  evidence_ids  uuid[] NOT NULL DEFAULT '{}',
  detail        jsonb NOT NULL DEFAULT '{}'::jsonb,
  at            timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX guardrail_event_business_ix ON guardrail_event (business_id, at DESC);

CREATE TABLE idempotency_key (
  business_id     uuid NOT NULL REFERENCES business(id),
  endpoint        text NOT NULL,              -- 'POST /v1/products/{id}/stock'
  key             text NOT NULL CHECK (key ~ '^[A-Za-z0-9_-]{8,64}$'),
  request_hash    bytea NOT NULL,             -- sha-256 of canonical request body
  response_status integer NOT NULL,
  response_body   jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (business_id, endpoint, key)
);

CREATE TABLE model_usage (
  id             bigserial PRIMARY KEY,
  business_id    uuid NOT NULL REFERENCES business(id),
  job_id         uuid REFERENCES job(id),
  node           text NOT NULL,
  model_id       text NOT NULL,
  mode           text NOT NULL CHECK (mode IN ('live','mock')),
  latency_ms     integer NOT NULL CHECK (latency_ms >= 0),
  input_tokens   integer,
  output_tokens  integer,
  media_units    numeric(12,3),
  est_cost_usd   numeric(10,6),                -- estimate; label as estimate in UI and reports
  at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX model_usage_business_ix ON model_usage (business_id, at DESC);

CREATE TABLE eval_run (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  mode          text NOT NULL CHECK (mode IN ('mock','live')),
  split         text NOT NULL CHECK (split IN ('dev','heldout')),
  system        text NOT NULL CHECK (system IN ('A','B','C')),
  status        text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','succeeded','failed')),
  model_ids     jsonb NOT NULL DEFAULT '{}'::jsonb,
  metrics       jsonb,
  usage         jsonb,
  started_at    timestamptz,
  finished_at   timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX eval_run_business_ix ON eval_run (business_id, created_at DESC);

CREATE TABLE eval_case_result (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id   uuid NOT NULL REFERENCES business(id),
  run_id        uuid NOT NULL REFERENCES eval_run(id),
  case_id       text NOT NULL,                 -- evals/dataset/cases.jsonl id
  decision      text NOT NULL,
  expected      jsonb NOT NULL,
  passed        boolean NOT NULL,
  detail        jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX eval_case_result_run_ix ON eval_case_result (business_id, run_id);
