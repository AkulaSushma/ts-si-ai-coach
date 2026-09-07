# TASK_LEDGER.md

Every task carries acceptance criteria and exactly one status: `COMPLETE`, `PARTIAL`,
or `BLOCKED`. A task is never marked `COMPLETE` because it was attempted.

ID format: `T-####`, sequential, never reused.

## Open Tasks

| ID       | Task                                              | Status    | Depends on |
| -------- | ------------------------------------------------- | --------- | ---------- |
| `T-0010` | Acquire official TGPRB SI notification + syllabus  | `PARTIAL` | Main notification + supplement RETRIEVED and read (session 004); 4 of 6 registered documents still blocked (`B-09`) |
| `T-0011` | Extract official syllabus into `knowledge/official/syllabus.json` | `COMPLETE` | 27 nodes verified against DOC-OFF-002 pages 42–44; quotes mechanically re-checked |
| `T-0012` | Write the data-model specification                | `BLOCKED` | `T-0011` complete — unblocked; knowledge-pipeline record shapes are ready inputs |
| `T-0013` | Acquire previous-year papers with keys             | `PARTIAL` | 9 coaching-copy papers supplied by the user under `source_material/pyq_raw/`, enumerated, SHA-256 hashed and registered (session 008). 2 of 9 extracted (400 questions); 7 scanned/not extracted. Source-host set still `BLOCKED` (`B-02` egress) — no board/coaching host reachable, so the broader universe is unenumerable. Coalesced with sibling `T-0018` (weightage) |
| `T-0014` | Confirm and pin provider model ID strings          | `BLOCKED` | `B-04`; `glm-5.3` still `UNVERIFIED_STRING` — no live call yet |
| `T-0019` | Decide Instagram access path (auth / network / defer) | `BLOCKED` | `B-08` — user decision |
| `T-0020` | Bulk-extract remaining 31 IG sources               | `BLOCKED` | `T-0019` — live access refused |
| `T-0021` | OCR + transcription stage over stored media         | `BLOCKED` | Live ingestion producing raw records (`T-0019`); interfaces exist |
| `T-0033` | Get the official notification PDFs into `source_material/official/` | `PARTIAL` | DOC-OFF-002/003 supplied by user and hashed; DOC-OFF-001/004/005/006 still blocked (`B-09`) |
| `T-0034` | Hash, ledger and confirm the retrieved documents    | `COMPLETE` | SHA-256 in `config/official_documents.json` + `EXTRACTION_MANIFEST.json`; hash-tamper test green |
| `T-0035` | Extract the 25 official facts, each with document, page/section and verbatim quote | `PARTIAL` | 24 of 25 `VERIFIED`; OFF-F03 honestly `BLOCKED` (dates deferred to a press release by the notification itself) |
| `T-0036` | Map the official syllabus Subject → Topic → Subtopic | `COMPLETE` | 27 nodes; document prints no subtopic layer, so none exists (by design rule) |
| `T-0037` | Populate `knowledge/weightage/official_marks_structure.json` | `COMPLETE` | 14 entries (6 PWT + 8 FWE) verified against DOC-OFF-002 pages 19–24 & 42–44; notification prints no topic-wise distribution, so `official_topic_weightage_provided_by_notification: false`; quotes mechanically re-checked |
| `T-0038` | Resolve `CONF-OFF-001` — which board domain is controlling | `BLOCKED` | `T-0033` partial — still needs an egress-enabled fetch of tslprb.in |
| `T-0051` | Reconcile the supplementary notification against the original | `COMPLETE` | `knowledge/official/current_official.json` — 5 records (REC-001–005); DOC-OFF-003 amends only the age paragraph (GO Ms No. 122, +2 years), additive to GO Ms No. 87's (+5); governing general upper limit derived as 32 as on 1 July 2026; no conflict; structured tests + fabricated-data cases in `test_official_knowledge.py` |
| `T-0040` | Write `SPEC-KNW-001` before any pipeline code      | `COMPLETE` | `specs/features/knowledge-processing-pipeline.md`, `APPROVED`, 18 acceptance criteria in §12 |
| `T-0041` | Build the content-processing stage (null-safe)      | `COMPLETE` | `processor.py`; 6 processing tests incl. all-null, OCR-only, transcript-only |
| `T-0042` | Build the GLM extraction schema + versioned prompt  | `COMPLETE` | `extraction_schema.py` (field-path errors, enum-enforced), `prompts/knowledge_extraction_v1.py` (`knowledge-extraction-v1`) |
| `T-0043` | Route extraction through model_routing.json        | `COMPLETE` | `KNOWLEDGE_EXTRACTION` role (glm/anthropic fallback) + independence pair; validator enforces separation |
| `T-0044` | Build candidate + question construction with provenance | `COMPLETE` | `candidates.py`; deterministic ids; provenance asserted field-by-field in tests |
| `T-0045` | Implement documented deterministic scoring          | `COMPLETE` | `scoring.py` + `docs/relevance_scale.md` v1; PYQ similarity null without denominator |
| `T-0046` | Implement dedup + cross-source corroboration       | `COMPLETE` | `dedup.py` + `config/dedup_synonyms.json`; 42nd-Amendment fixture pair → one concept, 2 sources, still UNVERIFIED |
| `T-0047` | Build the verification queue (no fake verification) | `COMPLETE` | `verify_queue.py`; UNVERIFIED-only; provider separation recorded per line; no verify method exists |
| `T-0048` | Batch processing with checkpoint/resume/idempotency/cost controls | `COMPLETE` | `pipeline.py`; resume-from-crash, idempotent rerun (0 new files, 0 re-calls) tested |
| `T-0049` | Fixture dataset + offline "first GLM test"         | `COMPLETE` | `tests/fixtures/raw_records/` (test_fixture: true, IGFIX* ids); run verified: 9→7 candidates, 2 questions, 6 concepts, 7 queued |
| `T-0050` | Tests for all 18 SPEC-KNW-001 criteria            | `COMPLETE` | 59 tests in `tests/knowledge/test_knowledge_pipeline.py`; full suite 220/220 |

