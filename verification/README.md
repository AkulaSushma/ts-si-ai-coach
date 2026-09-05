# verification/ — Proof that knowledge was checked

Nothing becomes trusted knowledge because a model sounded confident. This folder
holds the audit trail.

## Subfolders

| Folder       | Contents                                                                     |
| ------------ | ---------------------------------------------------------------------------- |
| `runs/`      | One log per verification run: what was checked, by which method, with what result |
| `evidence/`  | Supporting evidence — quoted source text, page references, screenshots, computed proofs |
| `disputes/`  | Model disagreements and their arbitration outcomes                            |

## Verification methods recognised by this project

| Method                  | Applies to                              | Strength |
| ----------------------- | --------------------------------------- | -------- |
| `DETERMINISTIC`         | Mathematics, formulae, shortcut validity | Strongest — code proves it |
| `SOURCE_DOCUMENT`       | Official examination facts               | Strongest for `T1_OFFICIAL` |
| `CROSS_SOURCE`          | Facts appearing in independent sources   | Moderate |
| `INDEPENDENT_MODEL`     | Reasoning, classification, explanations  | Moderate — a second model, not the author |
| `DB_CONSISTENCY`        | Structural integrity of records          | Narrow but cheap |
| `SELF_REVIEW`           | Nothing                                  | **Not accepted as verification** |

## Rules

- A verification run that finds no problems must still record what it actually
  executed. "Reviewed and looks correct" is not a verification record.
- Disagreements are recorded, not smoothed over. Write both positions into
  `disputes/`, then record the arbitration decision and its basis.
- A `DISPUTED` record stays out of the tutor's answer path until resolved.
- Prefer `DETERMINISTIC` for every mathematical claim. If a claim can be checked by
  running code, checking it any other way is a policy violation.
