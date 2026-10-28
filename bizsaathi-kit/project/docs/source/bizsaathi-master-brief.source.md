# BizSaathi - Master Project Brief (source, retyped from the user's message)

Status: source document supplied by the project owner. Edit only to record decisions. Derived docs: docs/00-vision.md through docs/13-demo-script.md. Companion source: bizsaathi-2.0-architecture.source.md. (Parts C and D: Part C prompts are in docs/prompts/PROMPTS-1-8.md; Part D rules are below.)

Project: BizSaathi, Agentic AI co-pilot for small sellers. Frontend requirement: one Next.js app supporting desktop/mobile web and an installable PWA. Approach: spec-first, evidence-based, phased, test-driven. Primary AI ecosystem: Meta AI models and APIs. Principle: plan first, verify assumptions, implement incrementally, never claim a feature works until tested.

# PART A - Master project brief

## Purpose
Multimodal, agentic AI business assistant: turns product photos and voice notes into structured listings, creates marketing content, answers customer questions from verified business data, and manages basic order workflows with human approval.

## Domain
Agentic AI, multimodal AI, small-business enablement, e-commerce operations, workflow orchestration, trustworthy AI.

## Vision
A polished, production-minded prototype giving small sellers useful AI without technical skill: reliable, evidence-grounded, auditable, safe for business-critical actions, usable on desktop and mobile.

## Users
Small business owners and independent sellers; voice-preferring or time-poor sellers; customers visiting a public storefront; administrators/operators monitoring the demo.

## Core problem
Sellers manually prepare listings, adapt marketing, answer repeated questions, keep prices and stock consistent. Generic chatbots can produce unsupported claims or wrong business information. Combine multimodal AI with structured data, independent validation and human approval.

## Frontend
Next.js App Router; strict TypeScript; one shared responsive web app and installable PWA; reusable components and design system; accessible mobile-first layouts; manifest, icons, install experience, service worker/offline behavior where appropriate; no separate frontend codebase for web and PWA.

## Backend
Python 3.12 (subject to verification); FastAPI; Pydantic; SQLAlchemy and Alembic; LangGraph for typed stateful workflows; PostgreSQL source of truth; Redis for cache/background work when justified; S3-compatible object storage; Docker Compose for local dev.

## AI models and integrations
Meta model APIs for multimodal understanding, reasoning, generation, transcription where supported; evaluate SAM 3.1 for segmentation. Verify model identifiers, inputs, authentication, response formats, rate limits and pricing from current official docs. Never invent an endpoint, model id or capability. Meta keys only on the server in env or managed secret store; never in frontend code, browser storage, logs or git.

## Agent architecture
Graph of typed workflow nodes, conditional routing, deterministic tools, validators and approval gates. Up to 15 logical stages; not every stage needs an LLM call.

## Core workflows
1. Product photo -> multimodal analysis -> structured draft -> seller confirmation.
2. Voice note -> transcription -> structured extraction -> seller confirmation.
3. Confirmed facts -> marketing content -> claim verification -> seller approval.
4. Customer question -> verified database lookup -> grounded answer or escalation.
5. Order request -> stock and policy validation -> order draft -> authorized confirmation.

## Trust and security
PostgreSQL is source of truth for prices, stock, confirmed facts. AI-generated information distinguishable from verified data. Claims traceable to evidence. Deterministic checks for business rules. Seller approval before external publishing or consequential actions. Agents cannot confirm payments, change payment status or bypass authorization. Tenant authorization on every backend operation. Minimize personal data sent to models. Audit trail for important decisions. Treat uploads, user instructions, customer messages and retrieved content as untrusted.

## Budget
Hackathon Meta API credits if available. Earlier information indicated $150; verify current amount and eligibility. Track usage, set spending limits, prefer a working affordable MVP.

## Team, deadline, deployment
Team: TODO confirm. Deadline: official hackathon deadline (verify exact date and time zone). Deployment: local Windows dev; Docker Compose; frontend and backend on compatible hosting; managed PostgreSQL and secure env config for a public demo if budget allows; HTTPS when deployed.

## Mandatory artifacts
AGENTS.md; CLAUDE.md; .claude/rules/; approved skills and subagents only; docs 00-vision, 01-architecture, 02-data-model, 03-ui, 04-test-strategy, 05-troubleshooting, PHASES; docs/tasks/; working justfile; .env.example; automated tests and AI evaluation dataset; reproducible README and demo instructions.