`T-0033` is now the highest-value action in the entire project: 25 fact slots, the
official syllabus, the marks structure, `physical/standards/` and `CONF-OFF-001` all
wait on bytes that no further engineering can produce. `T-0019` gates Instagram
content acquisition: the machinery is finished, only the access decision is missing
(`B-08`).

## Blocked Tasks

| ID       | Task                              | Blocked by | Why it cannot proceed                                          |
| -------- | --------------------------------- | ---------- | -------------------------------------------------------------- |
| `T-0011` | Syllabus extraction               | `T-0010`   | Nothing to extract from. Writing one from memory is prohibited   |
| `T-0012` | Data-model spec                   | `T-0011`   | The schema must reflect the real syllabus taxonomy               |
| `T-0015` | Build the AI tutor                | `T-0011`   | A tutor with no verified knowledge would invent exam facts        |
| `T-0016` | Build the frontend                | `D-0003`   | Framework undecided; no approved UI spec                        |
| `T-0017` | Populate physical event standards | `B-03`     | Official document only. An invented standard causes real harm     |
| `T-0018` | Topic weightage analysis          | `T-0013`   | A percentage needs a counted denominator                        |
| `T-0035` | Official fact extraction          | `T-0034`   | A fact with no retrieved document cannot cite a page or a quote  |
| `T-0036` | Official syllabus mapping         | `T-0034`   | Coaching syllabi are not the board's syllabus (`D-0015`)          |
| `T-0038` | `CONF-OFF-001` resolution         | `T-0033`   | Deciding a controlling domain without reading either is a guess   |

## Session 003 — official knowledge foundation

