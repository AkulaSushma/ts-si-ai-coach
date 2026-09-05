# Bootstrap completion report — 2026-09-05

| Field         | Value                                                        |
| ------------- | ------------------------------------------------------------ |
| Session       | 001 — Bootstrap                                              |
| Date          | 2026-09-05                                                   |
| Phase         | 1 of 7                                                       |
| Scope status  | `COMPLETE` for bootstrap scope only                          |
| Repository    | `D:\Projects\ts-si-ai-coach`                                 |
| Environment   | Python 3.10.12, git 2.34.1                                   |

This report exists because `TASK_LEDGER.md` cites it as the evidence for `T-0006`.
Every number and every quoted line below was copied from real command output, not
summarised from memory.

## What was requested

Bootstrap the project infrastructure and nothing more: inspect the existing `D:` drive
folder and its Git state, preserve anything already there, create the long-term
directory architecture, write nine governance files, create `.gitignore`, a
beginner-friendly `README.md`, the initial project state, task ledger, verification
policy and test plan, configure Git, verify every file created, run validation checks,
update the state and ledger files, and create the first Git checkpoint.

Explicitly excluded by instruction: installing frameworks, building any UI, building the
AI tutor, beginning bulk web research, and recording any Telangana SI examination fact
that had not been read from a source.

## What was actually completed

| # | Item                                                                     | Status     |
| - | ------------------------------------------------------------------------ | ---------- |
| 1 | Inspected the folder and Git state before writing anything                | `COMPLETE` |
| 2 | Directory architecture — 58 directories, 40 `.gitkeep` markers            | `COMPLETE` |
| 3 | Nine root governance files, each with its required sections               | `COMPLETE` |
| 4 | 17 per-area `README.md` files stating each area's provenance rules        | `COMPLETE` |
| 5 | `.gitignore`, `.env.example`, `config/model_routing.json`                 | `COMPLETE` |
| 6 | `scripts/validate_bootstrap.py` — 21 structural checks, stdlib only      | `COMPLETE` |
| 7 | `tests/bootstrap/test_bootstrap.py` — 35 L0 tests, stdlib `unittest`     | `COMPLETE` |
| 8 | Git initialised on `main`; two checkpoints; clean working tree            | `COMPLETE` |
| 9 | State and ledgers reconciled against the filesystem                      | `COMPLETE` |

Nothing about the examination itself was recorded. `KNOWLEDGE_LEDGER.md` declares
`Verified knowledge records: 0` and `SOURCE_LEDGER.md` declares `Entries: 0`, and a test
asserts that those declarations match what is actually on disk.

## What was verified, and how

Verification here means a command was run and its output read. "It looks right" is not
recorded as verification anywhere in this project.

| Claim                                        | How it was verified                                        |
| -------------------------------------------- | ---------------------------------------------------------- |
| Folder was safe to initialise in place       | `git rev-parse --is-inside-work-tree` failed; only `.claude/settings.local.json` existed |
| 58 required directories exist                | Validator check 1 — `all 58 present`                        |
| No directory is empty                        | Validator check 6; Git does not record empty directories, so each holds a `.gitkeep` or README |
| Nine governance files, none a stub           | Validator checks 2–3 — `all 9 present`, `all >= 800B`       |
| 23 required section headings present         | Validator check 4                                          |
| Routing config is valid and self-consistent  | Validator checks 7–11; `5 author/verifier pairs are independent` |
| No provider may verify its own output        | Validator check 10 plus `test_verifier_never_shares_provider_with_author` |
| No credential anywhere in the project        | Validator checks 11, 13, 14; `git check-ignore` probes below |
| Ledger counts match the filesystem           | Validator check 18 — `0 records on disk, both ledgers agree` |
| `physical/standards/` is empty               | Validator check 19 — an invented physical standard would waste months of training |
| Git is on `main` with a clean tree           | `git rev-parse --abbrev-ref HEAD`; `git status --porcelain` |
| The validator itself can fail                | `test_validator_actually_fails_on_a_broken_repository` runs the same script against an empty temporary directory and requires exit `1` |

That last row matters more than it looks. A validator that passes on an empty directory
proves nothing at all, so the suite deliberately checks that it fails when it should.

### Secret-handling probes

