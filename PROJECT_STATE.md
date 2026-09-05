# PROJECT_STATE.md

> Single source of truth for where this project actually stands.
> A fresh session with no memory of any conversation must be able to resume from this
> file alone. Update it before ending any session.

## Snapshot

| Field                  | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| Project                | Telangana Police SI 2026 AI Coaching System              |
| Repository             | `D:\Projects\ts-si-ai-coach`                             |
| Last updated           | 2026-09-06                                               |
| Session                | 003 — Official knowledge foundation                      |
| Phase                  | 2 of 7 — Official source acquisition (in progress)       |
| Overall status         | `PARTIAL` — the official-knowledge **container** is `COMPLETE` and tested; the **content** is `BLOCKED` at zero facts by `B-09` (network egress). Ingestion machinery `COMPLETE`-for-scope; live Instagram extraction `BLOCKED` by `B-08` |
| Git branch             | `main`                                                   |
| Latest commit          | Session 003 verified then committed as `a209e05` → `77967da` → `fa76278`; later commits are documentation only — run `git log --oneline` for the current head |
| Structural checks      | 21 of 21 passed — `python scripts/validate_bootstrap.py` exit `0` |
| Unit tests             | 157 of 157 passed — `python -m unittest discover -s tests` (45 bootstrap + 43 ingestion + 69 official), 0 failures, 0 errors, 0 skips |
| Last re-verified       | 2026-09-06, session 003, after every file change below   |
| Official facts verified| **0 of 25** — `B-09`. No examination fact exists anywhere in this repository |
| Evidence               | `docs/reports/2026-09-06-phase1-official-foundation.md`   |

## Current Phase

**Phase 1 — Bootstrap: `COMPLETE`** (session 001).

**Phase 2 — Source acquisition: `IN PROGRESS`** (sessions 002 and 003).

Session 003 worked the official-document half of this phase, which the session
instruction called "Phase 1: official knowledge foundation" — the same work as
this file's Phase 2, named differently. Outcome, stated plainly:

- The **container** is `COMPLETE`: an approved spec, a document registry, 25
  provenance-bearing fact slots, an empty official syllabus with its emptiness
  justified, three separated weightage categories, a separate preparation
  taxonomy that forbids the official tier, three declarative schemas, a balanced
  acquisition manifest, a research plan, and 69 tests.
- The **content** is `BLOCKED`: 0 of 6 enumerated official documents retrieved,
  therefore 0 of 25 facts `VERIFIED` and 0 syllabus nodes. Cause is `B-09`, the
  environment's network egress allowlist, recorded verbatim in
  `source_material/official/RETRIEVAL_LOG.md`.

Passing container tests does not license calling the phase `COMPLETE`; that is
written into `SPEC-OFF-001` §9 so a later session cannot mistake one for the
other. No examination fact has been written anywhere in this repository.

**Phase 2 — Instagram half (session 002).** The ingestion machinery is built,
specified, and tested. Live extraction was attempted against exactly one
configured source (IG001) per instruction, and Instagram refused anonymous
access (HTTP 429 on the web profile API; the profile HTML page returns 200 but
contains only a JavaScript shell with no embedded posts). The refusal was
recorded honestly as a `blocked` checkpoint with a balanced manifest; no bypass
was attempted.


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
| **Official document registry**    | `COMPLETE` | `config/official_documents.json`: 6 documents enumerated and registered, 0 retrieved, 1 conflict recorded |
| **Official fact slots (25)**      | `COMPLETE` | `knowledge/official/required_facts.json`: `OFF-F01`–`OFF-F25`, every value `null`, every status `BLOCKED` with a reason |
| **Official fact values**          | `BLOCKED`  | `B-09` — 0 of 25 `VERIFIED`. Nothing may be written without a retrieved, hashed document |
| **Official knowledge tests**      | `COMPLETE` | `tests/official/test_official_knowledge.py` — 69 tests including 30 that feed the checkers fabricated records and require rejection |
| Official syllabus                | `BLOCKED`  | `B-09` — container exists (`knowledge/official/syllabus.json`, 0 nodes, reason recorded). Must not be guessed |
| Exam pattern / marks / duration  | `BLOCKED`  | `B-09` — `knowledge/weightage/official_marks_structure.json`, 0 entries |
| Eligibility rules                | `BLOCKED`  | `B-09` — fact slots `OFF-F07`–`OFF-F10` |
| Physical event standards         | `BLOCKED`  | `B-09` — fact slots `OFF-F18`, `OFF-F19`; `physical/standards/` stays empty. Wrong numbers here waste months of training |
| PYQ database                     | `BLOCKED`  | No papers acquired                                       |
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
| `B-01` | No official TGPRB document has been obtained                   | Acquire the current SI notification and syllabus PDF          |
| `B-02` | No previous-year papers obtained                               | Acquire PYQ papers, ideally with official answer keys          |
| `B-03` | Physical event standards unknown                               | Official document only — `physical/standards/` stays empty     |
| `B-04` | Provider model ID strings unpinned/unverified                  | Confirm exact model strings, then record under `D-0009`        |
| `B-05` | First outbound network calls made (session 002); Instagram refuses anonymous API access with HTTP 429 | Record access approach per platform; for Instagram see `B-08`  |
| `B-06` | Frontend framework undecided                                   | Write and approve the first UI spec (`D-0003`)                 |
| `B-07` | Data-model spec not written, so no schema and no database      | Write `specs/data-model/` spec (`D-0010`)                      |
| `B-08` | **Instagram refuses anonymous content access from this client** (API 429; feed 401; profile HTML is a JS shell with no posts) | User decision: either (a) provide authenticated access through a mechanism Instagram permits, (b) run extraction from a network context where anonymous access is allowed, or (c) deprioritize Instagram ingestion until (a)/(b). The offline pipeline is ready; nothing else in the subsystem needs to change |
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
| 4     | PYQ ingestion               | `BLOCKED`  | Papers normalized with balanced accounting manifests           |
| 5     | Knowledge and methods       | `BLOCKED`  | Question families with recognition cues and L2 deterministic tests |
| 6     | Backend and tutor           | `BLOCKED`  | Tutor answers only from `VERIFIED` records; L5 tests passing    |
| 7     | Practice, analytics, revision | `BLOCKED` | Timed practice, mocks, error analysis, spaced revision working  |