| ID       | Task                                                       | Status     | Verified by |
| -------- | ----------------------------------------------------------- | ---------- | ----------- |
| `T-0023` | Write `SPEC-OFF-001` before any structure                    | `COMPLETE` | `specs/features/official-knowledge-foundation.md`, status `APPROVED`, acceptance criteria in §6, container-vs-content rule in §9 |
| `T-0024` | Probe the official sources and record accessibility verbatim | `COMPLETE` | `source_material/official/RETRIEVAL_LOG.md` — every refusal quoted; `B-09` identified as host-level egress denial, not a login wall or an outage |
| `T-0025` | Enumerate and register the official documents                | `COMPLETE` | `config/official_documents.json` — 6 documents, `retrieved_count: 0`, 2 URLs flagged `INFERRED_UNVERIFIED`, 1 conflict recorded, coaching mirrors excluded |
| `T-0026` | Create the 25 official fact slots with provenance fields     | `COMPLETE` | `knowledge/official/required_facts.json` — `OFF-F01`–`OFF-F25`, every `value` `null`, every `status` `BLOCKED` with a reason; tested by `TestEveryOfficialFactHasProvenance` |
| `T-0027` | Create the official syllabus container and justify emptiness | `COMPLETE` | `knowledge/official/syllabus.json` — 0 nodes with a written reason; `TestOfficialSyllabusIsFullyMapped` forbids an unexplained empty syllabus and forbids emptiness once a document is retrieved |
| `T-0028` | Separate the three weightage categories                      | `COMPLETE` | `knowledge/weightage/` — official marks (`T1_OFFICIAL`), observed weightage (`T2_HISTORICAL_PYQ`), estimated priority (`T4_AI`); cross-tier contamination tested |
| `T-0029` | Build the preparation taxonomy that forbids the official tier | `COMPLETE` | `knowledge/preparation_taxonomy/taxonomy.json`; `test_preparation_taxonomy_forbids_the_official_tier` |
| `T-0030` | Write the three declarative schemas                          | `COMPLETE` | `knowledge/schemas/` — enforced by hand-written checks, no third-party validator (`D-0006`) |
| `T-0031` | Record the balanced acquisition manifest and research plan    | `COMPLETE` | `research/manifests/official/2026-09-06-tgprb-si-2026.json` balances `expected = processed + inaccessible + irrelevant + duplicate + failed`; `research/plans/PLAN-OFF-001` |
| `T-0032` | Write the six required Phase-1 verification tests             | `COMPLETE` | `tests/official/test_official_knowledge.py` — 69 tests, one class per required test, plus 30 fabricated-record tests and 2 clean-data tests |
| `T-0039` | Replace the two self-declared reconciliation stubs            | `COMPLETE` | `scripts/validate_bootstrap.py` check 18 and `tests/bootstrap/test_bootstrap.py::TestHonestyOfState` now recompute real counts; 10 fabricated-data cases prove the reconciliation can fail |

Acceptance criteria for these tasks are in `SPEC-OFF-001` §6. Every criterion that
concerns the *container* is satisfied and tested. Every criterion that concerns
*content* — retrieved documents, extracted facts, mapped syllabus nodes — is
`BLOCKED` at zero by `B-09`. `SPEC-OFF-001` §9 states in writing that passing the
container tests does not license calling the phase `COMPLETE`.

## Session 007 — PYQ acquisition & analysis preparation

