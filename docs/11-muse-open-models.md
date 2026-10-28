# 11 Specialized intelligence: Muse open models and Fireworks (optional track)

Source note: the session "Building Specialized Intelligence on Fireworks: From Inference to Training with Muse Open Models" could not be retrieved. Facts below come from public pages fetched while building this kit; each is labelled with its source and confidence. Re-check before relying on any of it.

## What was found
| Fact | Source | Confidence |
|---|---|---|
| Fireworks model id for Muse Spark Open: `accounts/fireworks/models/muse-spark-open` | llmreference.com provider page | third-party, verify on Fireworks |
| 1M-token context; takes text, image, video, audio input; returns text; tags: vision, reasoning, JSON/tool use | same page | third-party, verify |
| Pay-as-you-go listing: $1.25 input, $4.25 output per 1M tokens (page value) | same page | third-party, verify; prices change |
| Released under the "Muse Model License" | same page | read the license before commercial use |
| Fireworks Managed Training: SFT, DPO, ORPO, LoRA only; OpenAI-format data | fireworks.ai/product/training | vendor page |
| Training API: custom loops, RL incl. GRPO; serverless LoRA per token, dedicated LoRA/full per GPU-hour | same | vendor page |
| Trained checkpoints deploy on the same platform | same | vendor page |
| Training page does not mention Muse models | same | so Muse fine-tuning on Fireworks is UNVERIFIED |

## Decision for the hackathon
- Primary demo: Meta Model API. This track is FUTURE / optional experiment, after the eval baseline exists.
- Do not self-host a large open model for a short hackathon. If experimenting, use a hosted endpoint.

## Experiment ladder (each step needs evidence before the next)
1. Inference swap: add a `FireworksClient` behind the same adapter interface (config-selected). Check whether the API is OpenAI-compatible (UNVERIFIED). Run the same dev evals mock vs live; compare quality, latency, cost.
2. Routing: use the cheaper or faster model for easy cases (customer FAQs from DB, field extraction), the stronger one for high-risk verification. Decide from eval data, not intuition.
3. Specialization (training): only if evals show a narrow, repeatable failure (for example claim classification in Hindi/Marathi) AND you have enough labelled data NOT in heldout. Candidate: a small supervised fine-tune of a claim-verdict classifier. Confirm the base model is trainable on the platform and license-compatible first.
4. Report: before/after on heldout, with cost of training and serving.

## Data hygiene for any training
Never train on tenant data without consent and anonymization; keep heldout out of training; version datasets; record hyperparameters and base model id.

## Why this is last
It adds infrastructure, cost and risk. The brief's must-haves are the verified workflow, approvals and honest evals. Specialization is a research extra, not a requirement.
