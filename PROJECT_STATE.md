# PROJECT_STATE.md

> Single source of truth for where this project actually stands.
> A fresh session with no memory of any conversation must be able to resume from this
> file alone. Update it before ending any session.

## Snapshot

| Field                  | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| Project                | Telangana Police SI 2026 AI Coaching System              |
| Repository             | `D:\Projects\ts-si-ai-coach`                             |
| Last updated           | 2026-09-07                                               |
| Session                | 008 — real-data PYQ processing (2 papers extracted, 400 questions, 13 observed-frequency entries; 7 registered papers scanned/not extracted) |
| Phase                  | 2 of 7 — Source acquisition (official SI half complete; Instagram half blocked; PYQ content partial) |
| Overall status         | `PARTIAL` — the Phase-1 official-source scope is complete: 24 of 25 official facts `VERIFIED`, official syllabus mapped (27 nodes), official marks structure populated (14 entries), supplementary-vs-original reconciliation recorded (5 records). **PYQ content is now `PARTIAL`, not zero**: 9 coaching-copy papers are registered and hashed; 2 (the 2016 Preliminary and 2016 General Studies final) have a usable text layer and were extracted into **400 question records**; the other 7 are scanned image-only/watermark-only and registered as retrieved but not extracted. **13 observed-frequency (weightage) entries** were computed over the 400 extracted questions, each explicitly marked `PARTIAL` with counted/intended coverage (2 of 9 papers, 400 questions) — no entry claims a share of the whole 9-paper corpus. Instagram knowledge still `BLOCKED` by `B-08`; the final UI/tutor are deliberately not begun. Per `D-0016`, this is honest `PARTIAL`, never `COMPLETE` |
| Git branch             | `main`                                                   |
| Latest commits         | `feat(pyq): ...` (session-007 PYQ foundation) ← `afec030` (session-006) ← `f8fd72a` (session-005) — run `git log --oneline` for the head |
| Structural checks      | 21 of 21 passed — `python scripts/validate_bootstrap.py` exit `0` |
| Unit tests             | 278 passed, 0 failures, 3 skips that are correct-by-design — `python -m unittest discover -s tests`. PYQ module alone green over the real 400-record corpus |
| PYQ papers registered  | 9 coaching-copy papers (`PAPER-PYQ-1601/1602/1801/1802/1803/2301/2302/2303/2304`) in `pyq/papers/` + `config/pyq_documents.json`, each `T2_HISTORICAL_PYQ`/`COACHING_COPY`, SHA-256 hashed, registered in `SOURCE_LEDGER` (SRC-0039–SRC-0047) |
| PYQ questions extracted | **400** (`Q-PYQ-010001`..) from the 2016 Preliminary (Q1–200) and 2016 General Studies final (Q1–200) — the only two of nine papers with a usable text layer. `pyq/questions/` is `PARTIAL` relative to the registered corpus (400 of a set whose full size is unknown) |
| PYQ observed frequency  | **13 entries** (`WGT-PYQ-0001`..`WGT-PYQ-0013`) over the 400 questions, all `PARTIAL` (2/9 papers, 400 questions), `basis OBSERVED`, `T2_HISTORICAL_PYQ`; no entry claims a share of the whole corpus. Subject sums: General Studies 299, Arithmetic/Reasoning 101 |
| Official facts verified| **24 of 25** (`OFF-F03` honestly BLOCKED — the notification defers application dates to a future press release) |
| Official syllabus      | 27 nodes, verbatim from Annexures II–III (pages 42–44) |
| Official marks structure | 14 entries (6 PWT + 8 FWE) — per-paper totals, durations, qualifying %, negative marking; no topic-wise distribution in the notification, so none recorded |
| Supplementary reconciliation | 5 records — DOC-OFF-003 amends only the upper age limit; governing general limit derived 32 as on 1 July 2026 |
| Instagram knowledge    | **0 items processed.** No Instagram raw content exists; the fixture run is explicitly marked `test_fixture: true` and no real source was touched |
| Evidence               | `docs/reports/2026-09-07-session008-pyq-realdata.md` |