| ID       | Task                                                          | Status     | Verified by |
| -------- | ------------------------------------------------------------- | ---------- | ----------- |
| `T-0052` | Write `SPEC-PYQ-001` before any structure                      | `COMPLETE` | `specs/features/pyq-questions-foundation.md`, status `APPROVED`, 8 acceptance criteria (AC-1..AC-8) in §9, container-vs-content rule in §9 |
| `T-0053` | Identify the required paper set and the eligibility rule       | `COMPLETE` | `SPEC-PYQ-001` §4 — the set of concrete years/papers is honestly `UNVERIFIED`; the eligibility rule over components/posts/provenance is recorded, not a claim that any paper exists |
| `T-0054` | Probe paper sources and record the blocker verbatim            | `COMPLETE` | `config/pyq_source_registry.json` `attempts[]` + `source_material/pyq_raw/RETRIEVAL_LOG.md` — 3 refusals verbatim (google.com, tgprb.in, web search no-content); `B-02`/egress; no bypass (`D-0017`) |
| `T-0055` | Build the PYQ source + document registries and retrieval log   | `COMPLETE` | `config/pyq_source_registry.json` + `config/pyq_documents.json` + `RETRIEVAL_LOG.md`; balanced accounting `0 = 0+0+0+0+0`; `tests/pyq` assert fields, blocked state, and verbatim-log cross-reference |
| `T-0056` | Create the PYQ storage + extraction structure (content folders) | `COMPLETE` | `pyq/{papers,questions,weightage}/README.md` + `.gitkeep` (already tracked); each README states its provenance/denominator rules |
| `T-0057` | Write the three PYQ schemas (paper / question / weightage)     | `COMPLETE` | `knowledge/schemas/pyq_paper.schema.json`, `pyq_question.schema.json`, `pyq_weightage.schema.json`; hand-written checks (`D-0006`) |
| `T-0058` | Record the balanced acquisition manifest                       | `COMPLETE` | `research/manifests/pyq/PYQ_ACQUISITION_MANIFEST.json` (`PYQ-ACQ-007`) — status `blocked`, identity `0 = 0+0+0+0+0`, reason recorded, coaches/candidate-recall notes |
| `T-0059` | Add PYQ provenance + anti-vacuity tests                        | `COMPLETE` | `tests/pyq/test_pyq_foundation.py` — 45 tests over AC-1..AC-8; `TestPyqCheckersRejectFabrication` has 15 poisoned-record cases + `test_a_clean_record_set_is_accepted` proving the checkers are not always-failing |

Acceptance criteria are in `SPEC-PYQ-001` §9. Every **container** criterion
(`AC-1`..`AC-8`) is satisfied and tested, and the anti-vacuity tests prove the
checkers can fail. Every **content** criterion — acquired papers, hashed bytes,
extracted questions, computed weightage — is `BLOCKED` at zero by `B-02` (egress
allowlist). `SPEC-PYQ-001` §9 states in writing that passing the container tests
does not license calling the phase `COMPLETE` (`D-0016`).

## Session 008 — real-data PYQ processing

| ID       | Task                                                          | Status     | Verified by |
| -------- | ------------------------------------------------------------- | ---------- | ----------- |
| `T-0060` | Register the nine real paper PDFs in the PYQ registries        | `COMPLETE` | `config/pyq_documents.json` COMPLETE (9 documents, SHA-256); `pyq/papers/PAPER-PYQ-*.json`; `SOURCE_LEDGER` SRC-0039–SRC-0047 (`T2_HISTORICAL_PYQ`/`COACHING_COPY`); acquisition manifest `partial`, identity `9 = 9+0+0+0+0` |
| `T-0061` | Extract questions with provenance from the extractable papers  | `COMPLETE` | The two papers with a usable text layer (2016 Preliminary, 2016 GS final) → **400 records** in `pyq/questions/` (`Q-PYQ-010001`..), each `T2_HISTORICAL_PYQ`, sourced, `answer_source` present. The other 7 registered papers are scanned image-only/watermark-only and are registered as retrieved but not extracted — documented, not silently skipped |
| `T-0062` | Classify extracted questions with confidence                  | `COMPLETE` | Every record carries a `classification` block (subject/topic, keyword/pattern basis, `NEAR`/`AMBIGUOUS`, `unresolved: true` where a topic could not be resolved). No silent guessing: unresolved topic → `topic: null` |
| `T-0063` | Compute observed subject/topic frequency with explicit coverage | `COMPLETE` | 13 entries `WGT-PYQ-0001`..`WGT-PYQ-0013` over the 400 questions, each `PARTIAL` with counted/intended coverage (2/9 papers, 400 questions), `basis OBSERVED`, `T2_HISTORICAL_PYQ`. Subject sums: General Studies 299, Arithmetic/Reasoning 101. No entry claims a share of the whole corpus |
| `T-0064` | Run all checks green and add real-data validation            | `COMPLETE` | Validator 21/21 exit `0`; full suite 278 tests, 0 failures, 3 skips correct-by-design. Fixed at root cause the bootstrap ledger-reconciliation accounting bug (`stored_and_raw()` was counting derived `pyq/` records as harvested sources; now counts acquired source bytes, matching `validate_bootstrap.py`) |

