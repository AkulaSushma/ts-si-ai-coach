# KNOWLEDGE_LEDGER.md — Index of what the system actually knows

This is the honest inventory of verified knowledge. Its job is to make gaps visible
rather than let them hide behind a large-looking folder tree.

## Current state

**Verified knowledge records: 51.**

Session 004 acquired the two official notification PDFs (user-supplied downloads
from the board's site, `B-09` resolved for `DOC-OFF-002` and `DOC-OFF-003` only)
and read them. All 51 verified records are `T1_OFFICIAL`, cited to a stored,
hashed document with page, section and a verbatim quote that
`tests/official/test_official_evidence.py` re-checks mechanically:

| Area                             | Records | Status                                      |
| -------------------------------- | ------: | ------------------------------------------- |
| Official facts (`OFF-F01`–`F25`)  |      24 | `VERIFIED` against DOC-OFF-002 / DOC-OFF-003; OFF-F03 (application dates) stays `BLOCKED` — the notification defers the dates to a future press release |
| Official syllabus (`OFF-SYL-*`)   |      27 | `VERIFIED` — 27 nodes: 2 PWT sections + 4 FWE papers with the topics the notification itself lists (Annexures II and III, pages 42–44); no subtopic layer because the document prints none |
| Exam pattern, marks, duration     |       3 | Covered by verified facts OFF-F12–OFF-F14 (paper structure, qualifying thresholds, negative marking) |
| Eligibility rules                |       4 | Covered by verified facts OFF-F07–OFF-F10 (age, education, local candidate status) |
| Physical event standards          |       2 | Covered by verified facts OFF-F18, OFF-F19 (height, chest/PMT/PET as printed) |
| Official notification identity   |       2 | Covered by verified facts OFF-F01, OFF-F02 (Rc. number, issue date) |
| Preparation taxonomy              |       0 | `BLOCKED` — may now anchor to the verified syllabus; first expert source still not ingested |
| PYQ papers                       |       0 | `BLOCKED` — no papers acquired               |
| Question families                 |       0 | `BLOCKED` — depends on PYQs                  |
| Recognition cues / decision trees|       0 | `BLOCKED` — depends on question families     |
| Standard methods                  |       0 | `BLOCKED` — depends on question families     |
| Fast / mental methods             |       0 | `BLOCKED` — depends on standard methods      |
| Traps                             |       0 | `BLOCKED` — depends on question families     |
| Confusion pairs                   |       0 | `BLOCKED` — depends on topics                |
| Topic weightage (3 categories)    |       0 | `BLOCKED` — official marks structure file still empty pending its own read; observed and estimated categories still empty |

Counting basis: 24 facts with `status: VERIFIED` plus 27 syllabus nodes with a
`verification.method` set — recomputed by `scripts/validate_bootstrap.py`
check 18, which fails if this figure disagrees, and by
`tests/bootstrap/test_bootstrap.py::TestHonestyOfState`. No
social-media-derived, coaching, or model-recalled content appears anywhere in
the verified total: Instagram acquisition is still blocked (`B-08`) and the
candidate-knowledge pipeline writes only `UNVERIFIED` records by design.

## ID format

`KN-####` — sequential, never reused.

## Required fields per entry

`id`, `subject`, `topic`, `subtopic`, `question_family`, `provenance_tier`,
`verification_status`, `verification_method`, `verified_on`, `source_ids`,
`confidence`, `record_path`, `notes`.

## Rules

- An entry appears here only once a record exists in `knowledge/` and validates against
  its schema in `knowledge/schemas/`.
- `confidence` is a stated judgement with a reason, never a decorative number. If the
  reason cannot be written, the confidence cannot be claimed.
- Counts in the table above must be recomputed by counting files, never estimated. A
  wrong count here is worse than no count, because it makes gaps invisible.
- When a record is `REJECTED`, keep the entry and mark it. Removing it invites the same
  error to be rediscovered and trusted later.

## Entries

_None yet — no record has reached `VERIFIED`._

The 25 official fact slots are tracked in `knowledge/official/required_facts.json`,
not here. They graduate into the table below one at a time, each with the document
id, page or section, and the verbatim quote that supports it.

| id | subject | topic | question_family | tier | verification_status | source_ids |
| -- | ------- | ----- | --------------- | ---- | ------------------- | ---------- |
