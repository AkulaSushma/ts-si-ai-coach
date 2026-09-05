# pyq/ — Previous-year questions, normalized

Raw papers live in `source_material/pyq_raw/`. This folder holds the **normalized,
machine-readable** form of those papers plus the analysis derived from them.

## Subfolders

| Folder       | Contents                                                                   |
| ------------ | -------------------------------------------------------------------------- |
| `papers/`    | One record per paper: exam, year, phase, paper number, language, marks, source ID |
| `questions/` | One record per question, linked to its paper and to a `question_family`      |
| `weightage/` | Historical topic-weightage analysis outputs, with the inputs used to compute them |

## Provenance

Everything here is `T2_HISTORICAL_PYQ`. A PYQ tells you what **was** asked. It is
strong evidence about exam behaviour and **not** a statement of official policy.
Never present a pattern observed in PYQs as an official rule — that is a `T1_OFFICIAL`
claim and needs a TGPRB document.

## Rules

- A question record must record `answer_source`: whether the correct answer came
  from an official key, a coaching key, or is `UNVERIFIED`. Unofficial keys contain
  errors; the system must be able to distinguish them.
- Weightage analysis must state its denominator explicitly: which papers, which
  years, how many questions total, and how many questions were unclassifiable.
  A weightage table without that footer is invalid.
- Never extrapolate a weightage percentage from an incomplete paper set without
  labelling it `PARTIAL` and stating the coverage.