## Current Phase

**Phase 1 — Bootstrap: `COMPLETE`** (session 001).

**Phase 2 — Source acquisition: `PARTIAL`.**

- **Official half (sessions 003–004):** container built in 003; in 004 the user
  supplied the two notification PDFs by browser download (`B-09` resolved for
  `DOC-OFF-002`/`DOC-OFF-003` only — the environment still cannot re-fetch),
  and both documents were read. 24 of 25 official facts are `VERIFIED` with
  document/page/section/verbatim-quote provenance, mechanically re-checked by
  `tests/official/test_official_evidence.py`. The official syllabus is mapped:
  27 nodes from Annexures II–III, verbatim wording, no invented layer.
  `OFF-F03` (application dates) is honestly `BLOCKED`: the notification defers
  the dates to a future press release.
- **Instagram half (session 002):** machinery `COMPLETE`; live access still
  `BLOCKED` (`B-08`), recorded not bypassed.
- **Downstream pipeline (session 005):** `SPEC-KNW-001` implemented and tested
  — raw content → processing → GLM extraction schema → atomic candidate
  knowledge → relevance scoring → dedup/corroboration → verification queue.
  Fully operable offline via the committed fixture; **zero Instagram content
  processed**; nothing marked `VERIFIED` by it.
- **PYQ half (session 007 container, session 008 content):** container
  `COMPLETE` under `SPEC-PYQ-001`; content now `PARTIAL`, not zero. In session
  008 the nine real coaching-copy papers supplied under
  `source_material/pyq_raw/` were registered (`pyq/papers/`, `SOURCE_LEDGER`
  SRC-0039–SRC-0047, SHA-256 hashed). Two of the nine have a usable text layer
  — the 2016 Preliminary and the 2016 General Studies final — and were fully
  extracted into **400 question records** (`pyq/questions/`). The other seven
  are scanned image-only/watermark-only, registered as retrieved but not
  extracted, so `pyq/questions/` is honest `PARTIAL`. **13 observed-frequency
  entries** (`WGT-PYQ-0001`..`WGT-PYQ-0013`) were computed over the 400
  questions, each explicitly `PARTIAL` with counted/intended coverage; no entry
  claims a share of the whole 9-paper corpus. The source-host registry stays
  `BLOCKED` (egress allowlist); recorded, not routed around (`D-0017`).

## The knowledge processing pipeline (new in session 005)

Implements `specs/features/knowledge-processing-pipeline.md` (`SPEC-KNW-001`).

- **Layers kept separate** — raw (ingestion, immutable) → processed
  (`data/processed/`) → candidate knowledge + questions
  (`data/knowledge/candidates|questions/`, `UNVERIFIED`) → concepts
  (`data/knowledge/concepts/`, one concept, many supporting sources) →
  verification queue (`data/knowledge/verification_queue.jsonl`). The trusted
  `knowledge/` layer is untouched by this pipeline.
- **Content processor** — null-safe text assembly (caption, slide OCR in
  order, transcript, on-screen); empty content skipped with a reason and zero
  model calls; OCR/transcription are interfaces only until raw media exists.
- **GLM extraction** — strict machine-checkable output schema
  (`extraction_schema.py`, field-path errors, enum-enforced); versioned prompt
  `knowledge-extraction-v1` (atomic extraction, never summarize, never
  invent, questions separate, source-claims-not-truth); routed via the new
  `KNOWLEDGE_EXTRACTION` role in `config/model_routing.json` (GLM 5.3,
  env-keyed; independence pair with `VERIFICATION` enforced by the validator).
  Tests use a scripted client; the live client requires `GLM_API_KEY` and
  reports honestly when absent.
- **Candidate knowledge** — one record per atomic unit with full provenance
  (`source_id, content_id, url, published_at, extraction model, prompt
  version, timestamp, T3_EXPERT`), deterministic ids, `verification_status`
  `UNVERIFIED` (the pipeline structurally cannot create anything else).
