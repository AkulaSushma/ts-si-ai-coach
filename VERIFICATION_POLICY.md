# VERIFICATION_POLICY.md

The purpose of this policy is to make it structurally difficult for a confident wrong
answer to reach the student.

## 1. Core principle

AI output is a **hypothesis**, not knowledge. It becomes knowledge only by passing a
check that is independent of whatever produced it.

Model capability is explicitly not evidence. "This model is strong" is never accepted
as a reason to skip verification. Strong models fail in the most dangerous way
available: fluently, confidently, and in correct formatting.

## 2. Provenance tiers

| Tier                | Meaning                                   | May the tutor teach it?                 |
| ------------------- | ----------------------------------------- | --------------------------------------- |
| `T1_OFFICIAL`       | TGPRB / official government document       | Yes, once source-linked                  |
| `T2_HISTORICAL_PYQ` | Real past papers and official keys         | Yes, labelled as observed history        |
| `T3_EXPERT`         | Educators, coaching, books, videos         | Only after verification                  |
| `T4_AI`             | Model-generated                            | Only after verification                  |

Relabelling a tier upward is a policy violation, not a style choice.

## 3. Verification status

| Status       | Meaning                                                             |
| ------------ | ------------------------------------------------------------------- |
| `UNVERIFIED` | Default for everything on creation                                   |
| `VERIFIED`   | Passed a sufficient check; the run is logged in `verification/runs/` |
| `DISPUTED`   | Sources or models conflict; unresolved                               |
| `REJECTED`   | Checked and found wrong. Kept, so the error is not reintroduced      |

`DISPUTED` and `REJECTED` records never enter the tutor's answer path. `REJECTED`
records are deliberately retained: a recorded wrong answer stops a future session from
rediscovering and trusting it.

## 4. Accepted verification methods

| Method              | What it means                                                        |
| ------------------- | -------------------------------------------------------------------- |
| `DETERMINISTIC`     | Code computes the answer independently, over many inputs              |
| `SOURCE_DOCUMENT`   | A quotable passage in a `T1`/`T2` document, with a locator            |
| `CROSS_SOURCE`      | Two genuinely independent sources agree                               |
| `INDEPENDENT_MODEL` | A different provider reviews without seeing the author's reasoning    |
| `DB_CONSISTENCY`    | Automated structural and referential checks                           |

`SELF_REVIEW` — the author re-reading its own work — is **not** a verification method
and must never be recorded as one.

## 5. Required method by claim type

| Claim type                                   | Minimum required                                              |
| -------------------------------------------- | ------------------------------------------------------------- |
| Syllabus, marks, eligibility, dates, physical standards | `SOURCE_DOCUMENT` on a `T1_OFFICIAL` document       |
| A question appeared in year Y                | `SOURCE_DOCUMENT` on the paper itself                          |
| Correct answer to a PYQ                      | Official key, else `DETERMINISTIC`, else stays `UNVERIFIED`    |
| Any mathematical method or shortcut          | `DETERMINISTIC` — mandatory, no substitute accepted            |
| Shortcut validity boundary                   | `DETERMINISTIC` including inputs where it must fail            |
| Topic weightage figures                      | `DETERMINISTIC` recount from `pyq/questions/` + stated denominator |
| Recognition cues, decision trees             | `INDEPENDENT_MODEL` + tested against real PYQs                 |
| Explanations and teaching text               | `INDEPENDENT_MODEL`                                            |
| Record structure and links                   | `DB_CONSISTENCY`                                               |

Where a claim is mathematical and checkable by code, checking it any other way is a
policy violation. Reasoning about arithmetic is strictly worse than computing it.

## 6. Independence rule

The model that produced an output may never verify it. Concretely: if `DEEP_REASONING`
was filled by provider A, then `VERIFICATION` for that item must be filled by a
provider other than A. The same applies to `CODE_GENERATION` and `CODE_REVIEW`.

`config/model_routing.json` is checked by `scripts/validate_bootstrap.py` to enforce
that authoring and verifying roles do not share a provider. This is a mechanical check
so the rule cannot quietly erode.

## 7. Disagreement handling

Only two providers are currently available (`D-0005`), so there is no neutral third
party for arbitration.

1. Record both positions in `verification/disputes/`, with each party's reasoning.
2. Attempt resolution by `DETERMINISTIC` computation or `SOURCE_DOCUMENT` first — a
   fact beats two opinions.
3. If neither resolves it, the item stays `DISPUTED` and is escalated to the user.
4. Never ask one disputant to judge the disagreement it is party to.
5. Never average two conflicting answers into a middle one. In an exam context a
   blended wrong answer is worse than an acknowledged unknown.

## 8. Verification run record

Every run in `verification/runs/` must state: run ID, date, item IDs checked, method
used, who or what performed it, the exact command executed where applicable, the raw
result, and the resulting status change. A run that changes nothing is still recorded.

"Reviewed and looks correct" is not a verification record and will be treated as if
verification never happened.

## 9. Escalation triggers — stop and tell the user

- An official source contradicts something already stored as `VERIFIED`
- Two `T1_OFFICIAL` documents contradict each other
- A widely taught coaching shortcut fails deterministic testing
- A physical standard or eligibility rule cannot be sourced
- Providers disagree and neither computation nor a document resolves it

## 10. What this policy does not do

It does not guarantee correctness. It makes unverified claims visible and traceable
instead of invisible. When something is wrong, the goal is that the audit trail shows
where it came from and which check failed to catch it — so the gap can be closed rather
than repeated.

Treat every `VERIFIED` label as a claim about the check that was run, not a promise
about reality.
