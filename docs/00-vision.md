# 00 Vision

Human-owned. Edit this by hand; agents draft, you decide. Source material: docs/source/.

## Problem
Small sellers run on photos, voice notes, chat messages and handwritten stock. Generic AI can write captions but cannot guarantee a price is right, stock exists, a marketing claim is supported, or an order is fulfillable. Wrong answers cause disputes, lost sales and extra work.
How might we turn a seller's photos, voice instructions, product records and customer conversations into verified, actionable workflows while the seller stays in control of consequential actions?

## Users
- Primary: small business owner or independent seller (often voice-first, mixed Hindi/Marathi/English, mobile-first)
- Secondary: customer on the public storefront chat
- Also: the operator monitoring the demo; hackathon judges

## Solution in one paragraph
A closed loop: perceive -> plan -> execute tools -> verify -> repair or escalate -> request approval -> execute -> measure. Models interpret and draft. PostgreSQL stores confirmed facts. Deterministic validators and independent verification controls check the work. The seller approves anything consequential.

## Product principles
1. Database over model for prices, stock and confirmed facts.
2. Show uncertainty. AI suggestions look different from confirmed facts.
3. Fail closed: no evidence, no claim.
4. The seller approves; agents never confirm payments or publish alone.
5. Prove it: measured evals, honest limits.

## Scope classes (MVP / STRETCH / FUTURE)
| Class | Items |
|---|---|
| MVP | One Next.js web+PWA app; photo-to-product draft with seller confirmation; evidence-linked content generation with claim verification and repair; approval queue with audit trail; PostgreSQL source of truth; tenant isolation; server-side Meta adapter; mock + live eval harness; reproducible demo |
| MVP-next | Public store chat answering from verified records, with escalation; order draft |
| STRETCH | Voice-to-product (Muse Voice Transcribe); SAM 3.1 segmentation; Muse Image visuals; background jobs with Redis; pgvector policy retrieval; model routing experiments |
| FUTURE | Real WhatsApp/Instagram/Facebook webhooks and publishing; real payments; seller KYC; open-weight deployment (Muse open models); fine-tuning |

## Success metrics (measure, never claim before measuring; thresholds in evals/thresholds.yaml)
- Unauthorized actions blocked in adversarial tests (target 100%)
- Cross-tenant leaks (target 0)
- Evidence coverage of factual claims; false approvals; missed escalations (baseline first)
- Median and p95 workflow latency; cost per completed workflow (record actuals)

## Explicit limitations (keep updated, show in the demo)
- Nothing published to real social channels, no real payments, no KYC.
- Live model quality is only claimed from live eval runs.
- Hindi/Marathi/code-switching quality is unmeasured until tested on real samples.

## Constraints
Hackathon deadline (TODO verify exact date and time zone), limited credits (TODO verify amount and eligibility), team size TODO, local Windows + Docker Compose.