Run with `git check-ignore -q`, so the answers come from Git's own rule engine rather
than from reading `.gitignore` and assuming:

```
IGNORED     .env
IGNORED     data/si_coach.db
IGNORED     .claude/settings.local.json
IGNORED     secrets.key
IGNORED     api_keys.json
TRACKABLE   .env.example
TRACKABLE   data/README.md
TRACKABLE   config/model_routing.json
```

A scan of every tracked filename for `.env`, `.key`, `.pem`, `credential`, `secret` or
`token` returned: `no tracked file matches secret-like names`.

## Failures found during this session, and their root causes

Recorded because a report showing only successes is not evidence of anything. All three
of these were real failures against a real run, not hypotheticals.

### 1. A fabricated commit hash and invented test counts — caught and reversed

While drafting `PROJECT_STATE.md` I wrote a commit hash and two test-count lines
(`32 passed, 0 failed` and `24 passed, 0 failed`) **before anything had been run or
committed**. The hash belonged to a throwaway smoke-test repository, and the counts were
invented outright.

This is precisely the failure mode `CLAUDE.md` §3 and §14 exist to prevent, and it
happened anyway, on the very first file that reports status. All six invented values were
replaced with the pending-verification placeholder token, and that token was then added to
the validator's `PLACEHOLDER_MARKERS` list so that a leftover placeholder becomes a *check
failure* rather than something a future session might not notice.

(The literal token is deliberately not written out in this report, because the validator
scans every tracked text file for it. Spelling it here would make this file fail check 17
and the check would have to be weakened to accommodate the report — which is the wrong way
round.)

The durable lesson, written here so a later session inherits it: numbers that describe a
run must be pasted from that run's output. Writing the expected number first and
verifying later is how false `COMPLETE` states get created.

### 2. A test that encoded a wrong expectation

`test_self_verification_is_forbidden_in_policy` asserted that
`VERIFICATION_POLICY.md` contained the string `may never verify its own output`. The
policy's actual §6 sentence, at line 71, is:

```
The model that produced an output may never verify it. Concretely: if `DEEP_REASONING`
```

So the rule was stated correctly and clearly; the *test* named a phrasing that was never
written. Per `CLAUDE.md` §12, the decision was which of the two was wrong — and here it
was the test. The assertion was corrected to the string that genuinely exists, and two
further assertions were added rather than removed, so the test is now strictly stronger
than before:

```python
self.assertIn("produced an output may never verify it", body)
self.assertIn("SELF_REVIEW", body)
self.assertIn("not** a verification method", body)
```

No test was weakened, skipped or deleted at any point in this session.

### 3. A cascading failure that was not a separate bug

`test_validator_passes_on_this_repository` failed with `AssertionError: 1 != 0` purely
because the validator was correctly reporting the placeholder token described in
failure 1 (the literal token is deliberately not written out in this report; see the
note there). Filling in the verified values resolved both. It is logged separately only
to record that it was diagnosed rather than assumed.

This section originally contradicted itself: it spelled out the literal token that
failure 1 explicitly said was being withheld from this file, which is what made check 17
fail when the validator was re-run in session 002. The token was removed, not the check.

### 4. Environment findings worth keeping

The `D:` drive folder is reached through a FUSE mount, which does not support hardlinks,
and file deletion initially returned `Operation not permitted`. Deletion had to be
explicitly permitted before cleanup and before Git could operate without
`unable to unlink` warnings. A future session that sees those warnings should treat this
as the known cause rather than a repository problem.

## Tests executed

Both commands were run from the project folder. Neither requires anything installed
beyond Python itself (decision `D-0006`).

```
python scripts/validate_bootstrap.py
python -m unittest discover -s tests -v
```

## Test results

Structural validator, final run — exit code `0`:

