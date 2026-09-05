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
| Session                | 001 — Bootstrap                                          |
| Phase                  | 1 of 7 — Bootstrap                                       |
| Overall status         | `COMPLETE` for bootstrap scope only                      |
| Git branch             | `main`                                                   |
| Bootstrap commit       | `a77f793` — `chore(bootstrap): establish project architecture...`  |
| Structural checks      | 21 of 21 passed — `scripts/validate_bootstrap.py` exit `0`         |
| Unit tests             | 35 of 35 passed — `unittest discover -s tests`                     |
| Evidence               | `docs/reports/2026-09-05-bootstrap.md` (verbatim run output)        |

## Current Phase

**Phase 1 — Bootstrap: `COMPLETE`.**

Scope was infrastructure only: directory architecture, governance files,
configuration, `.gitignore`, validation tooling, and a first Git checkpoint.

Explicitly excluded from this phase by instruction, and correctly not done: no UI, no
AI tutor, no bulk web research, no frameworks installed, and no Telangana SI
examination facts recorded. **The system currently knows nothing about the exam.** That
is the accurate state, not a gap that was overlooked.

## Component Status

| Component                        | Status     | Evidence / blocker                                      |
| -------------------------------- | ---------- | ------------------------------------------------------- |
| Directory architecture           | `COMPLETE` | Verified by `validate_bootstrap.py`                      |
| Governance files                 | `COMPLETE` | 9 root files, section checks pass                        |
| `.gitignore` and secret safety   | `COMPLETE` | Secret patterns asserted by tests; no keys tracked       |
| Model routing config             | `COMPLETE` | Valid JSON; independence rule mechanically enforced      |
| Bootstrap validation script      | `COMPLETE` | 21 checks, all pass; proven to fail on a broken tree      |
| L0 structural tests              | `COMPLETE` | 35 tests, all pass; run output in `docs/reports/`         |
| Git repository + first checkpoint| `COMPLETE` | Commit `a77f793` on `main`, 72 files, clean tree           |
| Official syllabus                | `BLOCKED`  | Needs an official TGPRB document. Must not be guessed    |
| Exam pattern / marks / duration  | `BLOCKED`  | Same                                                     |
| Eligibility rules                | `BLOCKED`  | Same                                                     |
| Physical event standards         | `BLOCKED`  | Same. Wrong numbers here waste months of training        |
| PYQ database                     | `BLOCKED`  | No papers acquired                                       |
| Question-family taxonomy         | `BLOCKED`  | Depends on PYQs                                          |
| Recognition training             | `BLOCKED`  | Depends on question families                             |
| Methods (standard/fast/mental)   | `BLOCKED`  | Depends on question families                             |
| Topic weightage analysis         | `BLOCKED`  | Depends on a counted PYQ set                             |
| Database schema                  | `BLOCKED`  | Data-model spec not written yet                          |
| Backend application              | `BLOCKED`  | No approved spec                                         |
| Frontend                         | `BLOCKED`  | Framework undecided (`D-0003`); no approved spec          |
| AI tutor                         | `BLOCKED`  | Depends on verified knowledge existing                    |
| Adaptive learning / mocks        | `BLOCKED`  | Depends on PYQ database                                  |
| Multi-model verification runtime | `PARTIAL`  | Policy and routing defined; no code, no API call made     |

## Blockers

The critical path is **source acquisition, not engineering.** No amount of code
produces exam knowledge.

| ID     | Blocker                                                        | What unblocks it                                            |
| ------ | -------------------------------------------------------------- | ----------------------------------------------------------- |
| `B-01` | No official TGPRB document has been obtained                   | Acquire the current SI notification and syllabus PDF          |
| `B-02` | No previous-year papers obtained                               | Acquire PYQ papers, ideally with official answer keys          |
| `B-03` | Physical event standards unknown                               | Official document only — `physical/standards/` stays empty     |
| `B-04` | Provider model ID strings unpinned/unverified                  | Confirm exact model strings, then record under `D-0009`        |
| `B-05` | No API call has ever been made from this project               | First integration task, after a spec exists                   |
| `B-06` | Frontend framework undecided                                   | Write and approve the first UI spec (`D-0003`)                 |
| `B-07` | Data-model spec not written, so no schema and no database      | Write `specs/data-model/` spec (`D-0010`)                      |

Note on `B-01`/`B-02`: these were correctly *not* attempted in this session, because
bulk research was excluded from scope. They are the highest-value next work.

## Phase Plan

| Phase | Name                        | Status     | Gate to leave the phase                                     |
| ----- | --------------------------- | ---------- | ----------------------------------------------------------- |
| 1     | Bootstrap                   | `COMPLETE` | Structure, governance, validation, first commit               |
| 2     | Official source acquisition | `BLOCKED`  | TGPRB notification and syllabus in `source_material/official/`, ledgered |
| 3     | Data model and schema       | `BLOCKED`  | Approved data-model spec, migration `0001`, L1 tests passing   |
| 4     | PYQ ingestion               | `BLOCKED`  | Papers normalized with balanced accounting manifests           |
| 5     | Knowledge and methods       | `BLOCKED`  | Question families with recognition cues and L2 deterministic tests |
| 6     | Backend and tutor           | `BLOCKED`  | Tutor answers only from `VERIFIED` records; L5 tests passing    |
| 7     | Practice, analytics, revision | `BLOCKED` | Timed practice, mocks, error analysis, spaced revision working  |

Phases are gated deliberately. Skipping ahead to a tutor before verified knowledge
exists would produce a system that sounds like a coaching institute and teaches
invented facts — the exact failure this architecture is designed to prevent.

## Next Action

**Acquire the official TGPRB SI notification and syllabus**, store them in
`source_material/official/`, register them in `SOURCE_LEDGER.md` as `T1_OFFICIAL`, and
extract the syllabus into `knowledge/syllabus/` with source locators.

This unblocks `B-01`, and through it phases 2 to 5. Nothing else in the project should
begin before it.

## Session History

| Session | Date       | Outcome                                                        |
| ------- | ---------- | -------------------------------------------------------------- |
| 001     | 2026-09-05 | Bootstrap: 58 directories, 9 governance files, 17 area READMEs, 21 structural checks and 35 L0 tests all passing, two Git checkpoints. No examination fact recorded. Full evidence in `docs/reports/2026-09-05-bootstrap.md` |
