# 07 Agent catalog (15 workflow nodes)

Fifteen logical stages, not fifteen model calls. Each node: typed input/output, permissions, exit condition. "Kind": LLM = model call; DET = deterministic code; MIX = code with optional model. Class and kind are ASSUMPTIONS to confirm. Models are Meta models via the adapter (IDs UNVERIFIED, see docs/12).

| # | Node | Stage | Kind | Model | Input -> Output | Permissions | Class |
|---|---|---|---|---|---|---|---|
| 01 | Intent and task planner | A | MIX | Muse Spark | seller request -> `TaskPlan` (bounded steps, allowed tools, budget) | none (plans only) | MVP (simple router first) |
| 02 | Multimodal intake | A | MIX | Voice Transcribe (audio), Spark (image/text) | uploads/text -> normalized input bundle with provenance | read uploads (tenant) | MVP |
| 03 | Context and memory | A | DET | - | bundle -> scoped context with source ids and freshness | read-only DB tools | MVP |
| 04 | Visual product perception | B | MIX | Spark; SAM 3.1 (stretch) | image -> candidate attributes, mask, uncertainty flags | read media | MVP (Spark), STRETCH (SAM) |
| 05 | Voice and instruction interpreter | B | LLM | Spark | transcript -> fields with spans and confidence | none | STRETCH |
| 06 | Catalogue reconciliation | B | DET | - | candidates + DB -> proposed changes + conflict records | read-only; proposes only | MVP |
| 07 | Content strategy | C | MIX | Spark | context -> content brief | none | MVP (light) |
| 08 | Content production | C | LLM | Spark; Image (stretch) | brief + facts -> versioned drafts with claim list | none | MVP |
| 09 | Customer intent and commerce | C | MIX | Spark | customer message -> answer with evidence or escalation; order draft | read-only product/stock/policy; order-draft tool | MVP-next |
| 10 | Evidence and claim verifier | D | DET + LLM assist | Spark (optional) | claims + records -> verdict per claim, evidence ids | read-only | MVP |
| 11 | Independent multimodal critic | D | LLM | Spark (separate prompt/config) | image + caption + transcript + fields -> mismatches, severity | none | MVP (lite) |
| 12 | Repair and recovery | D | MIX | Spark | failure + mismatch -> regenerate field / re-query / ask owner / stop; max 2 | none | MVP |
| 13 | Policy and permission gate | E | DET | - | proposed action -> allow / require_approval / deny | reads rules and role; cannot grant itself permissions | MVP |
| 14 | Human approval and action | E | DET | - | proposal diff -> approval record, execution receipt | execution service only, after owner approval of the exact proposal version | MVP |
| 15 | Evaluation and learning | E | DET | - | events -> scorecards, proposed improvements (never auto-applied) | write eval events | STRETCH (metrics), MVP (audit events) |

## Control separation (do not merge)
- 10 checks facts. 11 checks cross-modal consistency. 13 enforces permissions. One model call must not certify its own output and execute it.
- Treat critic independence as a hypothesis: evaluate against known errors; do not claim independence from a second prompt alone.

## Routing
- Seller product flow: 01 -> 02 -> 03 -> (04, 05) -> 06 -> 07 -> 08 -> 10 -> 11 -> 13 -> 14 -> 15. Failures go 10/11 -> 12 -> 10, cap 2, then blocked.
- Customer flow: 09 -> 10 -> 13 (skips 02, 04-08).
- Order draft: 09 -> 13 -> 14 (payment confirmation is owner-confirmed or provider-backed; never model-written).

## Per-node definition of done
Catalog row current; typed models; tests per apps/api/app/agents/CLAUDE.md; events emitted; no new permission without an ADR.
