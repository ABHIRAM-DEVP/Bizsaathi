# 01 Architecture

Mermaid diagrams are the source of truth and live in git. ASSUMPTION: marks anything not verified.

## Containers (modular monolith + worker)
```mermaid
flowchart LR
  subgraph Client
    O[Owner web + PWA<br/>one Next.js app]
    C[Public store chat widget]
  end
  subgraph Backend
    API[FastAPI<br/>authN/Z, tenant scope, rate limits]
    G[LangGraph graph<br/>typed state, checkpoints, approval interrupts]
    W[Async worker]
    EX[Execution service<br/>only post-approval side effects]
  end
  subgraph Data
    PG[(PostgreSQL<br/>source of truth, pgvector optional)]
    RD[(Redis<br/>jobs, cache, limits)]
    S3[(S3-compatible storage)]
  end
  M[Meta Model API<br/>via one adapter]
  O --> API
  C --> API
  API --> PG
  API --> RD
  API --> S3
  API --> G
  G --> W
  G --> M
  G --> PG
  G -->|proposal| API
  API -->|owner approval, version-bound| EX
  EX --> PG
```

## The 15-node graph (conditional, not a chain)
```mermaid
flowchart TD
  IN[Seller photo + voice + text] --> N1[01 Planner]
  N1 --> N2[02 Intake]
  N2 --> N3[03 Context]
  N3 --> N4[04 Visual perception]
  N3 --> N5[05 Voice interpreter]
  N4 --> N6[06 Catalogue reconciliation]
  N5 --> N6
  N6 --> N7[07 Content strategy]
  N7 --> N8[08 Content production]
  CQ[Customer question] --> N9[09 Customer + commerce]
  N8 --> N10[10 Evidence verifier]
  N9 --> N10
  N10 --> N11[11 Multimodal critic]
  N11 --> N13[13 Policy gate]
  N10 -->|fail| N12[12 Repair, max 2]
  N11 -->|fail| N12
  N12 --> N10
  N12 -->|cap reached| BL[Blocked with explanation]
  N13 -->|require approval| N14[14 Owner approval + execution]
  N13 -->|deny| BL
  N14 --> N15[15 Evaluation]
  BL --> N15
  N15 --> AU[(Audit + metrics)]
```
Customer questions skip 02, 04-08 and go 09 -> 10 -> 13. Nodes 10, 11, 13 are different controls: facts, cross-modal consistency, permissions. No node certifies its own output.

## Sequence: photo to confirmed product
```mermaid
sequenceDiagram
  participant S as Seller (PWA)
  participant A as FastAPI
  participant W as Worker/Graph
  participant M as Meta adapter
  participant D as PostgreSQL
  S->>A: POST /uploads, then POST /products/from-photo
  A->>D: create job (tenant-scoped)
  A-->>S: 202 job id
  W->>M: structured image interpretation
  M-->>W: candidate attributes + uncertainty flags
  W->>D: reconcile with existing SKUs (read-only tools)
  W->>D: store proposal v1 (AI suggestion, not fact)
  S->>A: GET /jobs/{id}/events (SSE)
  S->>A: POST /approvals/{id}/approve (proposal version)
  A->>D: execution service writes confirmed product + audit event
```

## Sequence: customer question
```mermaid
sequenceDiagram
  participant C as Customer
  participant A as FastAPI (public, rate limited)
  participant G as Graph
  participant D as PostgreSQL
  C->>A: POST /public/sessions/{id}/messages
  A->>G: untrusted text + session scope (business_id from store slug)
  G->>D: read-only tools: product, stock, policy
  G->>G: evidence verifier + policy gate
  alt evidence supports answer
    G-->>C: answer with evidence refs
  else missing or ambiguous
    G-->>A: escalation to owner inbox
    A-->>C: honest holding message
  end
```

## Decisions
| Topic | Decision | Status |
|---|---|---|
| Shape | Modular monolith + worker; no microservices | ADR-0001 |
| Frontend | One Next.js app for web and PWA | fixed by brief |
| Models | Meta Model API behind adapter; IDs in config | IDs UNVERIFIED |
| Execution boundary | Model proposes, policy gate decides, owner approves, execution service acts | fixed |
| Retrieval | SQL tools for facts; pgvector/FTS only for unstructured policy text | optional |
| Observability | Structured logs, OpenTelemetry spans per node, observable events only | |
| Errors | Problem JSON `{type,title,status,detail,request_id}` | |

## Failure and retry
Timeouts per model call; retry transient errors only; max 2 repairs; model unavailable -> blocked state with manual-review path; fallback model never skips verification.

## Change rule
Any change to a diagram or the decisions table needs an ADR in docs/adr/.