```
========================================================================
Bootstrap validation - Telangana SI 2026 Coaching System
========================================================================
[PASS]  1. required directories exist                 all 58 present
[PASS]  2. governance files exist at root             all 9 present
[PASS]  3. governance files have real content         all >= 800B
[PASS]  4. governance files contain required sections 23 required sections found
[PASS]  5. every top-level area has a README          all 17 areas documented
[PASS]  6. empty directories retain .gitkeep          no required directory is completely empty
[PASS]  7. model_routing.json is valid JSON           parsed successfully
[PASS]  8. all canonical agent roles are routed       8 roles routed
[PASS]  9. every routed provider is defined           2 providers, all references resolve
[PASS] 10. no provider verifies its own output        5 author/verifier pairs are independent
[PASS] 11. routing config contains no credentials     keys referenced by environment variable only
[PASS] 12. .gitignore exists with required exclusions all 6 critical patterns present
[PASS] 13. .env.example exists and holds no real key  placeholders only, both providers documented
[PASS] 14. no credential-like string in any file      scanned project text files, none found
[PASS] 15. data/ ignored but data/README.md kept      runtime data excluded, its README retained
[PASS] 16. status vocabulary is defined and exclusive COMPLETE / PARTIAL / BLOCKED defined
[PASS] 17. no unresolved placeholder markers remain   none found
[PASS] 18. ledger counts match the filesystem         0 records on disk, both ledgers agree
[PASS] 19. physical standards folder is empty         empty, as required until an official TGPRB document
[PASS] 20. git repository is initialised on main      initialised, HEAD on main
[PASS] 21. no .env file is present in the repository  absent (user creates it locally)
========================================================================
21 passed, 0 failed, 21 checks total
RESULT: PASS - repository structure and governance are intact.
========================================================================
```

Unit tests, final run — exit code `0`:

```
Ran 35 tests in 12.429s

OK
```

Run history, in order, so the progression is on record rather than only the green result:

| Run | Command   | Result                        | Cause of failures                              |
| --- | --------- | ----------------------------- | ---------------------------------------------- |
| 1   | validator | 18 passed, 3 failed           | `tests/bootstrap` empty; placeholder; no Git yet |
| 2   | unittest  | 35 tests, `FAILED (failures=3)` | placeholder; wrong test expectation; cascade    |
| 3   | validator | 20 passed, 1 failed           | placeholder only                                |
| 4   | unittest  | 35 tests, `FAILED (failures=2)` | placeholder and its cascade                     |
| 5   | validator | **21 passed, 0 failed**, exit `0` | —                                           |
| 6   | unittest  | **Ran 35 tests, OK**, exit `0`    | —                                           |

### The 35 tests, by class

| Class                      | Tests | What it defends                                            |
| -------------------------- | ----- | ---------------------------------------------------------- |
| `TestDirectoryArchitecture` | 4    | Every area exists, is documented, and is not empty          |
| `TestGovernanceFiles`       | 7    | Nine files exist, carry required sections, no stubs, no placeholders |
| `TestModelRouting`          | 7    | All 8 roles routed, references resolve, verifier ≠ author, two-provider arbitration limit documented |
| `TestSecretSafety`          | 7    | `.env` and key patterns ignored, `.env.example` kept, no credential pattern in any file |
| `TestHonestyOfState`        | 4    | Ledgers match disk, `physical/standards/` empty, exam areas marked `BLOCKED`, no unsourced exam fact in governance |
| `TestGitRepository`         | 2    | Repository initialised, `HEAD` on `main`                    |
| `TestValidatorScript`       | 4    | Validator exists, stdlib only, passes here, **and fails on a broken tree** |

`TestHonestyOfState` is the unusual one: it tests the project's claims about itself.
`test_no_fabricated_exam_facts_in_governance` greps the governance files for patterns like
`total marks: <number>`, `cut-off: <number>` and `exam date: <digit>`, and fails if any
appears, because no `T1_OFFICIAL` source exists yet to support such a statement.

## Files created and modified

Created in this session — 73 tracked files in total. Grouped rather than listed one by
one, with the exact counts:

| Group                          | Count | Paths                                                     |
| ------------------------------ | ----- | --------------------------------------------------------- |
| Root governance files          | 9     | `CLAUDE.md`, `PROJECT_STATE.md`, `TASK_LEDGER.md`, `DECISIONS.md`, `KNOWLEDGE_LEDGER.md`, `SOURCE_LEDGER.md`, `VERIFICATION_POLICY.md`, `TEST_PLAN.md`, `README.md` |
| Per-area READMEs               | 17    | `docs/`, `specs/`, `source_material/`, `research/`, `knowledge/`, `pyq/`, `expert_methods/`, `verification/`, `agents/`, `backend/`, `frontend/`, `database/`, `tests/`, `scripts/`, `config/`, `physical/`, `data/` |
| Configuration                  | 3     | `.gitignore`, `.env.example`, `config/model_routing.json`   |
| Tooling and tests              | 3     | `scripts/validate_bootstrap.py`, `tests/bootstrap/__init__.py`, `tests/bootstrap/test_bootstrap.py` |
| Directory markers              | 40    | `.gitkeep` in otherwise-empty directories                  |
| This report                    | 1     | `docs/reports/2026-09-05-bootstrap.md`                     |

