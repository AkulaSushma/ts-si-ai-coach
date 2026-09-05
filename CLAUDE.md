# CLAUDE.md — Operating instructions for any AI session on this project

This file is the contract. Read it fully before doing anything else in this
repository. It is written for an AI assistant, not for the user.

## 0. Read-first order

At the start of every session, read in this order:

1. `CLAUDE.md` (this file) — the rules
2. `PROJECT_STATE.md` — where the project actually stands
3. `TASK_LEDGER.md` — what is open, what is blocked
4. `DECISIONS.md` — what has already been settled, and why
5. Then, only if relevant to the task: `VERIFICATION_POLICY.md`, `TEST_PLAN.md`,
   `SOURCE_LEDGER.md`, `KNOWLEDGE_LEDGER.md`

**Conversation history is not this project's memory.** Assume the previous session's
context is gone. If a fact is not written into a file here, it does not exist.

## 1. Who the user is

A complete beginner in coding and Git, preparing for the Telangana Police SI 2026
examination. They have explicitly asked not to hand-create folders, files, config, or
Git commands. Do the work; do not hand back instructions for them to execute.

Explain in plain language. Do not assume knowledge of terminals, virtual
environments, branches, or SQL. When something technical is unavoidable, say what it
does and why it matters to them.

## 2. Project goal

A high-accuracy AI coaching system for the Telangana Police SI 2026 exam that behaves
like an experienced coaching institute: official syllabus, PYQ database, topic and
question-family classification, historical weightage, question-identification
training, standard/fast/mental methods, confusion detection, trap awareness,
expert-derived methods, a verified knowledge base, an AI tutor, adaptive learning,
timed practice, mock exams, error analysis, spaced revision, performance analytics,
physical-preparation tracking, source provenance, and multi-model verification.

## 3. The quality principle

Optimise for being correct, verifiable, traceable, and reproducible. Do **not**
optimise for appearing complete.

Attempting a task is not completing it. A task is `COMPLETE` only when its written
acceptance criteria have each been satisfied and that satisfaction has been observed —
by running something, reading something, or testing something.

### Status vocabulary — these three words only

| Status     | Meaning                                                                    |
| ---------- | -------------------------------------------------------------------------- |
| `COMPLETE` | Every acceptance criterion satisfied and verified. Evidence recorded.        |
| `PARTIAL`  | Real progress, criteria not all met. What remains is written down.           |
| `BLOCKED`  | Cannot proceed. The blocker is named, and what would unblock it is named.    |

Never use "done", "finished", "all set", or "everything works". Never promote
`PARTIAL` or `BLOCKED` to `COMPLETE` without new evidence in the same session.

If asked whether something is finished, answer with one of the three statuses and the
evidence. An honest `PARTIAL` is a good outcome; a false `COMPLETE` corrupts every
decision built on top of it.

## 4. Never fabricate examination facts

This project concerns a real examination that affects a real career. Fabricated exam
information is the worst possible failure mode here — worse than slow progress, worse
than an empty section.

- Never state a syllabus item, mark scheme, cut-off, eligibility rule, physical
  standard, exam date, or paper structure that has not been read from a source.
- Never fill a gap with a plausible-sounding guess. Write `UNVERIFIED` or `BLOCKED`.
- "I recall that the SI exam has..." is not a source. Model recall is `T4_AI`.
- If the user states an exam fact, record it as user-asserted and still seek the
  official document. Users misremember too.

## 5. Provenance tiers — never relabel

Every factual item carries exactly one tier:

| Tier                | Source                                                  | Authority                          |
| ------------------- | ------------------------------------------------------- | ---------------------------------- |
| `T1_OFFICIAL`       | TGPRB notifications and official documents               | Authoritative                       |
| `T2_HISTORICAL_PYQ` | Actual previous-year papers and official keys            | Evidence of behaviour, not policy   |
| `T3_EXPERT`         | Educators, coaching material, books, videos              | Informed opinion, needs checking    |
| `T4_AI`             | Model-generated                                          | Unverified until checked            |

Presenting one tier as another is the most serious content error possible in this
project. A pattern seen across PYQs is not an official rule. A coaching shortcut is
not an official method. A model's explanation is not a source.

## 6. Verification

Full policy in `VERIFICATION_POLICY.md`. The short version:

- A model may not verify its own output. Verification requires a different provider,
  deterministic computation, or a source document.
- Mathematics is verified by running code over many inputs, including edge cases
  where a shortcut should break — never by re-reading the reasoning.
- Model capability is not evidence. "This is a strong model" never substitutes for a
  check. Strong models produce confident, well-formatted, wrong answers.
- Disagreement is recorded in `verification/disputes/`, not averaged away.

## 7. Research accounting

Full rules in `research/README.md`. The identity that must always balance:

```
expected = processed + inaccessible + irrelevant + duplicate + failed
```

Never claim a channel, playlist, profile, or paper set was fully processed without
these counts. Report `120 / 250` and mark it `PARTIAL`. An unbalanced manifest is
`BLOCKED`, because unaccounted items mean the totals are unknown, not merely
incomplete.

## 8. Settled technical decisions

Recorded with rationale in `DECISIONS.md`. Do not silently revisit these.

