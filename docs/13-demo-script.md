# BizSaathi hackathon demo (3 minutes)

## Recording rule

The hackathon's Stage One requires a reasonable use of Meta Model API and/or Meta open-weight models. The repository currently defaults to mock mode, and a successful Meta call/model run is not verified in the project evidence. Before recording, configure and verify the eligible Meta model, then show its exact model/provider in the demo. Do not call a mock result a Meta result. If this proof is unavailable, the demo does not establish Stage One eligibility.

Show only working, tested features. Use a demo account and non-sensitive sample product data. Keep the recording to exactly 3:00; use captions and readable zoom for the interface and code.

## Timed script

| Time | Show and say |
|---|---|
| **0:00–0:18** | **Show:** Seller-facing app and one sample product photo. **Say:** “Small sellers receive product details through photos, messages, and memory. A wrong price or unsupported promise can cost trust. BizSaathi turns those inputs into reviewable work—the seller stays in control.” |
| **0:18–0:43** | **Show:** Upload the sample photo and start product intake; show the resulting job or draft. **Say:** “I’ll start with a product photo. The model helps interpret it, but the result is only a draft—not a confirmed catalog fact. We keep the workflow traceable instead of silently turning a guess into business data.” |
| **0:43–1:08** | **Show:** The actual Meta model/provider configuration or request evidence, then the generated extraction/draft. **Say:** “This run uses **[exact Meta model name]** through our server-side model adapter. The adapter keeps provider calls behind one interface; our application—not the model—controls tenant access and what can be saved.” **On screen:** Keep the model identity visible and never show API keys. |
| **1:08–1:38** | **Show:** Generate a product caption from the draft and available product records. Point to claim evidence or a genuinely blocked unsupported claim, if this path has been verified. **Say:** “Now we draft customer-facing copy. Confirmed facts come from the business record. Claims without supporting evidence should be flagged or blocked; the system must not invent certifications, price, or stock.” |
| **1:38–2:03** | **Show:** Review the proposal and its evidence/status, then approve or edit it if the actual UI supports that path. **Say:** “The seller sees what is proposed and decides what to accept. BizSaathi does not publish to social channels or make consequential changes by itself. Uncertain work can be corrected or escalated.” |
| **2:03–2:32** | **Show:** Briefly switch to the workflow trace and the relevant implementation: model adapter, LangGraph routing, and deterministic evidence/policy checks. **Say:** “Technically, this is a Next.js app backed by FastAPI, PostgreSQL, and a typed LangGraph workflow. The model proposes; ordinary application code enforces tenant scope, validates evidence, and gates approval. We record workflow outcomes and timing—not raw chain-of-thought.” |
| **2:32–2:48** | **Show:** A concise scorecard slide. **Say:** “Our recorded local checks include 236 of 236 backend unit tests and mock evaluations of 12 of 12 development cases and 4 of 4 held-out cases. These are software and mock-pipeline checks, not live-model quality or seller-impact measurements.” |
| **2:48–3:00** | **Show:** Return to the product and end card with repository and accessible video links. **Say:** “BizSaathi helps small sellers move from unstructured product information to evidence-grounded drafts, with the seller making the final call. AI proposes. Deterministic controls validate. Sellers approve.” |

## Capture checklist

- [ ] One representative submits one project for the team/startup; list every contributor on the submission.
- [ ] Verify the repository is public and the final video link is accessible without requesting permission.
- [ ] Complete the Meta Stage One proof: record a successful eligible Meta API call or open-weight model run, exact model identity, and the feature using it. Keep credentials private. Do not use paid Meta API calls without explicit authorization.
- [ ] Confirm every screen, model attribution, approval, validation result, and metric shown is real and repeatable. Remove any unimplemented path from the spoken script.
- [ ] Keep mock mode and mock evaluation results clearly labelled; do not imply they demonstrate live quality.
- [ ] Test the complete demo path immediately before recording; have a local screen recording ready only as a transparent fallback.
- [ ] Check the final video duration is 3:00 and submit before the stated deadline.

## Evidence and limits

The repository records local test and mock-evaluation results, but does not establish time saved, cost saved, production availability/performance, or live-model quality. Do not present illustrative percentages as BizSaathi outcomes. The Meta model identity and successful live/open-weight run must be verified before claiming Meta tooling use.