Acceptance criteria are in `SPEC-PYQ-001` §9. The **content** criteria — acquired
and hashed papers, extracted questions, computed weightage — are no longer at
zero: 9 papers registered, 2 extracted (400 questions), 13 observed-frequency
entries over an explicitly partial (2/9) set. The set is honest `PARTIAL`, never
`COMPLETE`: 7 of 9 registered papers are scanned and not extracted, the source-host
universe is unenumerable from this environment (`B-02`), and every weightage entry
states its counted/intended coverage.

## Completed Tasks

| ID       | Task                                          | Status     | Verified by                                  |
| -------- | --------------------------------------------- | ---------- | -------------------------------------------- |
| `T-0001` | Inspect project directory and Git state        | `COMPLETE` | `find` listing; `git rev-parse`; write/lock probes |
| `T-0002` | Create long-term directory architecture        | `COMPLETE` | Directory count check in `validate_bootstrap.py` |
| `T-0003` | Write the nine governance files                | `COMPLETE` | Presence + required-section checks             |
| `T-0004` | Create `.gitignore`, `.env.example`, routing config | `COMPLETE` | JSON parse + secret-pattern checks        |
| `T-0005` | Build bootstrap validation script and L0 tests  | `COMPLETE` | Script exit code 0; `unittest` run             |
| `T-0006` | Run validation and fix every failure           | `COMPLETE` | See `docs/reports/2026-09-05-bootstrap.md`     |
| `T-0007` | Initialise Git and create the first checkpoint  | `COMPLETE` | `git log`; clean `git status`                  |
| `T-0008` | Record verified state in the ledgers           | `COMPLETE` | This file and `PROJECT_STATE.md`               |
| `T-0009` | Resolve test failures; record verified results  | `COMPLETE` | Validator exit `0` (21/21); `unittest` `OK` (35/35) |
| `T-0022` | Re-verify bootstrap at `589877c` after session-002 edits | `COMPLETE` | 2026-09-06: validator 21/21 exit `0`; `unittest` 78/78 `OK`; `git diff a77f793 HEAD` on bootstrap checks reviewed line by line |

## Session 002 — ingestion subsystem

| ID       | Task                                                       | Status     | Verified by |
| -------- | ----------------------------------------------------------- | ---------- | ----------- |
| `T-0015a`| Write `SPEC-ING-001` before any code                        | `COMPLETE` | `specs/features/ingestion-subsystem.md` present with acceptance criteria |
| `T-0015b`| Build registry of 32 unique IG sources, cap 299             | `COMPLETE` | `load_registry` assertions in 6 registry tests |
| `T-0015c`| Build adapter architecture + Instagram adapter             | `COMPLETE` | 43 ingestion tests; `fetch_profile`/`fetch_page` contract tested offline |
| `T-0015d`| Raw + normalized stores with provenance and AI scaffold    | `COMPLETE` | `TestRawPersistence` — schema, null honesty, slide order, hashes |
| `T-0015e`| Checkpoint/resume + error log + manifests                  | `COMPLETE` | `TestCheckpointResume`, `TestFailureRecovery` — interrupt/resume equality with uninterrupted run |
| `T-0015f`| CLI: extract / resume / status / add, idempotent           | `COMPLETE` | `TestCLI` + manual runs recorded in the evidence report |
| `T-0015g`| Single-source live extraction test (IG001 only)            | `COMPLETE` | Run executed per instruction; outcome `blocked` (429) recorded honestly with checkpoint, error log, balanced manifest |

