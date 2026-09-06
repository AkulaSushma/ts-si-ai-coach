# Knowledge processing pipeline — raw content → candidate knowledge → verification-ready

| Field       | Value                                             |
| ----------- | ------------------------------------------------- |
| ID          | `SPEC-KNW-001`                                    |
| Status      | `APPROVED`                                        |
| Approved by | User instruction, session 004 (2026-09-06)       |
| Builds on   | `SPEC-ING-001` (ingestion), `D-0005` (providers), `D-0013` (no bypass), `VERIFICATION_POLICY.md` |

## 1. Purpose

The layer **after** ingestion: take raw content records (Instagram raw schema
today; any future adapter's records unchanged) and produce structured,
provenance-preserving **candidate knowledge** that a separate verification
stage can later promote or reject. The pipeline must be fully operable and
testable **without** live Instagram access, using a clearly-marked fixture
dataset, and without any real model call (an injectable client keeps tests
deterministic and free).

Non-negotiable inherited rules:

- Social-media content is `T3_EXPERT` and enters as **CANDIDATE** knowledge
  with `verification_status: UNVERIFIED`. Nothing social-media-derived may be
  `VERIFIED` by this pipeline, regardless of how many accounts repeat it.
- The verifier of a claim must be a different provider than its author
  (`config/model_routing.json` independence pairs; enforced by the existing
  validator).
- Raw source material is never overwritten. Every downstream record preserves
  provenance back to `source_id` + `content_id` + URL.
- No invented values: a field the model did not produce stays `null`.
- No new frameworks; standard library only (`D-0006`).

## 2. Layer separation (user requirement §2)

| Layer | Location | Written by | Mutability |
| ----- | -------- | ---------- | ---------- |
| A. Raw source content | `data/raw/<platform>/...` | ingestion (SPEC-ING-001) | immutable once written |
| B. Processed content | `data/processed/<platform>/<source_id>/<content_id>.json` | this pipeline, stage 1 | immutable once written |
| C. Candidate knowledge | `data/knowledge/candidates/<candidate_id>.json` | this pipeline, stage 3 | append-only; updates add provenance, never erase |
| D. Verified knowledge | `knowledge/` (existing, governed) | **verification stage only — not this pipeline** | governed by VERIFICATION_POLICY |
| E. Questions | `data/knowledge/questions/<question_id>.json` | this pipeline (candidates only, UNVERIFIED) | append-only |

The D layer is untouched by this spec's implementation. Layer C feeds a
verification queue that a future stage consumes. Files under `data/` are
git-ignored runtime products (`D-0008`); the code and tests are the tracked
artifacts, plus a small fixture committed under `tests/`.

## 3. Stage 1 — content processing (null-safe)

`processor.py` turns one raw record into one **processed record**:

- Assembles a `text_parts` list from, in order: caption, per-slide OCR text
  (slide order preserved), transcript, on-screen text. Null/missing parts are
  skipped, never fabricated. If all are null/empty, the record is
  `skipped_reason: "no_text"` and no model call happens (cost control §10).
- Keeps `published_at`, `content_type`, `hashtags`, media counts, provenance
  verbatim from the raw record; adds nothing.
- Emits a stable `processing_hash` = SHA-256 over the assembled text parts,
  so identical content across sources is detectable before any model call.
- A processed record is written once; reprocessing an identical raw record
  reuses it (idempotency, §11).
- OCR/transcription providers are **interfaces only** in this build
  (`OcrProvider`, `TranscriptionProvider` protocols); the raw records already
  carry null OCR/transcript fields, and the processor reads whatever exists.
  No OCR implementation is attempted while raw media is unavailable.

## 4. Stage 2 — GLM extraction (structured, versioned, routed)

### 4.1 Prompt

`prompts/knowledge_extraction_v1.py` — version string `knowledge-extraction-v1`.
The prompt is a versioned module (tracked in Git), instructing the model to:

- extract **atomic** knowledge units, not summaries;
- preserve factual meaning; separate multiple facts (the 26-Nov-1949 /
  26-Jan-1950 example is built into the prompt);
- mark relevance `RELEVANT` / `NOT_RELEVANT` / `UNCERTAIN` per item;
- classify `subject` and `knowledge_type`;
- extract questions/MCQs separately, never inventing options/answers;
- state uncertainty explicitly; never invent missing information;
- distinguish source claims from verified facts (output is explicitly
  `source_claim`, not truth);
- return **strict JSON** matching the schema, with a `provenance` echo of the
  source ids it was given.

Prompt changes require a new version string; `prompt_version` is stored on
every candidate and every processing checkpoint (§10) so future re-extraction
is a conscious decision, not silent drift.

### 4.2 Output schema (machine-checkable)

```json
{
  "relevance": "RELEVANT | NOT_RELEVANT | UNCERTAIN",
  "items": [
    {
      "knowledge_text": "...",
      "knowledge_text_te": null,
      "subject": "<taxonomy subject>",
      "topic": null,
      "knowledge_type": "<taxonomy type>",
      "confidence": 0.0,
      "is_question": false,
      "question": null
    }
  ],
  "questions": [
    {
      "question_text": "...",
      "options": {"A": "...", "B": "..."},
      "answer": "A | null",
      "explanation": null,
      "subject": "...",
      "topic": null,
      "question_format": "MCQ | QUESTION",
      "answer_status": "STATED_BY_SOURCE | NOT_STATED"
    }
  ],
  "notes": null
}
```

Validation (`extraction_schema.py`): enums checked against `taxonomy.py`
(extended: subjects include "Indian Constitution" as a distinct subject;
new subjects allowed via a `subject_allowlist` that reads the registry, so
adding a subject is data, not code); `knowledge_text` non-empty and ≤ 2000
chars; `confidence` in [0,1]; every question with `answer_status:
STATED_BY_SOURCE` must have non-null answer; an answer with
`NOT_STATED` must be null. Malformed output raises
`ExtractionSchemaError` with the field path — the item is recorded
failed-with-retries and never silently coerced.

### 4.3 Routing and client

- Role: a new `KNOWLEDGE_EXTRACTION` role entry is added to
  `config/model_routing.json`, provider `glm` (GLM 5.3, `GLM_API_KEY`,
  `GLM_BASE_URL` from env — no key in any tracked file), fallback `anthropic`.
  Its independence pair is added (`KNOWLEDGE_EXTRACTION` → `VERIFICATION`),
  which the existing validator enforces mechanically.
- `client.py` exposes `GlutClient` (sic: `GlmClient`) with a
  single `extract(content: ProcessedRecord) -> ExtractionResult` call,
  implemented over stdlib `urllib` + JSON. The concrete HTTP call exists but is
  **not exercised by tests**; every test injects a `RecordingFakeClient`.
  If `GLM_API_KEY` is absent, live calls raise `MissingKeyError` — the CLI
  reports it honestly instead of pretending.

## 5. Stage 3 — candidate knowledge

`candidates.py` maps one validated model output to N **candidate records**:

- Atomic units: one candidate per `items[]` entry — the 26-Nov/26-Jan example
  yields two candidates, both carrying the same source provenance.
- `candidate_id` = deterministic SHA-256 prefix over
  (source_id, content_id, prompt_version, index, knowledge_text) — stable
  across runs, so reprocessing detects the same candidate rather than
  duplicating it (idempotency §11).
- Every candidate embeds full provenance:
  `source_id, profile_username, content_id, source_url, published_at,
  content_type, extraction_model, prompt_version, extraction_timestamp`,
  `provenance_tier: T3_EXPERT` (for social-media sources), and
  `relevance` + exam-relevance scores (§7).
- `verification_status` is **always** `UNVERIFIED` at creation, and the store
  refuses any other initial value for `T3_EXPERT` input.
- Questions land in the questions store with the same provenance and
  `verification_status: UNVERIFIED`; answers are kept only when
  `STATED_BY_SOURCE`.

## 6. Deduplication & corroboration

`dedup.py` — deterministic, documented, no model calls:

- **Exact/near-exact**: candidates whose `normalized_text` (lower, whitespace
  collapsed, punctuation stripped) plus `knowledge_type` match are the same
  concept.
- **Cross-source corroboration**: same concept seen from multiple sources
  produces ONE concept record with `source_count`, `supporting_sources[]`
  (each: source_id, content_id, url, first_seen), and `source_diversity`
  (`SAME_ACCOUNT | FEW_ACCOUNTS | MANY_ACCOUNTS` — few=2-3, many≥4 distinct
  source_ids). The A/B "42nd Amendment" example in the user's instruction is
  a fixture case.
- **Never merges away provenance**: supporting sources are appended, never
  replaced; each retains its own candidate_id.
- Corroboration does **not** verify: a concept with 5 supporting Instagram
  accounts is still `UNVERIFIED`; `corroboration_is_not_verification: true`
  is recorded on the concept and asserted by tests.

## 7. Exam relevance scoring (documented, deterministic)

Scores are computed from **declared rules only**, never model invention:
`scoring.py` implements the scale in `docs/relevance_scale.md`:

- `si_relevance` / `constable_relevance`: `1` if the candidate's subject maps
  to a verified official syllabus node (OFF-SYL-*), `0` otherwise — the
  mapping table is data (`subject_syllabus_map.json`), citing node ids.
- `telangana_relevance`: `1` if subject ∈ {Telangana History, Telangana
  Geography, Telangana GK} or the text matches a Telangana-entity list,
  else `0`.
- `pyq_similarity`: `null` until a PYQ database exists (no denominator ⇒ no
  number; the field exists per the user's schema).
- `revision_priority`: integer 0–5 from a fixed published rule
  (subject-on-syllabus 2 pts; telangana 1; knowledge_type ∈ {FACT, DATE,
  LAW, ARTICLE, AMENDMENT} 1; CURRENT_AFFAIRS requires recency ≤ 12 months
  1 — else 0), capped at 5.
- `confidence`: the extraction model's own number, copied as-is with
  `confidence_basis: "model_self_reported"`; never interpreted as accuracy.

## 8. Verification queue (architecture, not fake verification)

`verify_queue.py` maintains `data/knowledge/verification_queue.jsonl`:
one line per candidate that reaches queueing, containing candidate_id,
concept_id, provider that authored it (from routing), required verifier
provider (resolved `AUTO_NOT_AUTHOR` at queue time from the routing config —
must differ from author, else the item is `QUEUED_BLOCKED_NO_INDEPENDENT_VERIFIER`),
and `status: UNVERIFIED`. The queue:

- performs **no verification itself**;
- refuses to mark anything `VERIFIED`;
- is the only input the future verification stage will consume.

A `VERIFIED` transition requires, by schema, a verification run id that exists
in `verification/runs/` — none exists today, so nothing can be verified yet.

## 9. Batch processing, resume, idempotency, cost control

`pipeline.py` — `KnowledgePipeline.process_batch(items, client)`:

- Processes items one at a time (model calls are per-item; batching at the
  transport level is the client's concern and GLM's context limits make
  per-item the honest unit).
- **Checkpoint** after every item: `data/knowledge/checkpoint.json`
  (per-prompt_version) records processed content_ids, failed ones with retry
  counts, and stage. Crash ⇒ resume continues from the checkpoint; already
  processed items are skipped, not reprocessed (§16 user requirement:
  "stop at 437 ⇒ resume from 437").
- **Idempotency**: candidate files keyed by deterministic id; a second run
  over the same raw items reuses processed records and candidates; no
  uncontrolled duplicates (§17).
- **Cost controls** (§18): skip empty content (stage 1); skip already
  processed (checkpoint); skip exact duplicate text within a run
  (`processing_hash` memo); every model call's request/response digests are
  logged to `data/knowledge/model_calls/` so nothing is re-called for the
  same content+prompt; prompt and model version are part of every record.
  Extraction quality is never traded for fewer calls — controls only
  eliminate *redundant* calls.

## 10. CLI

`scripts/process_knowledge.py` (mirrors `scripts/ingest.py` conventions):

```
python scripts/process_knowledge.py process --platform instagram            # all raw records
python scripts/process_knowledge.py process --source IG001                # one source
python scripts/process_knowledge.py process --fixture                    # the committed fixture
python scripts/process_knowledge.py status
```

`--fixture` runs the pipeline over `tests/fixtures/raw_records/` with the
recording fake client — the "first GLM test" of user requirement §22,
executed offline. `status` makes no model calls.

## 11. Fixture dataset

`tests/fixtures/raw_records/` — a small deterministic dataset marked
`"test_fixture": true` on every record and directory manifest, using the
**existing** raw-record schema (SPEC-ING-001 §4.4), clearly labelled as
fixture, never presented as Instagram content. It contains: a two-fact
constitution post (the user's exact example), an MCQ post with stated
answer, a question post without an answer, an irrelevant post (a meme), a
not-relevant/uncertain borderline post, a duplicate of the 42nd-Amendment
fact from a *different* source id (for cross-source dedup), and an
empty-content record (null caption, no OCR). Source ids use the reserved
fixture range `IGFIX*` so they can never collide with real registry ids.

## 12. Acceptance criteria

1. A raw record with all-null text produces a processed record with
   `skipped_reason: "no_text"` and zero model calls.
2. Null/missing fields anywhere are skipped, never invented; tests feed a
   record with only OCR text, only caption, and only transcript.
3. `NOT_RELEVANT` output creates no candidate; `RELEVANT` and `UNCERTAIN`
   both create candidates.
4. Every candidate's subject is in the taxonomy; an out-of-taxonomy subject
   in model output fails validation.
5. Every knowledge_type is in the enum; an unknown type fails validation.
6. The two-fact constitution fixture produces exactly two candidates with
   identical provenance and different texts.
7. The MCQ fixture produces a question record with options + answer; the
   no-answer question records `answer: null` with
   `answer_status: NOT_STATED`; no option is ever invented (a fake client
   that omits options yields empty options, not fabricated ones).
8. Every candidate preserves source_id/content_id/url/timestamps from its
   raw record — asserted field-by-field.
9. Two candidates with normalized-equal text and same type dedup to one
   concept with both provenances retained.
10. The A/B 42nd-Amendment fixture pair (different source ids) becomes one
    concept with `source_count: 2`, both supporting sources, and still
    `UNVERIFIED`.
11. Re-running the pipeline over the same fixture creates no new candidate
    files (byte-identical set).
12. A run interrupted after item k resumes at item k+1; already-processed
    items are not reprocessed (fake client call count asserted).
13. Malformed model output (missing field, bad enum, wrong type) fails
    validation with a field path, is retried per policy, and never coerced.
14. Model failure (exception) on one item does not stop the batch; the item
    is recorded failed with retry count; the batch completes.
15. Verification-state separation: no candidate can be created with
    `verification_status` ≠ `UNVERIFIED`; the verification queue never
    emits `VERIFIED`; the verifier provider always differs from the author
    provider (routing-derived).
16. A new prompt version string changes candidate ids and is recorded in the
    checkpoint, so re-extraction is explicit (old candidates coexist, labeled
    by their prompt version).
17. No test performs a network call; the GLM client's HTTP path exists but is
    exercised only by an explicit live command, which requires `GLM_API_KEY`
    and reports honestly when absent.
18. The full existing suite stays green; no Instagram source is processed
    (no `data/raw/instagram/` records exist; the fixture is the only input).

## 13. Explicitly out of scope

- Bulk processing of any real source (`IG001`–`IG032`) — blocked on `B-08`;
  the pipeline must be **ready**, not run.
- Any OCR/transcription implementation — interfaces only.
- Any verification execution — queue only.
- The trusted `knowledge/` layer — untouched.
- The SQLite database (`D-0010` open) — file-based stores now; a migration
  later maps 1:1 onto the record shapes defined here.