Phases are gated deliberately. Skipping ahead to a tutor before verified knowledge
exists would produce a system that sounds like a coaching institute and teaches
invented facts — the exact failure this architecture is designed to prevent.

## Next Action

**Get the official notification PDFs into `source_material/official/` (`B-09`).**
This is now the single highest-value action in the project: 25 fact slots, the
syllabus, the marks structure, the physical standards and conflict
`CONF-OFF-001` are all waiting on bytes, and none of them can be filled by any
amount of further engineering.

The easiest route needs no code and no network change: open
`https://tgprb.in/` in an ordinary browser, download the SI (Civil et al) 2026
notification and the supplementary notification, and save them into
`D:\Projects\ts-si-ai-coach\source_material\official\`. A later session hashes
them, ledgers them, and extracts the facts one at a time with page, section and
a verbatim quote. Two of the six registered URLs are inferred rather than
observed (`DOC-OFF-002`, `DOC-OFF-005`), so whatever the site actually serves
is the authority — the registry's URL gets corrected to match, not the other
way round.

Alternatives, if that is inconvenient: add `tgprb.in`, `www.tgprb.in` and
`www.tslprb.in` to the environment's egress allowlist and re-run retrieval, or
run retrieval from a network context where the board domain is reachable.

Still open in parallel: the Instagram access decision (`B-08`) — options (a)
authenticated access through a mechanism Instagram permits, (b) a network
context where anonymous access is allowed, or (c) deprioritize until later. The
offline pipeline is ready either way.


## Session History

| Session | Date       | Outcome                                                        |
| ------- | ---------- | --------------------------------------------------------------- |
| 001     | 2026-09-05 | Bootstrap: 58 directories, 9 governance files, 17 area READMEs, 21 structural checks and 35 L0 tests all passing, two Git checkpoints. No examination fact recorded. Full evidence in `docs/reports/2026-09-05-bootstrap.md` |
| 002     | 2026-09-05 | Ingestion subsystem built and tested (spec, registry of 32 IG sources, adapter architecture, raw/normalized stores, checkpoint/resume, error logs, manifests, CLI; 43 offline tests, all passing). Live single-source run (IG001) honestly `BLOCKED` by Instagram's anonymous-access refusal (429) — recorded, not bypassed. 78/78 tests green. Full evidence in `docs/reports/2026-09-05-ingestion-subsystem.md` |
| 003     | 2026-09-06 | Official knowledge foundation. `SPEC-OFF-001` approved; 6 official documents enumerated and registered; 25 fact slots created with every value `null`; empty official syllabus with its emptiness justified; three separated weightage categories; preparation taxonomy that forbids `T1_OFFICIAL`; three schemas; balanced acquisition manifest; `PLAN-OFF-001`; 69 new tests, 30 of them proving the checkers reject fabricated records. Two self-declared reconciliation stubs replaced with real counting (`T-0039`), adding 10 bootstrap tests. Suite 157/157 `OK`, validator 21/21 exit `0`. Retrieval `BLOCKED` by the environment's egress allowlist (`B-09`) — refusals recorded verbatim, no bypass and no coaching-site substitute. **0 examination facts written.** Full evidence in `docs/reports/2026-09-06-phase1-official-foundation.md` |