Acceptance criteria for the ingestion tasks are in `SPEC-ING-001` §6; each
criterion maps to a test class in `tests/ingestion/test_ingestion.py`. Criterion 11
(live single-source run) is satisfied: the run happened, its real outcome
(`blocked`) and all its artifacts were inspected and recorded. Bulk extraction is
gated on the user's access-path decision (`T-0019`).

## Acceptance criteria for the completed bootstrap tasks

- `T-0002`: all 17 required top-level areas exist, each with a `README.md` stating its
  purpose and its provenance or safety rules.
- `T-0003`: all nine governance files exist at the root, none near-empty, each
  containing its required section headings.
- `T-0004`: `.gitignore` excludes `.env`, key patterns and the runtime database;
  `model_routing.json` parses and satisfies the provider-independence rule.
- `T-0005`: script exits `0` when the repository is intact and non-zero when it is not.
- `T-0006`: validator and `unittest` suite both pass, with real output recorded.
- `T-0007`: a commit exists on `main`, the working tree is clean, and no secret is
  tracked.
- `T-0009`: both checks exit `0` with no test weakened, skipped or deleted, and the real
  output is recorded in `docs/reports/2026-09-05-bootstrap.md`. Three failures were found
  and fixed at root cause: one wrong test expectation (corrected and strengthened) and one
  unresolved placeholder (filled with verified values), which also resolved a third,
  cascading failure.
- `T-0022`: at commit `589877c` with a clean tree, both checks exit `0`; the placeholder
  markers appear only in the two files exempted by design (`scripts/validate_bootstrap.py`,
  `tests/bootstrap/test_bootstrap.py`), confirmed by `git grep`; and every change to a
  bootstrap check since `a77f793` was reviewed and found to add strictness rather than
  remove it. Two changes exist: the self-verification assertion was corrected to a string
  that is actually in `VERIFICATION_POLICY.md` and two assertions were added; and the
  ledger check was widened to count `data/raw/` records and to forbid any `SRC-` row
  claiming `AVAILABLE` while nothing is stored on disk. The zero-harvest branch is not
  vacuous: 32 sources are registered, 0 claim `AVAILABLE`, `data/raw/` does not exist, and
  `SOURCE_LEDGER.md` states `harvested items: 0`.
- `T-0032`: each of the six required tests exists as its own test class, fails on data it
  is supposed to reject, and passes on a clean record set. Proven by 30 fabricated-record
  tests (a value with no provenance, a value citing an unretrieved document, a missing
  verbatim quote, `SELF_REVIEW` as a method, an upgraded tier, a hash mismatch against a
  real temporary file, a subject with a parent, a `T1_OFFICIAL` node in the preparation
  taxonomy, an unbalanced manifest, and twenty-one more) alongside
  `test_a_clean_record_set_is_accepted` and `test_a_balanced_manifest_is_accepted`, which
  prove the checkers are not merely always-failing.
- `T-0039`: both reconciliations previously said in their own output that real counting was
  "not implemented yet" — a self-documented defect, and the only reason the bootstrap suite
  was touched at all. Check 18 now reports `25 knowledge record(s), 0 VERIFIED and declared
  as such; 0 harvested item(s) (0 stored file(s), 0 raw)`, and the replacement test drives a
  pure `reconcile()` over fabricated registries: a value without verification, a `VERIFIED`
  record with no provenance, a wrong `record_count`, a `record_count` with no record list,
  an overstated knowledge ledger, an overstated source ledger, an `AVAILABLE` row with
  nothing stored, and a ledger stating no figure at all are each rejected, while a
  consistent zero state and a consistent one-file/one-verified-record state are accepted —
  so the check is not hardwired to zero.

## Rules for this ledger

- Add a task before starting work, not after finishing it.
- Never delete a task. Mark it `BLOCKED` with the reason, or record it as superseded.
- A task whose acceptance criteria cannot be written is not yet understood well enough
  to start.
- When a status changes, record what evidence caused the change.