- **Questions/MCQs** — extracted separately; answers stored only when
  `STATED_BY_SOURCE`; options never invented.
- **Scoring** — deterministic rules in `docs/relevance_scale.md` v1;
  `pyq_similarity` is `null` until PYQs exist (no denominator, no number);
  `constable_relevance` carries an explicit PROVISIONAL basis because the
  Constable notification is not yet retrieved.
- **Dedup & corroboration** — concept keys over stopword-stripped,
  curated-synonym-canonicalized content words plus knowledge type
  (`config/dedup_synonyms.json` is reviewed data; "not" is never dropped);
  one concept holds every supporting source (`source_count`,
  `source_diversity`); corroboration is explicitly not verification.
- **Verification queue** — append-only; records the required verifier
  provider (resolved `AUTO_NOT_AUTHOR`, differing from the author's);
  performs and can perform no verification.
- **Batch + resume** — checkpoint after every item; resume skips
  dispositioned items and retries failed ones; prompt/model version is part
  of the checkpoint scope so re-extraction is always explicit. Cost controls:
  empty content, already-processed, and within-run duplicate text never reach
  the model.
- **CLI** — `python scripts/process_knowledge.py process --fixture |
  --source IG001 | --platform instagram`, `status`. The `--fixture` run is
  the offline "first GLM test" against the committed dataset.


## The ingestion subsystem (new in session 002)

Implements `specs/features/ingestion-subsystem.md` (`SPEC-ING-001`).

- **Source registry** — `config/source_registry.json`: 32 unique Instagram
  coaching/education profiles (IG001–IG032), each `max_items: 299` (hard cap
  299, configurable 1..299). A new URL is added by `python scripts/ingest.py
  add --url ...` or by editing the JSON; no code change. `sudheergenzacademy`
  (duplicated in the original user list) is stored once, as instructed.
- **Adapter architecture** — `backend/app/ingestion/adapters/base.py` defines
  the platform-neutral `SourceAdapter` interface; `adapters/instagram.py` is
  the first implementation. YouTube/Telegram/website/PDF adapters later reuse
  the same interface; runner, storage, and CLI need no changes.
- **Raw store** — `data/raw/instagram/<source_id>/<content_id>.json`, atomic
  write-once records preserving captions, hashtags, per-slide media ordering,
  accessibility captions, engagement, and the full original platform JSON
  under `platform_data`. Unavailable fields are `null`, never invented.
  Git-ignored per `D-0008`.
- **Normalized store** — `data/normalized/instagram/...` adds provenance
  (`T3_EXPERT` tier for these coaching sources) and content/URL hashes for
  dedup, plus an `ai_processing` scaffold with every GLM-classification field
  null pending the later AI stage. Git-ignored runtime data.
- **Checkpointing** — `data/ingestion/checkpoints/<source_id>.json` written
  after every item and page: discovered/extracted/duplicate/failed/inaccessible
  counts, per-item dispositions, per-edge cursors, resume state. `resume`
  re-walks only what was not finished; completed sources are skipped.
- **Error log** — `data/ingestion/errors/<source_id>.jsonl`: source, content
  URL, error type, timestamp, retry count, status — append-only.
- **Manifests** — `research/manifests/instagram/<id>-<ts>.json` satisfy the
  research accounting identity with an `expected_justification`.
- **Commands** — `python scripts/ingest.py extract [--source ID | --url URL]`,
  `resume`, `status`, `add`. All idempotent, standard library only (`D-0006`).

## Component Status

| Component                        | Status     | Evidence / blocker                                      |
| -------------------------------- | ---------- | ------------------------------------------------------- |
| Directory architecture           | `COMPLETE` | Verified by `validate_bootstrap.py`                      |
| Governance files                 | `COMPLETE` | 9 root files, section checks pass                        |
| `.gitignore` and secret safety   | `COMPLETE` | Secret patterns asserted by tests; no keys tracked       |
| Model routing config             | `COMPLETE` | Valid JSON; independence rule mechanically enforced      |
| Bootstrap validation script      | `COMPLETE` | 21 checks, all pass; proven to fail on a broken tree      |
| L0 structural tests              | `COMPLETE` | 45 bootstrap tests, all pass (35 original + 10 that replaced a self-declared reconciliation stub) |
| Ledger↔disk reconciliation       | `COMPLETE` | Validator check 18 and `TestHonestyOfState` both recompute real counts; 10 fabricated-data cases prove the check can fail (`T-0039`) |
| Git repository                   | `COMPLETE` | On `main`; checkpoints after each milestone               |
| **Ingestion spec**               | `COMPLETE` | `specs/features/ingestion-subsystem.md` (`SPEC-ING-001`) |
| **Source registry**              | `COMPLETE` | `config/source_registry.json`: 32 unique sources, all caps ≤ 299 |
| **Ingestion package**            | `COMPLETE` | `backend/app/ingestion/` — registry, adapters, storage, runner, CLI |
| **Ingestion tests (offline)**    | `COMPLETE` | 43 tests covering URL validation, 299 cap, dedup, resume, failure isolation, raw persistence, new-source registration — all pass, no network |
| **Live Instagram extraction**    | `BLOCKED`  | IG001 run: HTTP 429 on web profile API; HTML shell has no posts; no bypass attempted (see below) |
| **OCR / transcription stage**     | `BLOCKED`  | Depends on media download, which depends on live access; pipeline order puts OCR after raw storage by design |
| **GLM classification stage**     | `BLOCKED`  | Scaffolded (`ai_processing` fields, `taxonomy.py` enums); needs live raw data first |
| **Official knowledge spec**       | `COMPLETE` | `specs/features/official-knowledge-foundation.md` (`SPEC-OFF-001`), status `APPROVED` |
| **Official document registry**    | `COMPLETE` | `config/official_documents.json`: 6 registered, **2 RETRIEVED** (DOC-OFF-002, DOC-OFF-003, user-supplied downloads, hashed), 4 blocked by `B-09` |
| **Official fact slots (25)**      | `COMPLETE` | `knowledge/official/required_facts.json`: `OFF-F01`–`OFF-F25` with provenance structure |
| **Official fact values**          | `PARTIAL` | **24 of 25 `VERIFIED`** with document/page/quote; OFF-F03 honestly `BLOCKED` (notification defers application dates to a press release) |
| **Official fact evidence test**   | `COMPLETE` | `tests/official/test_official_evidence.py` — 4 tests; every quote (incl. `supporting[]`) reproducible from the cited artefact page; stored PDFs hash-checked |
| **Official knowledge tests**      | `COMPLETE` | `tests/official/test_official_knowledge.py` — 82 tests (69 original + 13 reconciliation/fabrication), 2 skips correct-by-design |
| Official syllabus                | `COMPLETE` | 27 nodes, verbatim from Annexures II–III (pages 42–44), generated with quotes located in the artefact at write time |
| **Official marks structure**      | `COMPLETE` | `knowledge/weightage/official_marks_structure.json` — 14 entries (6 PWT + 8 FWE) from DOC-OFF-002 pages 19–24 & 42–44; notification prints no topic-wise distribution, so `official_topic_weightage_provided_by_notification: false` |
| **Supplementary reconciliation**  | `COMPLETE` | `knowledge/official/current_official.json` — 5 records (REC-001–005); DOC-OFF-003 amends only the upper age limit via GO Ms No. 122 (+2 on GO Ms No. 87's +5); governing general upper limit derived 32 as on 1 July 2026; no conflict |
| Exam pattern / marks / duration  | `VERIFIED` | Covered by verified facts OFF-F12–OFF-F14 |
| Eligibility rules                | `VERIFIED` | Covered by verified facts OFF-F07–OFF-F10 |
| Physical event standards         | `VERIFIED` | Covered by verified facts OFF-F18, OFF-F19; `physical/standards/` still empty pending its own structured extraction |
| **Knowledge pipeline spec**       | `COMPLETE` | `specs/features/knowledge-processing-pipeline.md` (`SPEC-KNW-001`), `APPROVED` |
| **Knowledge pipeline package**    | `COMPLETE` | `backend/app/knowledge/` — processor, schema, prompt v1, routed client, candidates, scoring, dedup, queue, pipeline |
| **Knowledge pipeline tests**      | `COMPLETE` | 59 tests covering all 18 SPEC-KNW-001 criteria; zero network calls |
| **Fixture GLM test**              | `COMPLETE` | Offline deterministic run: 9 items → 7 candidates, 2 questions, 6 concepts, 7 queued; cross-source merge and idempotency verified |
| **GLM classification stage**      | `READY`   | Live execution blocked on real raw content (`B-08`) — the schema, prompt and routing are tested; no live call has been made |
| **PYQ spec**                     | `COMPLETE` | `specs/features/pyq-questions-foundation.md` (`SPEC-PYQ-001`), `APPROVED`, 8 acceptance criteria, container-vs-content rule in §9 |
| **PYQ source registry**          | `COMPLETE` | `config/pyq_source_registry.json` — 3 eligible source types, eligibility rules, 3 verbatim retrieval attempts, balanced accounting `0 = 0+0+0+0+0`, status `BLOCKED` |
| **PYQ document registry**        | `COMPLETE` | `config/pyq_documents.json` — target/acquired paper registry, `retrieved_count: 0`, `documents: []`, `status: BLOCKED` with recorded reason |
| **PYQ content folders**          | `COMPLETE` | `pyq/{papers,questions,weightage}/` — READMEs and `.gitkeep` only (already tracked), each with its provenance/denominator rules |
| **PYQ schemas (3)**              | `COMPLETE` | `knowledge/schemas/pyq_paper.schema.json`, `pyq_question.schema.json`, `pyq_weightage.schema.json` — hand-written checks, no third-party validator (`D-0006`) |
| **PYQ acquisition manifest**     | `COMPLETE` | `research/manifests/pyq/PYQ_ACQUISITION_MANIFEST.json` — `PYQ-ACQ-007`, status `blocked`, identity `0 = 0+0+0+0+0`, reason recorded |
| **PYQ retrieval log**            | `COMPLETE` | `source_material/pyq_raw/RETRIEVAL_LOG.md` — the 3 refusals verbatim; no bypass, no curl/wget/lynx/Python client, no archived copy (`D-0017`) |
| **PYQ foundation tests**         | `COMPLETE` | `tests/pyq/test_pyq_foundation.py` — 45 tests over the 8 acceptance criteria (AC-1..AC-8), incl. anti-vacuity `TestPyqCheckersRejectFabrication` (15 poisoned-record cases) + clean-data proof; all pass, no network |
| PYQ database                     | `BLOCKED`  | No papers acquired — container built, content blocked by `B-02` (egress allowlist) |
| Question-family taxonomy         | `BLOCKED`  | Depends on PYQs                                          |
| Recognition training             | `BLOCKED`  | Depends on question families                             |
| Methods (standard/fast/mental)   | `BLOCKED`  | Depends on question families                             |
| Topic weightage analysis         | `BLOCKED`  | Depends on a counted PYQ set                             |
| Database schema                  | `BLOCKED`  | Data-model spec not written yet (D-0010)                 |
| Backend application              | `PARTIAL`  | `backend/app/ingestion/` exists and is tested; FastAPI layer still awaits an approved spec |
| Frontend                         | `BLOCKED`  | Framework undecided (`D-0003`); no approved spec          |
| AI tutor                         | `BLOCKED`  | Depends on verified knowledge existing                    |
| Adaptive learning / mocks        | `BLOCKED`  | Depends on PYQ database                                  |
| Multi-model verification runtime | `PARTIAL`  | Policy and routing defined; first real API call made from this project this session (Instagram, blocked 429) — `B-05` now has its first data point |

## Blockers

The critical path is **source acquisition, not engineering.** No amount of code
produces exam knowledge.

| ID     | Blocker                                                        | What unblocks it                                            |
| ------ | -------------------------------------------------------------- | ------------------------------------------------------------ |
| `B-01` | ~~No official TGPRB document has been obtained~~ **CLOSED in session 004** for the SI notification and its supplement | Two documents stored and hashed; the other four remain blocked (`B-09`) |
| `B-02` | No previous-year papers obtained — **PYQ container built (session 007), content at zero**. No paper has been acquired because no source host is reachable (egress allowlist); no paper identity has been enumerated | Acquire PYQ papers, ideally with official answer keys. The container (`SPEC-PYQ-001`, registries, schemas, manifest, retrieval log, 45 tests) is finished; what is needed is bytes, which only a reachable host or a manual download into `source_material/pyq_raw/` can supply. Add a paper-hosting host to the egress allowlist (see `B-09`) |
| `B-03` | Physical event standards — **resolved in substance**: OFF-F18/OFF-F19 verified from the notification; structured `physical/standards/` records still to be written | Data entry from the already-verified facts; no new source needed |
| `B-04` | Provider model ID strings unpinned/unverified                  | Confirm exact model strings, then record under `D-0009`. The GLM string `glm-5.3` remains `UNVERIFIED_STRING` until a live call is made |
| `B-05` | First outbound network calls made; Instagram refuses anonymous API access with HTTP 429 | For Instagram see `B-08`; the knowledge pipeline's live GLM call has not been attempted (no key set in this environment) |
| `B-06` | Frontend framework undecided                                   | Write and approve the first UI spec (`D-0003`)                 |
| `B-07` | Data-model spec not written, so no schema and no database      | Write `specs/data-model/` spec (`D-0010`). The knowledge pipeline's file-based record shapes (candidates/concepts/questions) are a ready 1:1 source for the migration |
| `B-08` | **Instagram refuses anonymous content access from this client** (API 429; feed 401; profile HTML is a JS shell with no posts) | User decision: (a) authenticated access through a mechanism Instagram permits, (b) a network context where anonymous access is allowed, or (c) defer. The ingestion AND knowledge pipelines are both ready end-to-end; nothing downstream needs to change |
| `B-09` | **No official TGPRB / TSLPRB document can be fetched from this environment.** Network egress is restricted to an allowlist naming exactly one host (`tabitoken.com`), unrelated to this project. Every board URL is refused before a request leaves the machine — host-level, not rate limiting, not a login wall, not an outage | Any one of: (a) add `tgprb.in`, `www.tgprb.in`, `www.tslprb.in` to the environment's egress allowlist and re-run retrieval; (b) download the notification PDFs by hand into `source_material/official/` — the registry already holds the expected file identities, so hashing and fact extraction proceed offline with no code change; (c) run retrieval from a network context where the board domain is reachable. This blocker gates all 25 `OFF-F##` facts, the official syllabus, the official marks structure, `physical/standards/`, and conflict `CONF-OFF-001` |

Note on `B-09`: `B-01` records the *absence* of an official document; `B-09`
records the *reason* it is still absent after a real attempt. Both stay open —
satisfying `B-09` is what makes `B-01` closable. Six documents are enumerated
and registered in `config/official_documents.json`, so the work waiting on the
other side of `B-09` is extraction, not discovery.


Note on `B-08`: the refusal was probed politely (delays, retry-with-backoff,
fresh user agents) and **no bypass was attempted** — no credential scraping,
no aggressive requesting, no fabricated API parameters beyond one 400-rejected
GraphQL probe that was abandoned immediately. The blocked checkpoint, error
log, and manifest for IG001 are the evidence trail.

## Phase Plan

| Phase | Name                        | Status     | Gate to leave the phase                                     |
| ----- | --------------------------- | ---------- | ----------------------------------------------------------- |
| 1     | Bootstrap                   | `COMPLETE` | Structure, governance, validation, first commit               |
| 2     | Official source acquisition | `IN PROGRESS` | TGPRB notification and syllabus in `source_material/official/`, ledgered; Instagram access decision resolved |
| 3     | Data model and schema       | `BLOCKED`  | Approved data-model spec, migration `0001`, L1 tests passing   |
| 4     | PYQ ingestion               | `BLOCKED`  | Container built (session 007); gate is papers normalized with balanced accounting manifests, which needs acquired bytes |
| 5     | Knowledge and methods       | `BLOCKED`  | Question families with recognition cues and L2 deterministic tests |
| 6     | Backend and tutor           | `BLOCKED`  | Tutor answers only from `VERIFIED` records; L5 tests passing    |
| 7     | Practice, analytics, revision | `BLOCKED` | Timed practice, mocks, error analysis, spaced revision working  |

Phases are gated deliberately. Skipping ahead to a tutor before verified knowledge
exists would produce a system that sounds like a coaching institute and teaches
invented facts — the exact failure this architecture is designed to prevent.

## Next Action

**Session 007 built the PYQ container and is a STOP point per the standing
directive.** The PYQ foundation spec (`SPEC-PYQ-001`) is `APPROVED`, harmless to
the completed Phase-1 official-source work, and green. It also made no attempt
at Instagram/YouTube knowledge and no fabrications — but it produced **no
content**: zero papers acquired, zero questions extracted, zero weightage
computed, because no paper-hosting host is reachable (egress allowlist) and web
search returned no content. The acquisition path is `BLOCKED` by `B-02`/`B-09`.

The next move is the user's decision on which blocker to take up. The PYQ
container is finished, so the work waiting on the other side of `B-02` is
acquisition, not engineering:

- Option A — add a paper-hosting host (e.g. `tgprb.in`, or a named coaching
  host) to the environment's egress allowlist, then re-run retrieval; the
  registries and log already hold the intent and the attempt history.
- Option B — download the paper files by hand into `source_material/pyq_raw/`
  and register them; hashing, validation and question extraction then proceed
  offline with no code change.
- Option C — defer PYQs; the other high-value alternatives are (1) writing the
  data-model spec (`D-0010`) now that real record shapes exist, (2) resolving
  `CONF-OFF-001` once an official board URL is reachable, or (3) the Instagram
  access decision (`B-08`).

No code change is required for any option. **Do not begin another phase without
the user's explicit go-ahead.**


## Session History

| Session | Date       | Outcome                                                        |
| ------- | ---------- | --------------------------------------------------------------- |
| 001     | 2026-09-05 | Bootstrap: 58 directories, 9 governance files, 17 area READMEs, 21 structural checks and 35 L0 tests all passing, two Git checkpoints. No examination fact recorded. Full evidence in `docs/reports/2026-09-05-bootstrap.md` |
| 002     | 2026-09-05 | Ingestion subsystem built and tested (spec, registry of 32 IG sources, adapter architecture, raw/normalized stores, checkpoint/resume, error logs, manifests, CLI; 43 offline tests, all passing). Live single-source run (IG001) honestly `BLOCKED` by Instagram's anonymous-access refusal (429) — recorded, not bypassed. 78/78 tests green. Full evidence in `docs/reports/2026-09-05-ingestion-subsystem.md` |
| 003     | 2026-09-06 | Official knowledge foundation. `SPEC-OFF-001` approved; 6 official documents enumerated and registered; 25 fact slots created with every value `null`; empty official syllabus with its emptiness justified; three separated weightage categories; preparation taxonomy that forbids `T1_OFFICIAL`; three schemas; balanced acquisition manifest; `PLAN-OFF-001`; 69 new tests, 30 of them proving the checkers reject fabricated records. Two self-declared reconciliation stubs replaced with real counting (`T-0039`), adding 10 bootstrap tests. Suite 157/157 `OK`, validator 21/21 exit `0`. Retrieval `BLOCKED` by the environment's egress allowlist (`B-09`) — refusals recorded verbatim, no bypass and no coaching-site substitute. **0 examination facts written.** Full evidence in `docs/reports/2026-09-06-phase1-official-foundation.md` |
| 004     | 2026-09-06 | User supplied the two notification PDFs by browser download (`B-09` resolved for those two documents only). Reproducible page-marked extraction artefacts committed with digests; **24 of 25 official facts `VERIFIED`** with document/page/section/verbatim-quote provenance; `OFF-F03` honestly `BLOCKED` (notification defers application dates). **Official syllabus mapped: 27 nodes**, verbatim from Annexures II–III, quotes located in the artefact at write time. New `tests/official/test_official_evidence.py` mechanically re-checks every quote and the stored-PDF hashes; an `--check` digest mismatch was investigated and recorded as a pdftotext version difference (xpdf 4.06 vs poppler 22.02.0), not content drift. Suite 161/161 `OK` |
| 005     | 2026-09-06 | Knowledge processing pipeline (`SPEC-KNW-001`): raw → processed → GLM extraction schema (`knowledge-extraction-v1` prompt, strict enums, field-path errors) → atomic candidates + questions with full provenance → deterministic documented scoring → concept dedup with cross-source corroboration → UNVERIFIED-only verification queue with provider separation. Batch checkpoint/resume, idempotency and cost controls (empty and duplicate content never reach the model). `KNOWLEDGE_EXTRACTION` role added to routing with enforced independence pair. 59 new tests over all 18 criteria; offline fixture run verified (9 items → 7 candidates, 2 questions, 6 concepts, cross-source merge proven). **Zero Instagram content processed, zero network calls, nothing marked VERIFIED.** Suite 220/220 `OK`, validator 21/21. Evidence in `docs/reports/2026-09-06-session005-knowledge-pipeline.md` |
| 006     | 2026-09-07 | **Phase-1 official-source completion.** Closed the two remaining official gaps: (a) `knowledge/weightage/official_marks_structure.json` — 14 verified entries (6 PWT + 8 FWE) from DOC-OFF-002 pages 19–24 & 42–44; the notification prints no topic-wise distribution, so `official_topic_weightage_provided_by_notification: false` (T-0037 → `COMPLETE`); (b) `knowledge/official/current_official.json` — 5 reconciliation records settling the supplementary (DOC-OFF-003) against the original (DOC-OFF-002): only the upper age limit is amended (GO Ms No. 122, +2 years on GO Ms No. 87's +5), governing general upper limit derived 32 as on 1 July 2026, no conflict (T-0051). Added 13 tests (6 reconciliation + 7 fabricated-data anti-vacuity) to `test_official_knowledge.py` and extended `test_official_evidence.py` to re-check every quote across all three official registries. Suite 233/233 `OK` (2 skips correct-by-design), validator 21/21. Evidence in `docs/reports/2026-09-07-session006-official-completion.md`. **STOP point per directive — no phase auto-started.** |
| 007     | 2026-09-07 | **PYQ acquisition & analysis preparation (`SPEC-PYQ-001`).** Built the container that holds `T2_HISTORICAL_PYQ` material and makes fabricated weightage mechanically impossible: source registry (`config/pyq_source_registry.json`), document registry (`config/pyq_documents.json`), 3 schemas (paper/question/weightage), 3 content READMEs, acquisition manifest (`PYQ-ACQ-007`), verbatim retrieval log (3 refusals), and 45 tests over the 8 acceptance criteria — 15 of them anti-vacuity cases proving the checkers reject fabricated papers/questions/weightage. **Content is `BLOCKED` at zero**: 0 papers acquired, 0 discovered, all sources inaccessible (egress allowlist), 0 questions extracted, 0 hashes, no weightage computed. Suite 278/278 `OK` (2 skips correct-by-design), validator 21/21; PYQ module alone 45/45. Did **not** modify or redo the completed official-source work, did **not** start the final UI, did **not** invent topic-wise weightage, did **not** extract Instagram/YouTube knowledge, did **not** treat coaching-site copies as official. Evidence in `docs/reports/2026-09-07-session007-pyq-foundation.md`. **STOP point per directive.** |