Modified after the first checkpoint: `tests/bootstrap/test_bootstrap.py` (corrected
assertion) and `PROJECT_STATE.md` (verified values replacing placeholders).

Preserved untouched: `.claude/settings.local.json`, the only file that existed before this
session. It is Git-ignored but was deliberately left on disk, since deleting a user's
existing file is not something to do silently. Recorded as decision `D-0007`.

Directory count reconciles as `58 required + repository root + .claude/ +
tests/bootstrap/__pycache__ = 61`, which is what `find . -type d` reports. The
`__pycache__` directory is a byproduct of running the tests and is Git-ignored.

## Evidence

Git state, read from the repository rather than from memory:

```
$ git rev-parse HEAD
a77f793cf8a2825d9bd86cbbd557eb0336e35c3a
$ git rev-parse --abbrev-ref HEAD
main
$ git log --oneline -n 1
a77f793 chore(bootstrap): establish project architecture, governance and validation
$ git ls-files | wc -l
72
$ git status --porcelain | wc -l
0
```

Commit `a77f793` is the bootstrap checkpoint, dated `Sat Sep 5 13:21:26 2026 +0530`, with
72 files and a clean tree. A second checkpoint, `docs(state): record verified bootstrap
results`, adds this report and the two corrections described above; its own hash is not
printed here because a commit cannot contain its own hash — `git log --oneline` will show
it.

Git identity was set locally for this repository only: `TS SI Coach Project` /
`local@ts-si-ai-coach.invalid`, with `core.autocrlf false` and `core.safecrlf false` so
that line endings are never silently rewritten on this Windows-mounted path.

## What remains

Within bootstrap scope: nothing. Everything below is later-phase work that was correctly
not attempted.

| Item                                        | Status    | Waiting on                        |
| ------------------------------------------- | --------- | --------------------------------- |
| Pin exact provider model ID strings          | `BLOCKED` | `B-04` — confirm real strings, then `D-0009` |
| Data-model specification                     | `BLOCKED` | The official syllabus taxonomy (`T-0011`) |
| Database schema and migration `0001`         | `BLOCKED` | An approved data-model spec        |
| Frontend framework decision                  | `BLOCKED` | `D-0003` remains open              |
| First API call from this project             | `BLOCKED` | `B-05` — no integration code yet   |
| L1–L5 test layers                            | `BLOCKED` | Nothing exists yet for them to test |

## What is blocked

The critical path is source acquisition, not engineering. Writing more code does not
produce exam knowledge.

| ID     | Blocker                                        | Consequence if guessed instead                        |
| ------ | ---------------------------------------------- | ----------------------------------------------------- |
| `B-01` | No official TGPRB notification or syllabus      | An invented syllabus misdirects the entire study plan   |
| `B-02` | No previous-year papers                        | No weightage, no question families, no recognition training |
| `B-03` | Physical event standards unknown                | A wrong standard wastes months of physical training      |
| `B-04` | Provider model ID strings unpinned              | Calls fail, or silently hit a different model            |

`B-01` and `B-02` were excluded from this session's scope by instruction. They are the
highest-value next work.

## Recommended next task

`T-0010` — acquire the official TGPRB SI notification and syllabus, store them unmodified
in `source_material/official/`, register them in `SOURCE_LEDGER.md` as `T1_OFFICIAL` with
retrieval date and locator, then extract the syllabus into `knowledge/syllabus/` with a
source locator on every item.

It is the only open task that can start immediately, and it unblocks phases 2 through 5.
The correct way to start it is for the user to supply the official PDF, or to confirm the
official source URL so it can be fetched and ledgered — not for a model to write a
syllabus from recall, which would be `T4_AI` content wearing a `T1_OFFICIAL` label.





