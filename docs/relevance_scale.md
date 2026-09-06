# Exam-relevance scoring scale — v1

| Field     | Value                                                |
| --------- | ---------------------------------------------------- |
| Authority | `docs/relevance_scale.md` (this file) + `backend/app/knowledge/scoring.py` |
| Spec      | `SPEC-KNW-001` §7                                    |
| Version   | v1, 2026-09-06                                       |

Every score the pipeline writes is computed by these rules and nothing else.
No score is produced by a model, by intuition, or by an unlisted assumption.
Changing a rule means bumping this version and re-scoring candidates
explicitly.

## 1. `si_relevance` — 0 or 1

**1** iff the candidate's subject maps to at least one verified official
syllabus node (`OFF-SYL-*` in `knowledge/official/syllabus.json`) for the SI
exam's papers. **0** otherwise.

Mapping source: `config/subject_syllabus_map.json` — each subject lists the
`OFF-SYL` node ids it derives from, so the mapping is data with provenance,
not code. A subject absent from the map scores 0, not a guess.

Basis: the syllabus read from DOC-OFF-002 (verified, pages 42–44). Papers
considered for SI: PWT sections A/B; FWE Papers I–IV.

## 2. `constable_relevance` — 0 or 1 (PROVISIONAL)

Currently the same rule as SI, using the **SI (Civil) 2026** syllabus, because
the Constable-specific notification (`DOC-OFF-004`, PC Civil et al) is
registered but **not retrieved** (`B-09`). Every candidate carrying
`constable_relevance: 1` also carries `constable_relevance_basis:
"PROVISIONAL"` explaining this. When DOC-OFF-004 is retrieved, the map gains
constable-specific rows and this rule is recomputed — the field is never
silently assumed.

## 3. `telangana_relevance` — 0 or 1

**1** iff the candidate's subject is one of: Telangana History, Telangana
Geography, Telangana GK. **0** otherwise. Subject-derived only in v1 — a
Telangana fact filed under a non-Telangana subject scores 0 rather than the
pipeline second-guessing the classifier.

## 4. `revision_priority` — integer 0–5

Additive rules, capped at 5:

| Rule | Condition                                            | Points |
| ---- | ---------------------------------------------------- | ------ |
| R1   | subject on the verified syllabus (either exam)      | +2     |
| R2   | subject is Telangana-specific (rule 3)               | +1     |
| R3   | knowledge_type ∈ {FACT, DATE, LAW, ARTICLE, AMENDMENT} | +1   |
| R4   | knowledge_type = CURRENT_AFFAIRS and the item's `published_at` is within 12 months of scoring time | +1 |

R4 with no parseable `published_at` contributes 0 — an undatable item is not
penalized, it simply gains nothing. Cap at 5 means the maximum (R1+R2+R3+R4 =
5) is reachable only by a recent Telangana legal/current-affairs fact on the
syllabus, which is exactly the item a candidate should see first.

## 5. `pyq_similarity` — null until PYQs exist

`null` always, until a counted PYQ database exists (`B-02`: no papers
acquired). The field exists per the required schema; a similarity percentage
without a denominator would violate the project's no-uncounted-percentages
rule (TEST_PLAN.md L3). Basis string recorded on every candidate.

## 6. `confidence` — model self-report, copied

The extraction model's own per-item number, copied verbatim, labelled
`model_self_reported`. It is **extraction** confidence (did I read the post
right?), never a claim that the fact is true. Verification never consults it.

## 7. What this scale deliberately does not do

- No score is derived from engagement counts (likes/comments) — popularity is
  not relevance.
- No score is derived from which account posted it — authority is the
  verification stage's question, using tiers, not a number.
- No interpolation: an uncomputable score is null with a basis string, never
  a smoothed value.
