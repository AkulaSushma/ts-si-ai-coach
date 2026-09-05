# PROJECT_STATE.md

> Single source of truth for where this project actually stands.
> A fresh session with no memory of any conversation must be able to resume from this
> file alone. Update it before ending any session.

## Snapshot

| Field                  | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| Project                | Telangana Police SI 2026 AI Coaching System              |
| Repository             | `D:\Projects\ts-si-ai-coach`                             |
| Last updated           | 2026-09-05                                               |
| Session                | 002 — Ingestion subsystem (Instagram adapter)            |
| Phase                  | 2 of 7 — Official source acquisition (in progress)       |
| Overall status         | `PARTIAL` — ingestion machinery `COMPLETE`-for-scope; live Instagram extraction `BLOCKED` by platform access refusal |
| Git branch             | `main`                                                   |
| Latest commit          | `9c11c6f` (session-001 reconciliation) + this session's ingestion commits |
| Structural checks      | 21 of 21 passed — `scripts/validate_bootstrap.py` exit `0` |
| Unit tests             | 78 of 78 passed — `unittest discover -s tests` (35 bootstrap + 43 ingestion) |
| Evidence               | `docs/reports/2026-09-05-ingestion-subsystem.md`           |

## Current Phase

**Phase 1 — Bootstrap: `COMPLETE`** (session 001).

**Phase 2 — Source acquisition: `IN PROGRESS` (session 002).** The user
directed construction of a multi-platform ingestion subsystem with Instagram
as the first adapter. The machinery is built, specified, and tested. Live
extraction was attempted against exactly one configured source (IG001) per
instruction, and Instagram refused anonymous access (HTTP 429 on the web
profile API; the profile HTML page returns 200 but contains only a JavaScript
shell with no embedded posts). The refusal was recorded honestly as a
`blocked` checkpoint with a balanced manifest; no bypass was attempted.

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
| L0 structural tests              | `COMPLETE` | 35 bootstrap tests, all pass                              |
| Git repository                   | `COMPLETE` | On `main`; checkpoints after each milestone               |
| **Ingestion spec**               | `COMPLETE` | `specs/features/ingestion-subsystem.md` (`SPEC-ING-001`) |
| **Source registry**              | `COMPLETE` | `config/source_registry.json`: 32 unique sources, all caps ≤ 299 |
| **Ingestion package**            | `COMPLETE` | `backend/app/ingestion/` — registry, adapters, storage, runner, CLI |
| **Ingestion tests (offline)**    | `COMPLETE` | 43 tests covering URL validation, 299 cap, dedup, resume, failure isolation, raw persistence, new-source registration — all pass, no network |
| **Live Instagram extraction**    | `BLOCKED`  | IG001 run: HTTP 429 on web profile API; HTML shell has no posts; no bypass attempted (see below) |
| **OCR / transcription stage**     | `BLOCKED`  | Depends on media download, which depends on live access; pipeline order puts OCR after raw storage by design |
| **GLM classification stage**     | `BLOCKED`  | Scaffolded (`ai_processing` fields, `taxonomy.py` enums); needs live raw data first |
| Official syllabus                | `BLOCKED`  | Needs an official TGPRB document. Must not be guessed    |
| Exam pattern / marks / duration  | `BLOCKED`  | Same                                                     |
| Eligibility rules                | `BLOCKED`  | Same                                                     |
| Physical event standards         | `BLOCKED`  | Same. Wrong numbers here waste months of training        |
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

**Decide the Instagram access path (`B-08`)**, because the offline pipeline is
`COMPLETE`-for-scope and only live access blocks content acquisition:

1. Option A — the user enables authenticated access using an account they
   control, through a mechanism Instagram permits for API access, recorded as
   a new decision in `DECISIONS.md` with the account's terms acknowledged.
2. Option B — run `python scripts/ingest.py resume` from a network context
   where anonymous access is allowed, keeping the same code.
3. Option C — proceed to `T-0010` (official TGPRB syllabus acquisition), the
   project's highest-value next work either way, and revisit Instagram later.

In parallel, the highest-value non-blocked work remains **acquiring the
official TGPRB SI notification and syllabus** (unblocks `B-01`, and through
it phases 3 to 5).

## Session History

| Session | Date       | Outcome                                                        |
| ------- | ---------- | --------------------------------------------------------------- |
| 001     | 2026-09-05 | Bootstrap: 58 directories, 9 governance files, 17 area READMEs, 21 structural checks and 35 L0 tests all passing, two Git checkpoints. No examination fact recorded. Full evidence in `docs/reports/2026-09-05-bootstrap.md` |
| 002     | 2026-09-05 | Ingestion subsystem built and tested (spec, registry of 32 IG sources, adapter architecture, raw/normalized stores, checkpoint/resume, error logs, manifests, CLI; 43 offline tests, all passing). Live single-source run (IG001) honestly `BLOCKED` by Instagram's anonymous-access refusal (429) — recorded, not bypassed. 78/78 tests green. Full evidence in `docs/reports/2026-09-05-ingestion-subsystem.md` |