## Must-haves
1. One shared Next.js web and PWA frontend. 2. A working Meta-powered end-to-end product workflow. 3. Evidence-grounded AI, validation, seller approval and auditability.

## Not in MVP scope
1. Separate web and mobile frontend codebases. 2. Unverified claims of real social publishing, payment processing or business integrations. 3. Large-scale infrastructure, unnecessary microservices, unproven AI features.

## Unknowns policy
If the brief or repo does not establish a fact, write TODO or ASSUMPTION: and ask when it materially affects implementation. Do not invent repository contents, test results, model capabilities, integrations, deadlines or metrics.

# PART B - The 22 project definition fields

1. Requirements: functional (onboarding, product management, photo and voice input, content generation, customer messaging, approvals, basic orders); non-functional (security, reliability, responsiveness, accessibility, performance, maintainability, observability); API contracts, validation, error formats, loading/empty states, retry behavior; PWA install, caching, update behavior, offline limits; automated unit, integration, e2e, security and AI evaluation tests. Each requirement: unique ID, priority, phase, testable criterion. (docs/06-requirements.md)
2. Scope: MVP = seller workflow from product input to confirmed data, then verified marketing content and approval. Next = customer questions from verified records with escalation. Stretch = voice entry, segmentation, background jobs, customer order requests, more integrations. Classify every feature MVP, STRETCH or FUTURE.
3. Goal and method: technically defensible, high quality, spec-first, incremental; inspect repo before editing; architecture and acceptance criteria before coding; one vertical slice at a time; official docs for version-sensitive decisions; deterministic tools for deterministic rules; run tests after meaningful changes; explain trade-offs; never fabricate tests, deployments, API calls or benchmarks; keep it explainable in a technical interview.
4. Tech stack: Next.js App Router + TypeScript; accessible reusable UI; FastAPI; Pydantic; LangGraph; PostgreSQL; SQLAlchemy + Alembic; Redis when justified; S3-compatible storage; verified Meta APIs; SAM 3.1 if accessible; pytest, HTTPX, Playwright; Docker Compose; structured logs and OpenTelemetry where feasible; GitHub Actions and just. Verify versions first.
5. Vision: a dependable digital operations assistant, not a generic chatbot. Seller expresses intent naturally, gets useful work, understands what AI inferred, corrects mistakes, approves actions. Make uncertainty visible; preserve seller control.
6. Description: multimodal AI + structured business data + workflow orchestration + evidence tracking + deterministic policy checks + human approval. AI interprets and drafts; database stores confirmed facts; validators verify; the seller holds authority.
7. Outcomes: deployable web/PWA app; functional backend and documented contracts; at least one complete Meta-powered workflow; structured data model and migrations; approval and audit; reproducible dev environment; automated tests and labelled AI eval set; architecture docs, demo script and transparent limitations. Report results only after measuring.
8. Acceptance criteria: preconditions, user action, expected result, error/edge behavior, authorization, verification command or test, evidence the test passed. Given/When/Then. UI looking right is not completion.
9. Deploy target: local Windows; Docker Compose; production-like separate frontend and backend; HTTPS, secure secrets, health checks, migrations, per-environment config; public demo URL only after verified deployment. Web and PWA are one Next.js app.
10. Budget: use credits first after confirming validity; measure model calls, tokens/media where exposed, latency, estimated cost; avoid repeated calls for deterministic work; cache only where correctness and isolation are preserved; no paid services without approval; document expected and actual cost separately.
11. Deadline: the verified official deadline is the hard cutoff; reserve time for evaluation, deployment, recording, README, submission; freeze features before it.
12. Team size: TODO. For a solo developer, prefer a modular monolith and few services.
13. Tools: Git/GitHub; Claude Code; Python venv; Node and package manager; Docker Desktop; PostgreSQL client; API client; just; pytest and Playwright; Mermaid CLI if installed; official Meta docs. Verify installed tools. Do not install every suggested MCP server or skill.
14. Constraints: deadline; limited credits and variable latency; verify model availability; server-side secrets; AI can be wrong; tenant isolation; no unapproved external actions; PWA offline must not misrepresent server-backed operations; the demo must separate working features from mocks and plans.
15. Must-haves: polished responsive Next.js web + PWA; working Meta-powered workflow with validated structured outputs; approval and separation of suggestions from confirmed facts; PostgreSQL source of truth; secure server-side credentials; automated tests, AI evals and reproducible demo; clear error handling, audit and documented limitations.
16. Not in scope unless approved and implemented: React Native/native apps; real social publishing; real payment settlement or automatic payment confirmation; production identity verification or compliance claims; autonomous consequential actions; Kafka/Kubernetes/microservices for show; production-grade claims without tests.
17. Demo script (3 minutes): 0:00 problem; 0:25 multimodal input (photo, voice if supported); 0:55 data integrity (AI cannot silently invent price or stock); 1:25 trustworthy content (flag unsupported claim, repair); 2:00 customer workflow (answerable vs ambiguous question escalated); 2:30 technical proof (trace, audit log, tests, one real eval result). Only features built and tested in the event period; identify mocks. (docs/13-demo-script.md)
18. Risks and mitigation: Meta API unavailable -> verify early, adapter, labelled dev mock; hallucinated facts -> DB facts, schemas, evidence, confirmation; unsupported claims -> validation, bounded repair, approval; cross-tenant leakage -> server-side tenancy and negative tests; key leakage -> server secrets, .gitignore, secret scanning, log redaction; latency/cost -> measure, bound retries, safe caching, graceful failure; PWA offline confusion -> cache shell selectively and indicate connectivity needs; scope creep -> priorities and feature freeze; broken deployment -> health checks, migrations, env checks, tested fallback. (docs/12)
19. Timeline: confirm the deadline then schedule: repo audit and requirements; architecture, data model, UI flows; backend foundation and Meta smoke test; first complete product workflow; Next.js web/PWA interface; agent graph, evidence, approval, audit; customer workflow and optional voice/segmentation; tests, evals, deployment, demo. (docs/PHASES.md)
20. Milestones: M0 repo and environment verified; M1 requirements, architecture, acceptance approved; M2 backend, DB, Meta API verified; M3 end-to-end product workflow; M4 shared web/PWA interface; M5 verification, approval, audit tested; M6 customer workflow and selected stretch; M7 evaluation, deployment, docs, demo validated. Each with measurable exit criteria.
21. Dependencies: Meta account, key, credits, model access; Python and Node; PostgreSQL and optional Redis; object storage; hosting and deploy credentials; official docs; user decisions on scope. Keep a dependency register with owner, status, version, fallback. (docs/12)
22. Stakeholders: seller; customer; project owner/developer; hackathon judges; hosting and AI providers. Prioritize seller control, customer safety, transparency, accessibility, clear error recovery.
23. Assumptions register: id, description, why it matters, evidence, risk if wrong, validation method, owner, status. Never silently convert an assumption into a requirement or fact. (docs/12)

