# 10 Building the multimodal agent

Source note: Meta's session listing "The multimodal intelligence of Muse Spark" (Meta Connect) describes the model as treating what it perceives "as something to act on, not just something to caption" and lists Muse Voice Transcribe as a real-time audio perception model. The listing has no transcript or API detail. API specifics here are UNVERIFIED until checked against official Meta docs; see docs/12. "Build a Multimodal AI Agent" content beyond this was not retrievable; adapt this file to it when you have it.

## Pattern: perceive -> ground -> act -> verify
1. Perceive: normalize photo, voice and text into one input bundle with provenance (who/when/what file).
   - Audio -> Muse Voice Transcribe -> transcript with spans. Test Hindi, Marathi, English and code-switching on real samples before claiming support.
   - Image -> Muse Spark interpretation -> candidate attributes with uncertainty flags; optional SAM 3.1 mask for the product region (masks give geometry, not truth).
2. Ground: reconcile candidates with PostgreSQL via read-only typed tools. Conflicts become conflict records, never silent overwrites.
3. Act: produce structured drafts (Pydantic): product draft, content brief, drafts with a claim list. Models propose; they do not write facts.
4. Verify: evidence verifier (facts), multimodal critic (image vs caption vs transcript vs fields vs DB), policy gate. Repair at most twice.
5. Approve and execute: seller sees diff + evidence; execution service writes confirmed data.

## Contracts (write these as Pydantic models first)
- `InputBundle`: items[{kind, uri, mime, received_at, sha256}], text, language_hint
- `CandidateAttributes`: fields[{name, value, confidence, source: image|voice|text|db, span?}], uncertainty[]
- `ConflictRecord`: field, values[{value, source}], severity, needs_owner
- `ContentDraft`: text, language, claims[{text, kind: fact|opinion, required_evidence}], version
- `ClaimVerdict`: claim_id, verdict, evidence_ids[], source_versions[], repair_suggestion?

## Multimodal-specific failure modes and checks
| Failure | Check | Eval category |
|---|---|---|
| Caption color differs from image/record | critic compares fields vs image description | caption_image_mismatch |
| Spoken price differs from DB | reconciliation conflict | voice_price_conflict |
| Material guessed from blurry photo | uncertainty flag, ask seller | photo_attribute_uncertainty |
| Generated visual changes color/pattern | compare Muse Image output to record | (add case) |
| Instruction hidden in transcript or image text | treated as data | prompt_injection |
| Transcription error on numbers | show transcript span, require confirmation for price/stock | voice_price_conflict |

## Build order
1. Adapter + one real structured text call (`just meta-smoke`).
2. Image input call; record whether images are accepted and in what format (UNVERIFIED until tested).
3. Photo -> `CandidateAttributes` with mock fixtures first, then live on a few real photos.
4. Reconciliation (deterministic) and conflict UI.
5. Voice (stretch): transcribe -> interpret -> merge.
6. Critic (lite) -> then evals.

## Cost and latency discipline
One model call per LLM node at most; cache deterministic tenant-scoped results only; record model calls and cost per workflow; photo and voice run as async jobs.
