# KNOWLEDGE_LEDGER.md — Index of what the system actually knows

This is the honest inventory of verified knowledge. Its job is to make gaps visible
rather than let them hide behind a large-looking folder tree.

## Current state

**Verified knowledge records: 0.**

Nothing is known yet. Bootstrap created the structure to hold knowledge; it acquired
none, because acquiring exam facts was explicitly out of scope and fabricating them is
prohibited.

| Area                             | Records | Status                                      |
| -------------------------------- | ------: | ------------------------------------------- |
| Official syllabus                |       0 | `BLOCKED` — needs official TGPRB document    |
| Exam pattern, marks, duration    |       0 | `BLOCKED` — needs official TGPRB document    |
| Eligibility rules                |       0 | `BLOCKED` — needs official TGPRB document    |
| Physical event standards         |       0 | `BLOCKED` — needs official TGPRB document    |
| PYQ papers                       |       0 | `BLOCKED` — no papers acquired               |
| Question families                |       0 | `BLOCKED` — depends on PYQs                  |
| Recognition cues / decision trees|       0 | `BLOCKED` — depends on question families     |
| Standard methods                 |       0 | `BLOCKED` — depends on question families     |
| Fast / mental methods            |       0 | `BLOCKED` — depends on standard methods      |
| Traps                            |       0 | `BLOCKED` — depends on question families     |
| Confusion pairs                  |       0 | `BLOCKED` — depends on topics                |
| Topic weightage                  |       0 | `BLOCKED` — depends on a counted PYQ set     |

Every row is `BLOCKED` on source acquisition, not on engineering. That is the true
critical path: no amount of code produces exam knowledge.

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

_None yet._

| id | subject | topic | question_family | tier | verification_status | source_ids |
| -- | ------- | ----- | --------------- | ---- | ------------------- | ---------- |
