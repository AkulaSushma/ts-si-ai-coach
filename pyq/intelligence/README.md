# pyq/intelligence/ — Question-intelligence layer

This folder holds the **analytical** reading of the questions in `pyq/questions/`: what
family each belongs to, the concept it tests, how a solver recognises it, the standard
method, any faster method and whether it is verified, the traps, and the look-alikes.

The questions themselves stay in `pyq/questions/` and are **not** modified here. Each
intelligence record is an **analysis of that `T2_HISTORICAL_PYQ` evidence** — it is not
itself new evidence, and it is never `T1_OFFICIAL`.

## Files

| File | Holds |
| ---- | ----- |
| `questions.json` | One record per analysed question (schema `question_intelligence.schema.json`) |
| `families.json` | Question-family reference records, the core teaching unit |
| `concepts.json` | Concept records, the ideas a family tests |
| `methods.json` | Method records, standard and fast, with their verification state |
| `verifications.json` | Evidence that a fast method was checked |
| `visualizations.json` | `VISUAL_EXPLANATION_SPEC` — structured descriptions, not final images |

## Rules

- **Nothing is guessed.** A question that cannot be confidently classified is recorded
  as `unresolved: true`, and its `topic`, `question_family_id`, `required_concept_id`,
  and `standard_method_id` are all `null`. An unresolved record is a truthful negative,
  not a placeholder to be filled later by a model's guess.
- **`analysis_origin` is always recorded** — `OBSERVED_STANDARD`, `MODEL_DERIVED`, or
  `EXPERT_SOURCED`. A `MODEL_DERIVED` classification is this model's reading of T2
  evidence and is not independently verified. It is never presented as sourced.
- **A fast method has a `state`.** The six states are exclusive. A method is
  `VERIFIED_FAST_METHOD` only after it has been checked by deterministic computation or
  a different provider — never by the model's own confidence. Until then it is
  `MODEL_DERIVED` or `UNVERIFIED_FAST_METHOD`.
- **Identification is structural first.** A recognition clue is `STRUCTURAL` (the form
  of the set, the relationship, the arrangement) or `KEYWORD` (a surface word).
  Structural clues are preferred; a list of keywords only is not identification.
- **No official weightage.** Frequency here is observed behaviour over the corpus and
  is reported as a numerator/denominator with `papers_included`, `question_ids`, and
  `coverage_status`. `basis` is `OBSERVED`, never `OFFICIAL`.
- **`EXPERT_SOURCED` is not Instagram/YouTube.** A record sourced from expert material
  must name a source that is not those services; this phase does not use them.
- **Consolidate.** Do not create a separate file per question. Reference records are
  shared and cross-linked by ID.
- **Never relabel a provenance tier upward.** A pattern across questions is evidence of
  behaviour, not policy. That is `T2_HISTORICAL_PYQ` analysis, never `T1_OFFICIAL`.

## ID prefixes

| Record | Prefix | Example |
| ------ | ------ | ------- |
| question-intelligence | `INT-PYQ-` | `INT-PYQ-010003` |
| question-family | `FAM-PYQ-` | `FAM-PYQ-0001` |
| concept | `CON-PYQ-` | `CON-PYQ-0001` |
| method | `MET-PYQ-` | `MET-PYQ-0001` |
| verification | `VER-PYQ-` | `VER-PYQ-0001` |
| visual-explanation | `VIS-PYQ-` | `VIS-PYQ-0001` |
| trap | `TRAP-PYQ-` | `TRAP-PYQ-0001` |

## Coverage

This session analyses the **Arithmetic & Test of Reasoning** component (101 questions)
fully. General Studies (299 questions) is scaffolded and marked unresolved; it is for a
later session. The corpus itself is `PARTIAL` relative to the registered paper set
(2 of 9 papers extracted), and nothing here implies otherwise.