| Decision | Choice                                                              |
| -------- | ------------------------------------------------------------------- |
| `D-0001` | Single-user, local-only system. No authentication, no hosting.        |
| `D-0002` | Python 3.10+, FastAPI, SQLite via stdlib `sqlite3`                   |
| `D-0003` | Frontend framework deferred — open                                   |
| `D-0004` | English authoritative, Telugu `_te` companion fields from day one     |
| `D-0005` | Providers: Anthropic (Claude) and GLM / Z.ai (GLM 5.3)               |
| `D-0006` | Tests use stdlib `unittest`, no third-party test framework            |

## 9. Repository map

| Path               | Holds                                                            |
| ------------------ | ---------------------------------------------------------------- |
| `docs/`            | Documentation, guides, completion reports                         |
| `specs/`           | Specifications, written before code                               |
| `source_material/` | Raw acquired material — read-only after landing                   |
| `research/`        | Research plans, harvest manifests, pre-verification extractions   |
| `knowledge/`       | Verified structured knowledge — the tutor's only source           |
| `pyq/`             | Normalized PYQ records and weightage analysis                     |
| `expert_methods/`  | Educator-derived claims, unverified by default                    |
| `verification/`    | Verification runs, evidence, disputes                             |
| `agents/`          | Role definitions, prompts, routing rules                          |
| `backend/`         | Python application (empty until specs approved)                   |
| `frontend/`        | UI (empty until specs approved)                                   |
| `database/`        | Migrations and seeds (no schema yet)                              |
| `tests/`           | Automated checks                                                  |
| `scripts/`         | Standard-library operational scripts                              |
| `config/`          | Configuration, never secrets                                      |
| `physical/`        | Physical event standards and training logs                        |
| `data/`            | Runtime data, git-ignored                                         |

Each folder has its own `README.md` with rules specific to it. Read the folder README
before writing into a folder for the first time.

## 10. Context-continuity protocol

Context windows get compacted. Treat every session as one that may be cut off without
warning. Persist as you go, not at the end.

Write to disk immediately when any of these happens:

- a fact, constraint, or source is discovered
- a decision is made (record the *why*, not just the choice)
- an approach fails (negative results save future sessions real time)
- a sub-task finishes
- a test runs (record the actual output)
- roughly 20 minutes pass with nothing written

### Before ending a session or approaching a context limit

1. Persist newly discovered knowledge → `KNOWLEDGE_LEDGER.md`, `knowledge/`
2. Persist decisions → `DECISIONS.md`
3. Persist source references → `SOURCE_LEDGER.md`
4. Persist implementation status → `PROJECT_STATE.md`
5. Persist unresolved issues → `TASK_LEDGER.md`
6. Persist test results → `docs/reports/`
7. Update `PROJECT_STATE.md` header (date, session number, next action)
8. Update `TASK_LEDGER.md` statuses
9. Update the knowledge and source ledgers
10. Create a Git checkpoint

The test of a good handover: a fresh session with no memory of the conversation can
read these files and resume correctly. If it could not, the handover is incomplete.

## 11. Git conventions

The user is a Git beginner. Run Git for them; do not hand them commands.

- Branch: `main`. Commit directly to it — a single-user local project does not need a
  branching model.
- Commit message format: `type(scope): summary`, where type is one of `feat`, `fix`,
  `docs`, `chore`, `test`, `data`, `research`.
- Checkpoint after every milestone. Small frequent commits over large rare ones.
- **Before any destructive operation** (`reset --hard`, `clean -f`, force push,
  history rewrite, deleting tracked data), explain in plain language what will happen,
  what would be lost, and whether it can be undone. Then wait for explicit approval.
- Never delete anything under `source_material/`, `knowledge/`, `pyq/`,
  `expert_methods/`, `verification/`, or `data/` without explicit approval.
- Never commit `.env`, keys, or tokens. Check `git status` before every commit.

## 12. Testing discipline

1. Write acceptance criteria first.
2. Implement.
3. Test.
4. Read the failures properly — do not guess at fixes.
5. Fix the cause, not the symptom.
6. Re-test.
7. Report the real output as evidence.

Never weaken, skip, or delete a test to make something pass. If a test fails, either
the implementation is wrong or the test encodes a wrong expectation; decide which,
record the reasoning, and fix that. A failing test means `PARTIAL` or `BLOCKED`.

Structural check, runnable at any time from the project folder:

```
python scripts/validate_bootstrap.py
python -m unittest discover -s tests -v
```

## 13. Completion report format

End every substantial task with exactly these headings:

```
What was requested
What was actually completed
What was verified (and how)
What remains
What is blocked
Files created / modified
Tests executed
Test results
Evidence
Recommended next task
```

Cite real paths, real commands, real output. No vague summaries.

## 14. Prohibited actions

- Fabricating any Telangana SI examination fact
- Marking work `COMPLETE` without verified acceptance criteria
- Relabelling a provenance tier upward
- Letting a model verify its own output
- Claiming full coverage of a source without the accounting counts
- Weakening or deleting tests to produce a pass
- Committing secrets, or writing keys into tracked files
- Deleting source, knowledge, or user data without explicit approval
- Building features whose spec is not `APPROVED`
- Leaving important knowledge only in the conversation

