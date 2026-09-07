# Session 007 — Previous-year question (PYQ) acquisition and analysis preparation

**Date:** 2026-09-07 · **Session:** 007 · **Spec:** `SPEC-PYQ-001` (`APPROVED`)
**Repository:** `D:\Projects\ts-si-ai-coach` · **Branch:** `main`

## What was requested

Build the container that holds `T2_HISTORICAL_PYQ` material for the Telangana
Police SI 2026 exam, and make it mechanically impossible to (a) present a past
question as an official rule, or (b) compute a topic-weightage number that is not
counted over a real, enumerated paper set. The same standing directives applied:
do not modify or redo the completed official-source work, do not start the final
UI, do not invent any topic-wise weightage, do not extract Instagram/YouTube
knowledge yet, never silently treat a coaching-site copy as an official document,
and never claim a paper was acquired, read, extracted, or verified unless it
actually was.

## What was actually completed

The **container** is complete and green. The **content** is honestly at zero.

**Artefacts created (all `T2_HISTORICAL_PYQ` or metadata):**

- `specs/features/pyq-questions-foundation.md` — `SPEC-PYQ-001`, status `APPROVED`,
  8 acceptance criteria (`AC-1`..`AC-8`) in §9, container-vs-content rule in §9,
  provenance rules `R1`–`R5` in §3.
- `config/pyq_source_registry.json` — candidate-source registry: 3 eligible
  source types (`OFFICIAL_PUBLICATION`, `COACHING_COPY`, `CANDIDATE_RECALL`),
  eligibility rules, 3 verbatim retrieval attempts, balanced accounting
  `0 = 0 + 0 + 0 + 0 + 0`, status `BLOCKED` with a recorded reason, `sources: []`.
- `config/pyq_documents.json` — target/acquired paper registry: `retrieved_count: 0`,
  `extracted_question_count: 0`, `documents: []`, status `BLOCKED`, the
  component-coverage and eligibility requirements recorded.
- `knowledge/schemas/pyq_paper.schema.json`, `pyq_question.schema.json`,
  `pyq_weightage.schema.json` — the 3 record shapes, hand-written checks
  (`D-0006`), each carrying the honest-weightage invariants.
