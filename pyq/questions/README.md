# pyq/questions/ — Normalized question records

One JSON record per question, linked to its paper and eventually to a `question_family`.
Each record is `T2_HISTORICAL_PYQ`: it tells you what was asked, not what the rule is.

This folder is **empty until a paper is extracted**. An empty folder is the correct,
honest state, not a gap.

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
