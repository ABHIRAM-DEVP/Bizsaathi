# BizSaathi 2.0 — Advanced Agentic AI Architecture for the Meta Global AI Developer Hackathon

My recommendation is to keep BizSaathi, but evolve it from an AI marketing assistant into a verifiable, multimodal business operations system for small sellers.

The technical depth should come from how the system plans and executes workflows, uses multiple Meta models, verifies evidence, recovers from failures, protects customer data, and requests human approval—not merely from having 15 agents.

A critical hackathon constraint: your supplied guide explicitly discourages basic RAG applications and simple image analyzers. Therefore, BizSaathi should use database-grounded tools, multimodal perception, agentic planning, deterministic verification, controlled execution, and measurable evaluations. RAG can support selected workflows, but it must not be the core innovation.

## 1. Problem statement

Millions of small businesses operate through product photographs, voice notes, social posts, messaging apps, handwritten stock records, and informal customer conversations. A seller may know their products extremely well but lack the time, technical skills, and staff to manage product catalogues, create accurate marketing content, track inventory, respond to customers, and process orders consistently.

Existing AI tools can generate captions or answer questions, but generation alone does not guarantee that a product's price is correct, the advertised stock exists, a marketing claim is supported, or an order can actually be fulfilled. These failures can lead to customer disputes, lost sales, misleading promotions, and additional work for the seller.

How might we build an AI-powered business operations co-pilot that transforms a seller's photographs, voice instructions, product records, and customer conversations into verified, actionable workflows—while keeping the seller in control of consequential actions?

## 2. Proposed solution