# PART D - Execution rules for all prompts

Repository integrity: inspect before editing; preserve unrelated changes; do not overwrite without understanding; never modify global kit files when adapting project config; use diffs.
Implementation discipline: one approved task at a time; read task and dependencies first; small testable changes; no speculative abstractions or unnecessary infrastructure; no silent scope expansion; ask before changing core architecture or product behavior.
Web and PWA discipline: one shared Next.js frontend; responsive reusable components; installation and offline are explicit requirements; cache only appropriate resources; never cache sensitive business data indiscriminately; show connectivity and sync states; verify on desktop and mobile-sized layouts.
AI and agent discipline: verify Meta model ids and API behavior from official sources; structured schemas; confirmed facts in PostgreSQL; deterministic tools for prices, stock, authorization, policies; record evidence and verification outcomes; bound retries and repair loops; human approval for consequential actions; separate suggestions from persisted confirmed data.
Security discipline: no API keys in frontend bundles; no .env commits; validate uploads, enforce size/type limits; tenant authorization in the backend; redact secrets and unnecessary personal data in logs; treat customer messages and uploads as untrusted; no legal or regulatory compliance claims without assessment.
Verification discipline: report commands that were run; report failures honestly; separate mocked from real integration tests; no claim of deployment, integration or model call success without evidence; no invented performance numbers.
Final response format after every task: Completed; Files changed; Verification; Not completed; Assumptions; Risks; Next task.
Start with Prompt 1. Do not run all eight prompts in one operation.
