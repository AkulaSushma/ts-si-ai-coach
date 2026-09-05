# specs/ — Specifications

A specification is written **before** the code it describes. Code that has no
specification is unplanned work.

## Subfolders

| Folder        | Contents                                                                    |
| ------------- | --------------------------------------------------------------------------- |
| `data-model/` | Database schema specs, knowledge-record schemas, field definitions          |
| `features/`   | One spec per user-facing feature (AI tutor, mock exams, adaptive revision)   |
| `api/`        | Backend endpoint contracts (request shape, response shape, error behaviour)  |

## Required sections in every spec

Every spec file must contain these headings, in this order:

1. `## Purpose` — what problem this solves, in one paragraph
2. `## Scope` — what is explicitly in and out of scope
3. `## Acceptance Criteria` — a numbered, individually testable list
4. `## Open Questions` — unresolved issues, or the single word `None`
5. `## Status` — exactly one of `DRAFT`, `APPROVED`, `IMPLEMENTED`, `SUPERSEDED`

## Rules

- A spec with an empty or missing `## Acceptance Criteria` section is invalid.
  Acceptance criteria are the only definition of "done" this project recognises.
- Do not delete a superseded spec. Mark it `SUPERSEDED` and link to the successor.
- Any spec that depends on an unverified Telangana SI examination fact must cite
  the relevant `SOURCE_LEDGER.md` entry ID, or mark that dependency `BLOCKED`.