- `pyq/{papers,questions,weightage}/README.md` — subfolder provenance/denominator
  rules (the folders' `.gitkeep` files were already tracked from session 003).
- `research/manifests/pyq/PYQ_ACQUISITION_MANIFEST.json` — `PYQ-ACQ-007`, status
  `blocked`, identity `0 = 0 + 0 + 0 + 0 + 0`, reason recorded.
- `source_material/pyq_raw/RETRIEVAL_LOG.md` — the 3 retrieval refusals verbatim.
- `tests/pyq/__init__.py`, `tests/pyq/test_pyq_foundation.py` — 45 tests over
  `AC-1`..`AC-8`, including the anti-vacuity class.

**Acquisition outcome.** No paper was acquired; no paper identity was enumerated.
The environment's egress allowlist names one unrelated host, and web search
returned no content. All sources are therefore inaccessible from here, recorded,
not bypassed.

## What was verified (and how)

- **Validator:** `python scripts/validate_bootstrap.py` → `21 passed, 0 failed,
  21 checks total`, `RESULT: PASS`, exit `0`. Check 18 reports `71 knowledge
  record(s), 70 VERIFIED ... area files {'knowledge': 13, 'pyq': 0, ...}`.
- **PYQ module:** `python -m unittest tests.pyq.test_pyq_foundation -v` →
  `Ran 45 tests in 1.737s` `OK`.
- **Full suite:** `python -m unittest discover -s tests` → `Ran 278 tests in
  82.097s` `OK (skipped=2)`. (The `error:` lines in the stream are expected
  error-path assertions from the ingestion suite; the overall result is `OK`.)
- **Anti-vacuity, not just an empty tree:** `TestPyqCheckersRejectFabrication` has
  15 poisoned-record cases (a question with no paper, a retrieved paper whose
  bytes do not hash, a paper claiming a fixed `sha256` when the file on disk is
  `si-2024.pdf` and hashes differently, a coaching copy labelled `OFFICIAL_PUBLICATION`,
  a question without an `answer_source`, a weightage numerator with no denominator,
  a zero denominator, a `COMPLETE` entry with no paper set, a missing question
  number with no recorded issue, a paper claiming questions while `BLOCKED`, a
  question sourced from a `NONE`-extracted paper, an unbalanced manifest, a
  blocked registry with no attempt, a weightage counting an unregistered paper)
  plus `test_a_clean_record_set_is_accepted` proving the checkers are not
  always-failing. All pass.
- **No fabrication, confirmed by construction:** every registry holds zero
  records; no paper, question, or weightage entry exists in the tree; `basis` on
  any weightage entry must be `OBSERVED` and may never be `OFFICIAL`.

## What remains

- Acquiring actual previous-year paper bytes — the only thing that turns this
  container into content.
- Once bytes exist and are registered: hashing, extraction, subject/topic/
  subtopic classification with a recorded confidence, and then (and only then)
  computing observed weightage with its denominator and `partial_coverage`.
- The `pyq/` content folders are ready; no further container work is needed.

## What is blocked

- **`B-02`/`B-09` — no paper-hosting host is reachable from this environment.**
  The egress allowlist names one unrelated host (`api.lumosel.vip`); every
  attempted paper URL is refused before a request leaves the machine. The three
  refusals are recorded verbatim in `config/pyq_source_registry.json` and
  `source_material/pyq_raw/RETRIEVAL_LOG.md`. Per `D-0017` this was not routed
  around (no `curl`/`wget`/`lynx`, no Python HTTP client, no cached, archived, or
  mirrored copy).
- Consequently: `expected = processed + inaccessible + irrelevant + duplicate +
  failed` holds trivially at `0 = 0 + 0 + 0 + 0 + 0` because no source set has
  been enumerated — a documented zero, not an estimate.

## Files created / modified

Created (untracked, now staged):

| Path | Content |
| ---- | ------- |
| `specs/features/pyq-questions-foundation.md` | SPEC-PYQ-001 |
| `config/pyq_source_registry.json` | Candidate-source registry |
| `config/pyq_documents.json` | Target/acquired paper registry |
| `knowledge/schemas/pyq_paper.schema.json` | Paper record shape |
| `knowledge/schemas/pyq_question.schema.json` | Question record shape |
| `knowledge/schemas/pyq_weightage.schema.json` | Weightage output shape |
| `pyq/papers/README.md` | Papers subfolder provenance rules |
| `pyq/questions/README.md` | Questions subfolder rules |
| `pyq/weightage/README.md` | Weightage subfolder denominator rules |
| `research/manifests/pyq/PYQ_ACQUISITION_MANIFEST.json` | Acquisition manifest |
| `source_material/pyq_raw/RETRIEVAL_LOG.md` | Verbatim retrieval log |
| `tests/pyq/__init__.py` | Test package marker |
| `tests/pyq/test_pyq_foundation.py` | 45 PYQ foundation tests |

Modified (ledger updates in this session):

| Path | Change |
| ---- | ------ |
| `PROJECT_STATE.md` | Snapshot, Component Status (PYQ rows), Current Phase, `B-02` blocker, Phase Plan, Next Action, Session History (007) |
| `TASK_LEDGER.md` | `T-0013` note; new Session 007 block `T-0052`..`T-0059` |
| `DECISIONS.md` | New `D-0022` (coaching copy of a paper is `T2`, of an official document never `T1`) |

No file under `source_material/`, `knowledge/`, `pyq/`, `expert_methods/`,
`verification/`, or `data/` was deleted.

## Tests executed

1. `python scripts/validate_bootstrap.py`
2. `python -m unittest tests.pyq.test_pyq_foundation -v`
3. `python -m unittest discover -s tests`

## Test results

1. Validator: `21 passed, 0 failed, 21 checks total`, `RESULT: PASS`, exit `0`.
2. PYQ module: `Ran 45 tests in 1.737s` — `OK`.
3. Full suite: `Ran 278 tests in 82.097s` — `OK (skipped=2)` (the 2 skips are
   correct-by-design, as in earlier sessions).

## Evidence

- Commands and output above, run in the repository root.
- Registries, schemas, manifest, and retrieval log hold the zero-count blocked
  state and the verbatim refusals.
- `tests/pyq/test_pyq_foundation.py` is the mechanical proof: 45 tests, 15 of
  them fabricated-record cases exercising the checkers to confirm they can fail.

## Recommended next task

Resolve the PYQ acquisition path so that real byte files can be brought into
`source_material/pyq_raw/` and registered. The container is finished, so the next
step is acquisition, not engineering: add a paper-hosting host to the egress
allowlist, or have the user download the paper files by hand. Until then, no
weightage number, no question record, and no PYQ-similarity value may be written
(`D-0021`).

**STOP point per directive — no subsequent phase was auto-started.**