[Best Instagram Automation Tools India 2026: Small Business | QuickDM](https://images.openai.com/static-rsc-4/-drD9KxEUsEpJMtlBUTzSssmXWSl2xEMQStdIsYsPgD9y45He_SWSbI2DRENAz5HLwQDNa_DRW4Udal9AvKJAIwea7sDVfwQqgt8dDVRgQCKantAcLIWkHdeQfBD1LnzjVp7BEruD0XwLAE_aiwFF-upI968AIDHfTymCnn8DB4?purpose=inline)

A. Multimodal product intelligence

The seller uploads a product photo, speaks a description in Hindi, Marathi, or English, and optionally supplies a price. BizSaathi extracts candidate attributes, detects inconsistencies, and creates a structured draft for review.

[IKM Garuda](https://images.openai.com/static-rsc-4/NTKd50b5aDDVTWFnqfeMjl7zwAzAWxDb6ik5r4D4nb2B2pjH38GMeQNq7UtG1ul86p8Etenvkj2PYosX4A359KOxNaSJCblru7WeNQkTsDfnNnFN9XCYWXg5vRdu2d4QEG6WUCIFjO-00gWCJAj36H2xzH6btqWA_s0SxyKXVo0?purpose=inline)

B. Evidence-backed content production

Generate platform-specific content, link factual claims to product and policy records, check image-caption consistency, and pause unsupported claims for correction or approval.

[Emprendedores y tiendas de barrio pueden usar la tecnología para ganar más dinero; así pueden hacerlo](https://images.openai.com/static-rsc-4/1Jg1oeELL86UHtIeZsnU6qlRfzOHnZsaNJpQaN6mZ7Q9p_5gteKfMlSefEQ-VI52MCQhnPFicrrvGxQn86AcGDHiRP380-TsLFRGOr0NSmzmlfai3fhDGREV7qIlh1RYxBIeG_H4jhraJKdhGhg0m5rPGKBLK9oJ73wKMKbPDfc?purpose=inline)

C. Customer-to-order operations

Answer questions using live product, stock, and policy tools; create order drafts; check fulfilment constraints; and escalate uncertain cases to the seller.

[Driving Global Success | Advanced Professional Management | Cafe24](https://images.openai.com/static-rsc-4/3WLtSx5bMj-upVDD2xpszY6HMW-wP9W3La3ev0xIgDq-wU2I4DWKuRfvtYKG0KjZhkxMIhRVXAja4HayBoLBNYSAVcdkX_Mei3c_OGDEl_vGPsWfLVev-7EjM5ewqd-fiys3r5yFyHVveWA9m0TYFd5DpVXBG87loVYDqftUv9o?purpose=inline)

D. Verifiable execution

Every workflow has typed outputs, evidence references, risk checks, a persistent state, an audit trail, and explicit human approval before external publishing or other consequential actions.

The differentiator is a closed-loop business workflow: perceive → plan → execute tools → verify → repair or escalate → request approval → execute → measure the outcome.

## 3. The 15-agent pipeline

Build a supervised, stateful multi-agent graph using LangGraph. Fifteen agents provide technical depth, but they should not mean fifteen separate expensive model calls. Each is a specialized node with a defined input, output, permissions, and exit condition. Some nodes can run deterministically, some can run in parallel, and some invoke Meta models.

Stage A — Intake and planning

Agents 01–03 · Understand the seller's goal and create an executable plan

01

Intent and Task Planner

Converts requests such as "launch this new saree" into a typed task graph with dependencies, budgets, deadlines, and approval requirements. Uses Muse Spark.

Output: `TaskPlan` with bounded steps and allowed tools.

02

Multimodal Intake Agent

Coordinates photo uploads, voice notes, text instructions, and existing product records. Uses Muse Voice Transcribe for audio and Muse Spark for image/text interpretation.

Output: a normalized, timestamped input bundle with provenance.

03

Context and Memory Agent

Retrieves the seller's saved preferences, relevant product records, previous approved content, and current store policies. It distinguishes current facts from historical context.

Output: scoped context with source IDs and freshness.

Stage B — Perception and business intelligence

Agents 04–06 · Convert unstructured inputs into verified candidate data

04

Visual Product Perception Agent

Uses SAM 3.1 to segment the product from its surroundings, then Muse Spark to interpret visual attributes and flag ambiguity. Muse Image can optionally generate or edit promotional imagery.

Output: candidate attributes, segmentation mask, and uncertainty flags.

05

Voice and Instruction Interpreter

Extracts the seller's intended name, price, size, material, quantity, and constraints from transcribed speech. Checks whether speech-derived values conflict with the visual or database evidence.

Output: structured fields with transcript spans and confidence indicators.

06

Catalogue Reconciliation Agent

Compares extracted fields with existing SKUs, prices, stock, variants, and duplicate listings. It proposes updates but cannot silently overwrite authoritative business records.

Output: proposed product changes and explicit conflict records.

Stage C — Content and customer intelligence

Agents 07–09 · Produce useful work grounded in actual store data

07

Content Strategy Agent

Chooses the audience, objective, tone, language, and content format. Uses approved seller preferences and prior performance data rather than inventing audience insights.

Output: a content brief with constraints.

08

Multimodal Content Production Agent

Produces platform-ready captions, product descriptions, calls to action, and optional promotional visuals. Uses Muse Spark for writing and Muse Image for image generation or editing.

Output: versioned content drafts with structured metadata.

09

Customer Intent and Commerce Agent

Interprets customer questions, identifies purchase intent, checks stock and policies through read-only tools, and creates order drafts. It cannot invent discounts or confirm payments.

Output: an answer with evidence or a structured escalation.

Stage D — Verification and recovery

Agents 10–12 · Test the work rather than trusting the generator

10

Evidence and Claim Verification Agent

Checks factual claims against authoritative product and policy records. Classifies claims as supported, contradicted, or unverified, with evidence IDs and source versions.

Output: claim-by-claim verdicts and repair instructions.

11

Independent Multimodal Critic

Compares the image, caption, spoken instructions, and structured product fields for mismatches such as a blue item described as green. Uses a separate verification prompt or model configuration from the writer.

Output: mismatch list, severity, and required corrections.

12

Repair and Recovery Agent

Diagnoses failed checks and chooses a bounded action: regenerate a field, re-query the database, ask the owner a question, or stop. Limits retries and prevents infinite agent loops.

Output: corrected candidate or an explicit blocked state.

Stage E — Safe execution and learning

Agents 13–15 · Control side effects and learn from actual outcomes

13

Policy and Permission Agent

Evaluates the requested action against deterministic rules, shop permissions, approval requirements, and risk thresholds. It can veto a model recommendation; it cannot grant itself permissions.

Output: allow, require approval, or deny.

14

Human Approval and Action Agent

Presents a before-and-after diff, evidence, warnings, and proposed side effects. After an authenticated owner approves the specific action, a separate execution service performs only the permitted operation.

Output: approval record, execution receipt, or failure state.

15

Evaluation and Learning Agent

Measures corrections, escalation accuracy, verification failures, latency, and actual business outcomes. Suggests future policy or prompt changes, but never automatically changes production policies based on unverified feedback.

Output: evaluation events, scorecards, and proposed improvements.

### How the agents work together

This is a conditional graph, not a rigid chain in which every node must run every time.


Important implementation detail: agents 10, 11, and 13 are different controls. The evidence verifier checks facts; the multimodal critic checks cross-modal consistency; the policy gate enforces permissions and action rules. One language-model call should not be allowed to certify its own output and execute it without independent controls.

For a customer question, skip photo processing and content generation. Route directly through intent detection, product and policy tools, evidence verification, and the reply policy. That keeps the system efficient despite the 15-node architecture.

## 4. Meta AI model strategy

Use Meta models for the AI capabilities, and ordinary software components for permissions, persistence, validation, queues, and deterministic business rules.

The official Meta documentation lists Muse Spark for agentic reasoning, tool use, multimodal understanding and structured outputs; Muse Image for image generation/editing; Muse Voice Transcribe for speech-to-text; and SAM 3.1 for segmentation.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.meta.ai\&sz=32)

Meta Model API+1



[Neural Agent Network: A Modular Architecture for Emergent Superintelligence | by Lior Gd | Medium](https://images.openai.com/static-rsc-4/iYCtRgohTgpcZcuRcooJsVz-93TIR4wnDQJ_1ARXDr4hhOIbdv8ee2_DvvWPIJOiTW1ARB-lSvQpUkSgmoEu4DByFtiC8jpWz1gVZJoX-yVPnqmFYFAu5c_0u6sMuMNJNUbjOvKHhnwA8cnGY5rzMPtq5MT8LTQpw2tfvv7VBhE?purpose=inline)

Muse Spark — primary reasoning model

Core model

Agents 01, 03, 05–13, and selected verification tasks

Planning, tool calling, structured output, customer intent, claim analysis, repair decisions, and multimodal interpretation.

[Official model page](https://dev.meta.ai/models/muse-spark?utm_source=chatgpt.com)

[Buy Grey Understated Drape Handloom Saree | KALKI Fashion India](https://images.openai.com/static-rsc-4/gmdrK1qZqnS9b3VHZgK_uk32GAC6yapzyMu8rQZBHejRSyX-tZkjzBiSg228DQDFH9xWXYD2Yx6ursudzfBQyQ2QoCzXEOhhDDprAxJ4TN1XZD_yGUAGRlGQzF8VEkAgNfevbnOFHUFu7YLddgM1WGQMIlPk-ShmYhTHAzXZPCs?purpose=inline)

Muse Image — visual creation

Agent 08, optional image-repair workflow

Generate or edit promotional visuals. Preserve the actual product's identity; do not let a generated image silently change its colour, pattern, or other sale-relevant attributes.

[Official model page](https://dev.meta.ai/models/muse-image?utm_source=chatgpt.com)

[Voice Recording UI by Parnian Sabet on Dribbble](https://images.openai.com/static-rsc-4/RBxKc6Hl1A_Bjpw7_U-ykP8ENm_451XbIMeyLexyHBIPepXwovq1lIUDoKH7sNW2rKbiIdoxO02yfTOA9Ou0prQs9rkNti6pRm9Plac7qbg8ZwoUpjI4Y8Xjp3_Qh_uCrGH3d-8mWMvbq6nOBPmgnYaFnM1H7cxOPt0sgo0lnM8?purpose=inline)

Muse Voice Transcribe — speech understanding

Agent 02 and Agent 05

Transcribe seller voice notes, then pass the transcript to Muse Spark for semantic interpretation. Test Hindi, Marathi, English, and code-switching on actual examples.

[Official model page](https://dev.meta.ai/models/muse-voice-transcribe?utm_source=chatgpt.com)

[AdaFold: Adapting Folding Trajectories of Cloths via Feedback-loop Manipulation](https://images.openai.com/static-rsc-4/d_u9eZhdH4F7C5uZ8x95QuMTuQFq46CQ9N8Rvcw7IOMs4owG68yeM8gi2dDc3d6DhkzkpWfIeeqNSV18LYDZsWzIADWbm9LdAs_-PG9-1UnvDI_zINGY8zTzjgAOQnMyEge4J3jBWx_9pIcNOhvj_hJ3amVJtjYWxuHnpcpaWcE?purpose=inline)

SAM 3.1 — object segmentation

Agent 04

Identify and mask the target product for visual inspection or background-processing workflows. Segmentation alone does not establish a product's material, authenticity, or quality.

[Official model page](https://dev.meta.ai/models/sam-3-1?utm_source=chatgpt.com)

[Nvidia Backs Nscale at $14.6B as AI Data Center Race Heats Up | The Tech Buzz](https://images.openai.com/static-rsc-4/FkMf8FZpfzVTurUyXtMvQjd7oxNGEM27_DYOf89VzcLhi8vU3uTRpbsGCETJiApLK6wHBAjUwdIuBLTC-FTYUsAIz9W4U_vElxh9i9VMQSkql5NXaBBENC2LuapZdAXkkNLCqhnopSJVs9zJs9LPckbWTEnRJ0UYRsAXR8MRzfA?purpose=inline)

Muse Spark Open or Muse Glimmer — optional deployment track

Run a Meta open-weight model through a supported inference runtime or hosted inference provider. Use it for controlled experiments with cost, latency, or deployment constraints, not because every agent needs a different model.

[Official model catalogue](https://dev.meta.ai/docs/models?utm_source=chatgpt.com)

### Model selection rules

- Start with `muse-spark-1.3` for reasoning, subject to availability in your account.
- Use Muse Image only when image creation or editing is required.
- Use Muse Voice Transcribe for audio transcription rather than relying on an unverified audio capability.
- Use SAM 3.1 for masks and object geometry, not as the final product verifier.
- Treat a separate critic as independent verification logic, not guaranteed independence simply because you use a second prompt. Where feasible, evaluate a separate model configuration against known errors.
- Keep all model IDs and provider settings in server-side configuration, with `.env` used for credentials. Never expose API keys to the Next.js browser.

Open-model caveat: Muse Spark Open is a large model. Self-hosting it may be unrealistic for a solo developer under a short hackathon deadline. The primary demo should work through the Meta Model API; test open-weight deployment as a separate experiment if time and compute permit.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://dev.meta.ai\&sz=32)

Meta Model API+1



## 5. Do we need RAG? Which GenAI techniques are actually useful?

Yes, several advanced GenAI techniques are appropriate—but do not build a generic vector-search chatbot and call it agentic AI.

1\. Structured retrieval and evidence-linked generation

Must have

Retrieve product prices, stock, variants, and policies directly from PostgreSQL through typed tools. Every claim should include an evidence reference to a database row or versioned policy.

Example: "Green variant available" is allowed only if the current stock tool confirms it.

2\. Selective RAG for unstructured policies

Optional enhancement

If policies are long documents, retrieve relevant passages using PostgreSQL full-text search or `pgvector`. Attach passage IDs, document versions, and dates to the answer. A small retrieval layer is useful; it should support the agentic workflow rather than become the whole product.

Use structured SQL for prices and stock, not embeddings.

3\. Stateful planning and tool use

Must have

LangGraph stores the task state, routes between agents, retries bounded failures, pauses for approval, and resumes from a checkpoint. This is a concrete agentic capability, unlike a single prompt that describes a plan but never executes it.

4\. Multimodal consistency checking

Core differentiator

Cross-check the image, transcript, extracted attributes, database facts, and final caption. The system must detect conflicts and route them to repair or human review.

5\. Verifiable generation and constrained outputs

Must have

Use Pydantic schemas, deterministic business invariants, evidence references, separate verification stages, and explicit allow/deny/approval decisions. Unsupported claims must fail closed.

6\. Bounded self-repair

Advanced

If a check fails, the graph receives the specific mismatch and attempts a limited repair. After a small number of attempts, it escalates instead of continuing to spend tokens or hiding uncertainty.

7\. Evaluation-driven model routing

Advanced

Compare a fast configuration with a more capable one on your test set. Route ambiguous or high-risk cases to additional verification, while using fewer calls for simple tasks.

Other worthwhile techniques include prompt injection testing, tool-permission isolation, idempotent execution, provenance tracking, model output caching, and event-based observability.

Do not prioritize fine-tuning, a knowledge graph, multi-model debate, or reinforcement learning before the complete workflow works. These are optional research directions, not requirements for a technically strong project.

## 6. System architecture


### Architecture decisions

- API layer: FastAPI handles request validation, authentication, tenant scoping, and rate limits.
- Agent layer: LangGraph manages the state machine, conditional edges, retry limits, checkpoints, and human-in-the-loop pauses.
- Workers: Redis-backed jobs process image, audio, and post-generation tasks asynchronously. Stream progress through Server-Sent Events where useful.
- Database: PostgreSQL is the source of truth for products, stock, orders, approvals, and audit events. Use `pgvector` only if policy or historical-content retrieval benefits from semantic search.
- Object storage: Store uploaded product media and generated assets separately from relational data. Use signed upload URLs and short-lived signed download URLs.
- Observability: OpenTelemetry traces, structured logs, and per-agent latency, error, and model-usage metrics.
- Execution boundary: The model proposes actions. A server-side policy layer validates them, and an authenticated owner approves consequential actions before a narrowly scoped execution service runs.

For the hackathon, use a modular monolith plus a worker, not a dozen microservices. You can demonstrate sophisticated orchestration without creating unnecessary infrastructure overhead.

## 7. Complete BizSaathi API endpoint specification

Base path: `/v1`. The owner-facing APIs require authentication and shop-level authorization unless explicitly marked public or webhook-based. Agent nodes are internal services—not public endpoints.

The following preserves your earlier endpoint plan, organizes it by domain, and adds the supporting job, evidence, and evaluation routes needed for the advanced pipeline.

### A. Authentication, seller profile, and verification

| Method | Endpoint                        | Purpose                                           |
| ------ | ------------------------------- | ------------------------------------------------- |
| POST   | `/auth/otp/send`                | Send seller login OTP                             |
| POST   | `/auth/otp/verify`              | Verify OTP and issue session                      |
| POST   | `/auth/refresh`                 | Refresh session credentials                       |
| POST   | `/auth/logout`                  | Revoke current session                            |
| GET    | `/me`                           | Get authenticated seller                          |
| PATCH  | `/me`                           | Update seller profile                             |
| GET    | `/business`                     | Get shop profile and settings                     |
| PATCH  | `/business`                     | Update policies and business settings             |
| PUT    | `/business/payment-details`     | Update payout details with step-up authentication |
| POST   | `/business/verification`        | Submit seller verification details                |
| GET    | `/business/verification/status` | Get verification status                           |

Seller identity and payout verification must use real, authorized verification processes if you launch them. Do not label a seller verified merely because the UI has a badge.

### B. Media, product catalogue, and stock

| Method | Endpoint               | Purpose                                |
| ------ | ---------------------- | -------------------------------------- |
| POST   | `/uploads`             | Create a signed upload URL             |
| POST   | `/products/from-photo` | Start photo-to-product workflow        |
| POST   | `/products/from-voice` | Start voice-to-product workflow        |
| GET    | `/products`            | List and filter products               |
| POST   | `/products`            | Create a product from a reviewed draft |
| GET    | `/products/{id}`       | Retrieve product details               |
| PATCH  | `/products/{id}`       | Update approved product fields         |
| DELETE | `/products/{id}`       | Archive or delete a product            |
| POST   | `/products/{id}/stock` | Record a stock adjustment              |
| GET    | `/jobs/{id}`           | Retrieve workflow status               |
| GET    | `/jobs/{id}/events`    | Stream workflow progress and events    |

Photo and voice endpoints should create asynchronous jobs. A client should receive a job ID immediately rather than waiting for every model call to finish.

### C. Content studio and claim verification

| Method | Endpoint                        | Purpose                                   |
| ------ | ------------------------------- | ----------------------------------------- |
| POST   | `/products/{id}/posts/generate` | Generate content drafts                   |
| GET    | `/posts`                        | List drafts and published-content records |
| GET    | `/posts/{id}`                   | Retrieve a post and its provenance        |
| PATCH  | `/posts/{id}`                   | Edit a draft                              |
| POST   | `/posts/{id}/claim-check`       | Verify claims in submitted content        |
| POST   | `/posts/{id}/submit`            | Submit content for approval               |
| POST   | `/posts/{id}/share-status`      | Record per-channel sharing status         |
| GET    | `/posts/{id}/export`            | Export approved content and media         |

The claim-check response should include the claim, verdict, evidence IDs, severity, and repair suggestions. The API should not return just an unqualified `safe: true`.

### D. Approvals and execution

| Method | Endpoint                  | Purpose                                             |
| ------ | ------------------------- | --------------------------------------------------- |
| GET    | `/approvals`              | List pending approvals, optionally filtered by type |
| GET    | `/approvals/{id}`         | Retrieve proposal, evidence, and risk details       |
| POST   | `/approvals/{id}/approve` | Approve the specific proposed action                |
| POST   | `/approvals/{id}/reject`  | Reject a proposed action                            |
| POST   | `/approvals/{id}/edit`    | Edit a proposal before revalidation                 |

Approval must bind to a specific version of a proposal. If the content or requested action changes after approval, invalidate the old approval and run the necessary checks again.

### E. Customer-facing store and chat

These are public endpoints, so apply rate limits, abuse controls, opaque session identifiers, and server-side store scoping.

| Method | Endpoint                                    | Purpose                              |
| ------ | ------------------------------------------- | ------------------------------------ |
| GET    | `/public/stores/{slug}`                     | Return public store details          |
| POST   | `/public/stores/{slug}/sessions`            | Start an anonymous chat session      |
| POST   | `/public/sessions/{id}/messages`            | Submit a customer message            |
| GET    | `/public/sessions/{id}/stream`              | Stream replies and escalation status |
| POST   | `/public/sessions/{id}/verify-phone/send`   | Request an order-time OTP            |
| POST   | `/public/sessions/{id}/verify-phone/verify` | Verify phone possession              |
| POST   | `/public/sessions/{id}/order`               | Create an order draft                |
| GET    | `/widget.js`                                | Serve the embeddable chat loader     |

The customer can browse and ask questions without an account. Only collect order information when necessary, with a clear explanation of its use and appropriate consent.

### F. Owner inbox and customer management

| Method | Endpoint                    | Purpose                                         |
| ------ | --------------------------- | ----------------------------------------------- |
| GET    | `/conversations`            | List customer conversations                     |
| GET    | `/conversations/{id}`       | Retrieve a conversation                         |
| POST   | `/conversations/{id}/reply` | Send an owner-approved reply                    |
| POST   | `/conversations/{id}/block` | Block abusive sessions or identifiers           |
| GET    | `/customers/{id}`           | Retrieve the owner's authorized customer record |

Keep personally identifying data out of model prompts wherever possible. The owner-facing API can resolve a customer record through a protected identifier without exposing phone numbers or addresses to agents that do not need them.

### G. Orders and payments

| Method | Endpoint                       | Purpose                        |
| ------ | ------------------------------ | ------------------------------ |
| GET    | `/orders`                      | List orders                    |
| GET    | `/orders/{id}`                 | Retrieve order details         |
| POST   | `/orders/{id}/remind`          | Send an authorized reminder    |
| POST   | `/orders/{id}/confirm-payment` | Record owner-confirmed payment |
| POST   | `/orders/{id}/ship`            | Record dispatch or shipment    |
| POST   | `/payments/link`               | Create a payment-link request  |

Use an explicit order state machine, such as `DRAFT → AWAITING_PAYMENT → PAID → FULFILLED`, with additional cancellation and failure states. Payment confirmation must be backed by the payment provider or a clearly defined owner-confirmation process. Never let the language model write payment status directly.

### H. Trust, safety, disputes, and audit

| Method | Endpoint                 | Purpose                                    |
| ------ | ------------------------ | ------------------------------------------ |
| GET    | `/audit-log`             | Inspect authorized audit records           |
| GET    | `/guardrail/events`      | Review safety and verification decisions   |
| POST   | `/reports`               | Report problematic content or interactions |
| POST   | `/disputes`              | Open a dispute                             |
| GET    | `/disputes`              | List authorized disputes                   |
| POST   | `/disputes/{id}/respond` | Submit a dispute response                  |

### I. Dashboard, channel adapters, notifications, and model configuration

| Method | Endpoint                   | Purpose                                   |
| ------ | -------------------------- | ----------------------------------------- |
| GET    | `/dashboard`               | Metrics and recommended next step         |
| GET    | `/channels`                | List available and connected channels     |
| POST   | `/channels/{type}/connect` | Start a supported channel-connection flow |
| POST   | `/push/subscribe`          | Register a push subscription              |
| GET    | `/notifications`           | List notifications                        |
| POST   | `/webhooks/whatsapp`       | Receive WhatsApp webhook events           |
| POST   | `/webhooks/instagram`      | Receive Instagram webhook events          |
| POST   | `/webhooks/facebook`       | Receive Facebook webhook events           |

The three social webhooks are future integrations. Do not present them as working until the actual account connection, provider verification, webhook signatures, and message exchange have been implemented and tested.

### J. Agent observability and evaluation extensions

These are recommended additions for the advanced pipeline, beyond the earlier API list.

| Method | Endpoint                 | Purpose                                           |
| ------ | ------------------------ | ------------------------------------------------- |
| GET    | `/jobs/{id}/trace`       | Retrieve a sanitized execution trace              |
| GET    | `/evidence/{id}`         | Retrieve an authorized evidence record            |
| GET    | `/evaluations/runs`      | List evaluation runs                              |
| POST   | `/evaluations/runs`      | Start an evaluation suite                         |
| GET    | `/evaluations/runs/{id}` | Retrieve scores and failure cases                 |
| GET    | `/metrics/agents`        | Read authorized agent latency and outcome metrics |

Do not expose raw internal reasoning or private chain-of-thought in traces. Store observable events instead: selected tools, inputs and outputs after redaction, evidence references, decisions, retries, approvals, durations, and error codes.

This produces a broad API surface, but you do not need to implement every route for the hackathon. Prioritize the product workflow, approval flow, and evidence trail first.

## 8. Technology stack

Frontend

Next.js, React, TypeScript, Tailwind CSS

Owner dashboard, product studio, approvals, inbox, PWA and public chat widget.

Backend

Python 3.12+, FastAPI, Pydantic

Typed REST APIs, request validation, authentication, tenant enforcement.

Agent orchestration

LangGraph

Conditional graph routing, persistent checkpoints, bounded retries, human approval interrupts.

AI models

Meta Model API

Muse Spark, Muse Image, Muse Voice Transcribe and SAM 3.1, as applicable.

Database

PostgreSQL + pgvector

Authoritative product/order data, policies, conversations, evidence metadata and optional semantic retrieval.

Jobs and cache

Redis + worker process

Async workflows, rate limits, short-lived caching, progress events and retry scheduling.

Media

S3-compatible object storage

Product photos, audio uploads, generated images, signed URLs and media metadata.

Security

JWT/session cookies, RBAC, tenant scoping, KMS where available

Authentication, action authorization, secrets handling, PII minimization and audit controls.

Observability

OpenTelemetry + structured logs

Agent spans, tool timing, model usage, retry counts and failure diagnosis.

Testing and CI

pytest, HTTPX, GitHub Actions

Unit/integration tests, workflow replay, adversarial tests and evaluation gates.

Deployment

Docker Compose initially

API, worker, PostgreSQL, Redis, and frontend; managed infrastructure later.

Keep the AI stack Meta-first. Libraries such as LangGraph, Pydantic, PostgreSQL, Redis, and OpenTelemetry are supporting infrastructure rather than competing AI models.

## 9. Security and reliability requirements

These are essential to make the advanced design credible.

1. Tenant isolation: Every business-owned database record is scoped to the authenticated business. Test cross-tenant access explicitly; PostgreSQL row-level security can provide an additional boundary.
2. Least privilege: Customer-facing agents have read-only product tools and narrowly scoped order-draft tools. No agent receives unrestricted SQL or payment-write access.
3. Prompt injection resistance: Treat customer messages, uploaded text, and retrieved documents as untrusted input. Validate tool arguments and enforce permissions outside the model.
4. Evidence provenance: Attach product IDs, stock versions, policy versions, and source spans to factual claims. Missing evidence means block or escalate.
5. Safe retries: Use idempotency keys for order creation, approvals, notifications, and other side effects. Retry transient failures without duplicating an action.
6. Privacy: Minimize personal data in prompts, encrypt sensitive records, restrict access, and define retention and deletion policies.
7. Secret handling: Store API credentials in server-side environment configuration for the MVP, exclude `.env` from Git, and commit only `.env.example`. Never send keys to frontend JavaScript.
8. Failure handling: Define timeouts, bounded retries, model-unavailable states, and a safe fallback to manual review. A fallback model must not bypass the same safety checks.

## 10. Evaluation: how to prove the agents are better

A technically advanced demo should show not only that the system generates content, but that it detects mistakes and prevents unsafe actions.

Create a small, hand-labelled test dataset covering product photos, seller voice notes, price and stock conflicts, unsupported marketing claims, prompt injection, ambiguous customer questions, and order-state violations.

## Evaluation scorecard

Target metrics to measure—not claimed results.

Evidence coverage

Percentage of factual claims with valid supporting evidence.

Claim verification

Precision and recall for unsupported or contradicted claims.

Multimodal consistency

Accuracy detecting mismatches between image, voice, catalogue and caption.

Escalation quality

Percentage of cases escalated correctly, plus missed escalations.

Tool safety

Unauthorized actions successfully blocked in adversarial tests.

Workflow reliability

Successful completion rate, duplicate side effects and recovery rate.

Performance and cost

Median/p95 latency, model calls and cost per completed workflow.

### The experiment that makes the project stand out

Compare three systems using the same held-out cases:

- Baseline A: One Muse Spark call generates a product listing or answer.
- Baseline B: Muse Spark with structured database tools and evidence references.
- BizSaathi: The full agent graph with independent verification, repair, policy enforcement, and human approval.

Measure quality, false approvals, missed escalations, latency, and cost. Report the actual results, including cases where the multi-agent approach performs worse.

This is much more defensible than claiming that using 15 agents automatically improves accuracy.

## 11. What to build between October 27 and November 4

For a solo developer, the following order gives you the best chance of finishing a coherent, demonstrable system.

Phase 1 — October 27–28: Foundations

Build the FastAPI backend, PostgreSQL schema, Meta Model API adapter, upload flow, and the first three agent nodes. Implement photo and voice ingestion with a persistent job record.

Phase 2 — October 29–30: Multimodal intelligence

Add SAM 3.1 segmentation, Muse Voice Transcribe, catalogue reconciliation, and Muse Spark content generation. Demonstrate how conflicting price or colour information is handled.

Phase 3 — October 31–November 1: Verification

Implement evidence references, the independent critic, deterministic policy checks, bounded repair, approval checkpoints, and audit events.

Phase 4 — November 2: Customer and order flow

Add the public store chat, grounded answers, escalation to the owner, and an order draft. Keep payment handling simulated or use a properly configured payment provider.

Phase 5 — November 3–4: Testing and submission

Run the evaluation set, fix critical failures, deploy the demo, record the three-minute video, document what was built during the hackathon, and submit before the official deadline.

Keep WhatsApp, Instagram, Facebook, real SMS verification, seller KYC integrations, fine-tuning, and open-weight GPU deployment outside the critical path unless the core workflow is already complete.

## 12. The three-minute demo

## 0:00

30 sec

The real-world problem

Show a seller uploading a handloom product photo and speaking a mixed-language voice note. The system extracts candidate details and displays its plan.

## 0:30

45 sec

Multimodal intelligence

Show segmentation, structured catalogue creation, and a deliberate mismatch between the spoken price and existing product data. The workflow flags the conflict rather than silently choosing a value.

## 1:15

45 sec

Verifiable agents

Generate a caption with an unsupported claim. Show the claim verifier rejecting it, the repair step proposing a correction, and the evidence that supports the revised wording.

## 2:00

35 sec

Human-controlled execution

A customer asks an ambiguous stock or delivery question. The assistant checks the available facts, escalates the uncertainty, and waits for the seller's response or approval.

## 2:35

25 sec

Technical proof

Show the trace, evidence references, blocked action, and evaluation scorecard. Explain what is implemented and what remains planned.

## 13. Final recommendation

Build BizSaathi as a multimodal, evidence-grounded, human-supervised agentic operations platform for small sellers, with 15 specialized workflow nodes, Meta-first model usage, and a strict separation between model decisions and business execution.

The most important design choices are:

- Use Muse Spark for reasoning and tool orchestration, with Muse Image, Muse Voice Transcribe, and SAM 3.1 for their relevant tasks.&#x20;

  [image](https://www.google.com/s2/favicons?domain=https://dev.meta.ai\&sz=32)

  Meta Model API+1

- Use structured database tools as the source of truth, with selective RAG only for genuinely unstructured policies.

- Implement the verification, repair, and approval loop as real executable code.

- Keep the owner's approval queue, customer inbox, and dashboard in BizSaathi; customer-facing messaging channels can be added later through adapters.

- Keep credentials in `.env` on the server, not in the UI.

- Demonstrate measurable reliability and failure handling, not merely agent count or model names.

Your core innovation is not 15 agents. It is a system in which multimodal AI can perform useful business work, prove where its facts came from, detect its own failures, and stop before an unsafe action reaches a customer. That is the story I would build the hackathon submission around.
