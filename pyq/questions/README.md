# pyq/questions/ — Normalized question records

One JSON record per question, linked to its paper and eventually to a `question_family`.
Each record is `T2_HISTORICAL_PYQ`: it tells you what was asked, not what the rule is.

As of 2026-09-07 this folder holds **400 records** — the 2016 Preliminary
(`PAPER-PYQ-1601`, Q1–200) and the 2016 General Studies final (`PAPER-PYQ-1602`,
Q1–200), the only two of the nine registered papers with a usable text layer. The other
seven registered papers are scanned/image-only and are not extracted, so this folder is
**PARTIAL relative to the registered corpus** — 400 of a set whose full size is unknown.

Each record carries a `classification` block recording how the subject/topic was
assigned (keyword/pattern match over the stem, i.e. `T2_HISTORICAL_PYQ` evidence, not an
official rule), its confidence (`NEAR` / `AMBIGUOUS`), and whether the topic is
unresolved. Where the topic could not be resolved the record keeps `topic: null` with
`unresolved: true` rather than guessing a topic.

## Record shape

Defined in `knowledge/schemas/pyq_question.schema.json`. Every field the preparation
system may need is present; fields not yet known are `null`. The user-required fields
include: subject, topic, subtopic, question type, concept tested, difficulty, correct
answer, source/page/question number, year, paper, post code, solving method, estimated
normal solving time, verified fast method, fast-method source, identification clues,
confusion pairs.

## Rules

- `answer_source` is present on **every** question, even one with no key. A value of
  `UNVERIFIED` means no key was seen — it is a visible fact, not a silent assumption.
- `correct_answer` non-null requires an `answer_source` that is not `UNVERIFIED`.
- A question must resolve to a registered paper (`paper_id`). A question with no paper
  is unsourced and is rejected by the tests.
- A question with an unreadable number must record that in `extraction_issues`, not
  silently drop the number.
- A question from a paper whose `normalized_questions_status` is `NONE` cannot exist.
- A question's `subject` / `topic` / `subtopic` must be a valid assignment, with a
  recorded `extraction_confidence`.
