# TASK_LEDGER.md

Every task carries acceptance criteria and exactly one status: `COMPLETE`, `PARTIAL`,
or `BLOCKED`. A task is never marked `COMPLETE` because it was attempted.

ID format: `T-####`, sequential, never reused.

## Open Tasks

| ID       | Task                                              | Status    | Depends on |
| -------- | ------------------------------------------------- | --------- | ---------- |
| `T-0010` | Acquire official TGPRB SI notification + syllabus  | `BLOCKED` | `B-01`      |
| `T-0011` | Extract official syllabus into `knowledge/syllabus/` | `BLOCKED` | `T-0010`   |
| `T-0012` | Write the data-model specification                | `BLOCKED` | `T-0011`   |
| `T-0013` | Acquire previous-year papers with keys             | `BLOCKED` | `B-02`      |
| `T-0014` | Confirm and pin provider model ID strings          | `BLOCKED` | `B-04`      |

`T-0010` is the only task that can start right now. Everything else waits on it,
because the syllabus determines the taxonomy that the schema, the PYQ classification,
and the methods all hang off.

## Blocked Tasks

| ID       | Task                              | Blocked by | Why it cannot proceed                                          |
| -------- | --------------------------------- | ---------- | -------------------------------------------------------------- |
| `T-0011` | Syllabus extraction               | `T-0010`   | Nothing to extract from. Writing one from memory is prohibited   |
| `T-0012` | Data-model spec                   | `T-0011`   | The schema must reflect the real syllabus taxonomy               |
| `T-0015` | Build the AI tutor                | `T-0011`   | A tutor with no verified knowledge would invent exam facts        |
| `T-0016` | Build the frontend                | `D-0003`   | Framework undecided; no approved UI spec                        |
| `T-0017` | Populate physical event standards | `B-03`     | Official document only. An invented standard causes real harm     |
| `T-0018` | Topic weightage analysis          | `T-0013`   | A percentage needs a counted denominator                        |

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

## Acceptance criteria for the completed bootstrap tasks

- `T-0002`: all 15 required top-level areas exist, each with a `README.md` stating its
  purpose and its provenance or safety rules.
- `T-0003`: all nine governance files exist at the root, none near-empty, each
  containing its required section headings.
- `T-0004`: `.gitignore` excludes `.env`, key patterns and the runtime database;
  `model_routing.json` parses and satisfies the provider-independence rule.
- `T-0005`: script exits `0` when the repository is intact and non-zero when it is not.
- `T-0006`: validator and `unittest` suite both pass, with real output recorded.
- `T-0007`: a commit exists on `main`, the working tree is clean, and no secret is
  tracked.

## Rules for this ledger

- Add a task before starting work, not after finishing it.
- Never delete a task. Mark it `BLOCKED` with the reason, or record it as superseded.
- A task whose acceptance criteria cannot be written is not yet understood well enough
  to start.
- When a status changes, record what evidence caused the change.
