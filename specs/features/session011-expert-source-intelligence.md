# SPEC-INT-011 — Expert-source intelligence path (video-capable)

Status: APPROVED, PARTIALLY IMPLEMENTED
Depends on: SPEC-INT-010 (evidence integrity and bounded media intake)

## Purpose

Turn real expert media into auditable learning intelligence without ever letting a
teaching claim, a model interpretation or a single worked example become a
verified fact.

## Pipeline

```
committed asset -> identity (Git blob SHA-1 + SHA-256)
                -> probe (ffprobe metadata attempt)
                -> derivative (hashed frame at a probed timestamp)   [video]
                -> evidence span (image_region | video_interval)
                -> candidate (SOURCE_DERIVED T3 | MODEL_DERIVED T4)
                -> independent assessment per dimension
                -> fail-closed state projection
```

## Rules

1. **Identity before intelligence.** `register_committed` refuses any local file
   whose Git blob SHA-1 differs from the committed blob. The identity check is
   itself journalled as a PASS attempt.
2. **Located evidence only.** Every span carries the asset SHA-256, the probe id
   and either an `image_region` inside the real pixel dimensions or a
   `video_interval` inside the probed duration.
3. **Derivatives are evidence.** Extracted frames are hashed; an attempt records
   timestamp, engine version, processor version, artifact name and artifact hash,
   and is reused only when the artifact still hashes identically.
4. **Fail closed on missing capability.** Unavailable OCR/ASR produces a
   `BLOCKED` attempt with `output: null`. A BLOCKED or FAIL attempt can never
   support a span, so it can never reach a candidate or a verified claim.
5. **Origin separation.** `SOURCE_DERIVED` candidates must preserve the exact
   extracted wording; any paraphrase is `MODEL_DERIVED`. Candidates are created
   `UNVERIFIED`, with `confidence: null`, `pyq_links: []`.
6. **Independent dimensions.** correctness, applicability, speed, recognition,
   retention, source_fidelity are assessed separately. Correctness requires a
   DETERMINISTIC recomputation with at least two valid cases and one boundary
   case. `VERIFIED_FAST_METHOD` requires correctness AND applicability AND speed.
7. **Revision-bound history.** Assessments are bound to a hash of the exact
   method statement. Correcting a rule statement creates a new revision; the
   earlier revision keeps its FAIL and stays blocked forever.
8. **Underdetermination.** A single matching example never establishes a rule;
   `reasoning_verify.alternative_rule_count` demonstrates competing rules.

## Durable structures

- `data/expert_media/asset_plan.jsonl` — one header line plus one line per
  committed asset (file name, media class, bytes, Git blob SHA-1). Unobserved
  fields (publisher, source URL, transcript, PYQ relationships) are declared as
  defaults in the header rather than guessed per asset.
- Evidence journal records: `asset`, `occurrence`, `attempt`, `span`,
  `candidate`, `assessment` (append-only, hash-sealed).

## Out of scope for this checkpoint

UI, bulk processing, OCR/ASR engines, Telugu transcription, PYQ relationship
evidence, near-duplicate detection, concurrent scheduling, and any promotion of
legacy stored `VERIFIED` labels.
