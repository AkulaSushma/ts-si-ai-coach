# Session 008 — real-data PYQ processing

## What was requested

Process the real previous-year question paper PDFs supplied under
`source_material/pyq_raw/`. Stop pretending PYQ content is `BLOCKED` at zero
once real papers are in hand; but never invent missing papers, never compute
weightage over an incomplete or unknown corpus without marking partial coverage,
never claim a PDF was processed unless it was actually opened and extracted, never
claim a question was classified unless it exists in the extracted corpus, and never
state a weightage without showing numerator, denominator, and paper set.

## What was actually completed

- **Registered the nine real papers.** Each PDF was SHA-256 hashed and registered
  in `config/pyq_documents.json` and `pyq/papers/PAPER-PYQ-*.json`, and ledgered in
  `SOURCE_LEDGER.md` as `SRC-0039`..`SRC-0047`, all `T2_HISTORICAL_PYQ` /
  `COACHING_COPY`, never relabelled as board-issued.
- **Extracted the two extractable papers.** The 2016 Preliminary
  (`PAPER-PYQ-1601`) and the 2016 General Studies final (`PAPER-PYQ-1602`) are the
  only two of the nine with a usable text layer. They yielded **400 question
  records** (`Q-PYQ-010001`…), every record `T2_HISTORICAL_PYQ`, tied to a
  registered paper, with `answer_source` present on all 400 (`UNVERIFIED` where no
  key was seen — a visible fact, not a silent assumption).
- **Classified the extracted questions.** Each record carries a `classification`
  block recording subject and topic, the keyword/pattern basis, and a confidence
  of `NEAR` or `AMBIGUOUS`. Where a topic could not be resolved it is kept as
  `topic: null` with `unresolved: true` rather than guessed.
- **Computed observed frequency with explicit coverage.** 13 entries
  (`WGT-PYQ-0001`..`WGT-PYQ-0013`) over the 400 questions. Every entry is
  `PARTIAL`, states `papers_included` = the two 2016 papers, `years_included` =
  2016, `denominator` = 400, and a `partial_coverage` of 2 of 9 papers and 400
  questions. No entry claims a share of the whole nine-paper corpus. `basis` is
  `OBSERVED`, `provenance_tier` `T2_HISTORICAL_PYQ`; the two never mix with the
  official marks structure.

## What was verified (and how)

- Subject totals over the 400 records (recomputed from the files):
  General Studies **299**, Arithmetic & Test of Reasoning / Mental Ability **101**.
- Topic totals: GS|none 122, Arith|Arithmetic 48, GS|Geography 48, GS|Telangana
  GK & Culture 37, Arith|Test of Reasoning 33, Arith|none 20, GS|Indian Polity &
  Constitution 20, GS|Indian History 20, GS|Indian Economy 16, GS|Physics 12,
  GS|Chemistry 11, GS|Biology / Life Science 7, GS|Sports & Awards 6. These sum to
  400.
- Classification confidence: `NEAR` 231, `AMBIGUOUS` 169. Counted unresolved
  topics: 142.
- `tests/pyq/test_pyq_foundation.py` enforces: every weightage entry has a
  denominator, no entry uses an unregistered paper, no entry labels an observed
  frequency as official, no question exists without a paper, and every registered
  extraction count matches the records on disk. All green over the real corpus.
- `scripts/validate_bootstrap.py` and `tests/bootstrap/test_bootstrap.py` both
  agree the ledger figures match the filesystem. See "Tests executed" below.
- The two extractable PDFs and the provenance were confirmed by reading the actual
  PDF pages, not by assuming a text layer existed — the seven unpublished papers
  were read and found to be scanned image-only or watermark-only, and were not
  added to `pyq/questions/` for that reason.

## What remains

- `pyq/questions/` is `PARTIAL` relative to the registered corpus: 400 records, but
  the full question count of the other seven registered papers is unknown (they are
  scanned). A later OCR pass over those seven, or an extractable copy, would raise
  the count.
