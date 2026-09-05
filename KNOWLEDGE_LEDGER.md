# KNOWLEDGE_LEDGER.md — Index of what the system actually knows

This is the honest inventory of verified knowledge. Its job is to make gaps visible
rather than let them hide behind a large-looking folder tree.

## Current state

**Verified knowledge records: 0.**

Nothing is known yet. Sessions 001–003 created and tested the structures that will
hold knowledge; they acquired none, because every official document request was
refused by this environment's network egress allowlist (`B-09`) and inventing exam
facts is prohibited.

Session 003 added **25 official fact slots** (`OFF-F01`–`OFF-F25` in
`knowledge/official/required_facts.json`). Every one carries `value: null`,
`status: BLOCKED`, and a written reason. A slot is a question the project has
committed to answering from an official document — it is not an answer, and it is
never counted as knowledge. The distinction this ledger enforces: the **container**
for official knowledge is `COMPLETE` and tested; the **content** is `BLOCKED` at
zero.

| Area                             | Records | Status                                      |
| -------------------------------- | ------: | ------------------------------------------- |
| Official facts (25 slots)        |       0 | `BLOCKED` — `B-09`, 0 of 25 `VERIFIED`       |
| Official syllabus                |       0 | `BLOCKED` — needs official TGPRB document    |
| Exam pattern, marks, duration    |       0 | `BLOCKED` — needs official TGPRB document    |
| Eligibility rules                |       0 | `BLOCKED` — needs official TGPRB document    |
| Physical event standards         |       0 | `BLOCKED` — needs official TGPRB document    |
| Preparation taxonomy             |       0 | `BLOCKED` — forbids `T1_OFFICIAL` by design  |
| PYQ papers                       |       0 | `BLOCKED` — no papers acquired               |
| Question families                |       0 | `BLOCKED` — depends on PYQs                  |
| Recognition cues / decision trees|       0 | `BLOCKED` — depends on question families     |
| Standard methods                 |       0 | `BLOCKED` — depends on question families     |
| Fast / mental methods            |       0 | `BLOCKED` — depends on standard methods      |
| Traps                            |       0 | `BLOCKED` — depends on question families     |
| Confusion pairs                  |       0 | `BLOCKED` — depends on topics                |
| Topic weightage (3 categories)   |       0 | `BLOCKED` — official / observed / estimated kept in separate files |

Every row is `BLOCKED` on source acquisition, not on engineering. That is the true
critical path: no amount of code produces exam knowledge.

Mechanically enforced, so this table cannot drift: `scripts/validate_bootstrap.py`
check 18 recomputes the verified total from the registries and fails if the figure
above disagrees, and `tests/bootstrap/test_bootstrap.py::TestHonestyOfState`
reconciles both ledgers against the filesystem with ten fabricated-data cases
proving the reconciliation can fail.

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
