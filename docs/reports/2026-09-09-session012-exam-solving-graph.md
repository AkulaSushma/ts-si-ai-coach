# Session 012 — Exam-solving knowledge graph + deterministic rule derivation

Date: 2026-09-09 (Asia/Calcutta)
Base commit: e7840a82b7748e4b9d3947caf00dccfb8682286d
Overall status: **PARTIAL**

## What was requested

Continue the project from the actual repository state, re-establish ground truth, choose the
highest-value bounded milestone, and run an end-to-end pilot on a small number of real assets
that preserves provenance and uncertainty. No UI. No bulk media processing.

## Ground truth re-established (VERIFIED via GitHub API)

- Branch `main` HEAD was **e7840a82b7748e4b9d3947caf00dccfb8682286d**, not `b8facd4…`.
  `b8facd4…` is two commits behind (`7fd3679…` then `e7840a8…`).
- Media collection: 62 assets / 539,873,070 bytes / 37 videos / 25 images (unchanged).
- Videos remain unreachable through the available tooling (>1 MB content limit, no raw-blob
  download tool). 0 videos have been processed to date. **BLOCKED**, not deferred.

## What was built

`scripts/knowledge_graph.py` — append-only, hash-sealed node/edge log where status is
**derived from evidence at read time and never stored**, with pessimistic precedence
`BLOCKED > FAILED > INCOMPLETE > VERIFIED > SUPPORTED > CANDIDATE > UNVERIFIED`. Exam
relationships (`solves`, `applies_to_pyq`, `recognizes`, `contradicts`) are refused without
located evidence, a written justification and a known PYQ id.

`scripts/series_derive.py` — deterministic search of a declared finite rule space that
returns FAIL rather than a nearest match, and reports whether a fitting rule is unique.

`scripts/run_series_pilot.py` — the bounded pilot.

`tests/test_session012_graph.py` — 20 new tests; staged suite total 67, all passing in 2.257s.

## Pilot result on a real asset (honest outcome: FAILED)

Asset `Screenshot_2026-09-01-19-51-42-53_….jpg`, blob `b1705377…`, sha256 `e743b6d7…`,
423,178 bytes, 1080x2414, region [260,110,780,1180] (approximate visual bound, not OCR).

Visible handwritten table: 1-1, 2-5, 3-13, 4-27, 5-48, 6-78, 7-118, 8-170. No rule, no
worked steps, no question stem, no publisher, no date visible.

90,000 declared rules tested; **none** reproduces all eight pairs. First differences
4, 8, 14, 21, 30, 40, 52; second differences 4, 6, 7, 9, 10, 12 — never constant.

Resulting statuses:

| Node | Status |
|---|---|
| asset, evidence span | SUPPORTED |
| OBS-MEDIA-0002 (verbatim table) | SUPPORTED |
| CON-MEDIA-0002 (concept framing) | CANDIDATE |
| MET-MEDIA-0002 (rule hypothesis) | FAILED |
| OBS-MEDIA-0002-AUDIO (spoken rule) | BLOCKED |

PYQ links created: **0**. No rule was invented to make the data fit, and no handwritten
digit was "corrected".

## What is NOT done

- Speed / recognition / retention assessment procedures: **INCOMPLETE** (dimensions modelled,
  no harness).
- OCR and ASR: **BLOCKED** (no engine available in the execution environment).
- Video intelligence: **BLOCKED**.
- Weightage and sequencing model: **not started**.
- Legacy VERIFIED labels in `pyq/intelligence/` and `verification/`: still **UNVERIFIED** in
  substance; untouched and not re-promoted.
- Root ledgers (`PROJECT_STATE.md`, `TASK_LEDGER.md`, `SOURCE_LEDGER.md`,
  `KNOWLEDGE_LEDGER.md`) remain stale and were deliberately not rewritten in this session.

## Recommended next task

Run `scripts/video_intake.py` on `Dynasties & Founders (Tricks).mp4` in the local Windows
checkout (where the 1 MB API limit does not apply), then add a Telugu-capable ASR adapter
that fails closed. That is the single change that would unblock the largest amount of real
teaching intelligence.

SPEC-INT-012 is implemented and tested; it is **not** complete.