- The observed-frequency table is limited to the two 2016 papers; it cannot be
  extended without more extracted papers.
- No question has a verified `correct_answer`: every record's `answer_source` is
  `UNVERIFIED` or a coaching key has not been mechanically confirmed, so no question
  is yet marked answered.

## What is blocked

- **`B-02` (egress allowlist)** — no board or coaching host is reachable, so the
  broader universe of Telangana Police SI previous-year papers beyond these nine
  supplied files is unenumerable. Recorded verbatim; not routed around (`D-0017`).
- The 7 scanned papers (`SRC-0041`..`SRC-0047`) are registered as retrieved but not
  extracted; extracting them needs an OCR/text-layer source, not available here.
- `Instagram` knowledge (`B-08`) and source-host registry remain `BLOCKED`.

## Files created / modified

Created (untracked before this session):
- `pyq/papers/PAPER-PYQ-1601.json` … `PAPER-PYQ-2304.json` (9 paper records)
- `pyq/questions/Q-PYQ-010001.json` … (400 question records)
- `pyq/weightage/WGT-PYQ-0001.json` … `WGT-PYQ-0013.json` (13 entries)

Modified:
- `SOURCE_LEDGER.md` (harvested items 2→11; added SRC-0039..SRC-0047 rows)
- `config/pyq_documents.json` (registered the 9 documents, 400 extracted questions)
- `config/pyq_source_registry.json` (clarified it tracks source hosts, not the
  locally-supplied coaching copies)
- `pyq/questions/README.md`, `pyq/weightage/README.md` (documented the populated
  but `PARTIAL` state and the exposed fields)
- `research/manifests/pyq/PYQ_ACQUISITION_MANIFEST.json` (status `partial`,
  expected 9, accounting identity `9 = 9+0+0+0+0`)
- `tests/bootstrap/test_bootstrap.py` (root-cause fix to `stored_and_raw()`)
- `PROJECT_STATE.md`, `TASK_LEDGER.md` (this session's status)

## Tests executed

- `python scripts/validate_bootstrap.py`
- `python -m unittest discover -s tests -v`

## Test results

- Validator: **21 passed, 0 failed, 21 checks total — PASS**.
- Full suite: **Ran 278 tests … OK (skipped=3)** — 0 failures. The 3 skips are
  correct-by-design (e.g. the emptiness rule that does not apply once a registry is
  complete).
- The one earlier failure —
  `test_ledgers_reconcile_with_what_is_actually_on_disk` ("SOURCE_LEDGER.md
  declares 11 harvested, disk holds 433") — was fixed at its root cause: the test's
  `stored_and_raw()` was counting derived `pyq/` records (400 questions + 9 papers +
  13 weightage) as harvested *sources*. It now counts acquired source bytes only,
  matching `scripts/validate_bootstrap.py::stored_source_files()`. Source bytes
  under `source_material/` = 11; the 422 records under `pyq/` are outputs of
  processing those sources, not harvested sources.

## Evidence

- Real command output above (validator 21/21; suite 278 OK).
- `pyq/questions/README.md` states the `PARTIAL` state and the exposed record shape.
- `pyq/weightage/README.md` states the 13-entry `PARTIAL` table and every exposed
  field.
- `SOURCE_LEDGER.md` Current state (entries 47, harvested items 11) and the
  SRC-0039..SRC-0047 block.
- `research/manifests/pyq/PYQ_ACQUISITION_MANIFEST.json` (expected 9, processed 9).

## Recommended next task

OCR or otherwise obtain an extractable copy of the seven scanned registered papers
(`SRC-0041`..`SRC-0047`) so `pyq/questions/` can grow from 400 to a larger set and
the observed-frequency table can extend beyond the two 2016 papers. That is the
single highest-value next step; before it, the PYQ layer is honestly `PARTIAL`.
