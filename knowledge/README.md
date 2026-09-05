# knowledge/ — Verified, structured knowledge (the tutor's brain)

Only material that has passed `VERIFICATION_POLICY.md` belongs here. Everything the
AI tutor teaches must trace back to a record in this folder.

## Subfolders

| Folder              | Contents                                                                       |
| ------------------- | ------------------------------------------------------------------------------ |
| `schemas/`          | JSON Schema definitions that every record in the sibling folders must validate against |
| `syllabus/`         | Official syllabus, structured. `T1_OFFICIAL` only                              |
| `subjects/`         | Subject-level records                                                           |
| `topics/`           | Topic and subtopic records                                                      |
| `question_families/`| Question-family records — the core teaching unit                                |
| `methods/`          | Verified canonical methods: standard, fast, mental, alternative                 |
| `recognition/`      | Recognition cues and decision trees for identifying question type              |
| `traps/`            | Common traps and the mistakes they cause                                        |
| `confusions/`       | Pairs/groups of topics students confuse, and how to disambiguate them           |

## Required fields on a knowledge record

`subject`, `topic`, `subtopic`, `question_family`, `recognition_cues`,
`standard_method`, `fast_method`, `mental_method`, `alternative_method`,
`validity_conditions`, `when_not_to_use`, `common_mistakes`, `confusing_topics`,
`example_structures`, `difficulty`, `expected_solving_time`, `source_ids`,
`provenance_tier`, `verification_status`, `confidence`.

A field that is genuinely unknown is written as `null` with a matching entry in
`open_questions`. It is **never** filled with a plausible guess.

## Rules

- `provenance_tier` is one of `T1_OFFICIAL`, `T2_HISTORICAL_PYQ`, `T3_EXPERT`,
  `T4_AI`. Never relabel a lower tier as a higher one.
- `verification_status` is one of `VERIFIED`, `UNVERIFIED`, `DISPUTED`, `REJECTED`.
  A `T4_AI` record may not be `VERIFIED` on the strength of the model's confidence
  alone — see `VERIFICATION_POLICY.md`.
- Every record carries at least one `source_ids` entry pointing at `SOURCE_LEDGER.md`.
- Every record carries optional Telugu companion fields (`*_te`). English is
  authoritative for now; the Telugu fields exist so translation is later a
  data-entry task and not a schema migration.
