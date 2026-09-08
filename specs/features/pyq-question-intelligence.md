# SPEC-PYQ-002 — PYQ question-intelligence layer

**Status:** `APPROVED` · **Date:** 2026-09-07 · **Session:** 009
**Requirements source:** user directive, session 009 ("Build PYQ question-intelligence
layer"). That directive is the requirements document for this spec, in the same way
session 007's instruction was for `SPEC-PYQ-001` and session 003's for `SPEC-OFF-001`.

## 1. Purpose

Turn the stored `T2_HISTORICAL_PYQ` question records in `pyq/questions/` into an
**analytical intelligence layer** — the thing that makes each question teachable. This
is not new evidence. Each record already proved a fact about what was asked. The
intelligence layer classifies it, names the family it belongs to, names the concept it
tests, states how a solver recognises it, states the standard method and (where
justified) a faster method, names the traps and confusions, and explains how to tell it
apart from look-alikes.

The layer exists so the system can behave like an experienced coaching institute: it
sees a question, recognises the family, picks a method, warns of the trap. It does not
guess at official policy from a pattern, and it never presents a model-derived shortcut
as a verified fact.

The dominant constraint, from the project's quality principle, is that this layer must
**never fabricate or silently upgrade**. A classification is a claim over T2 evidence,
so it carries an `analysis_origin`. A fast method is a claim that may be wrong, so it
carries a `state` that says exactly how it was obtained and whether it was checked.
Both are recorded, and anti-vacuity tests make a lying record impossible to accept.

## 2. Scope

In scope:

- An analytical record per extracted question was already planned in the question schema;
  this spec makes that analysis a **separate, richer** record rather than enlarging the
  already-normalized question record. The question record stays authoritative and is not
  mutated; the intelligence record refines its classification.
- Six record types: **question-intelligence**, **question-family**, **concept**,
  **method**, **verification**, **visual-explanation**. Each has an explicit ID prefix
  and a provenance block.
- Full analysis of the **Arithmetic & Test of Reasoning** component first (the 101
  questions). General Studies is scaffolded and marked unresolved; it is out of scope
  for this session.
- Consolidated JSON files, not hundreds of files (`D`, data-model rule).
- Anti-hallucination validators and tests.
- Mathematical verification of every candidate fast method, before it may be recorded
  as `VERIFIED_FAST_METHOD`.
- A structured `VISUAL_EXPLANATION_SPEC` per family (description, not final images).

Out of scope:

- Redoing the completed official-source work, the PYQ acquisition infrastructure, or the
  400 already-extracted questions.
- Rendering visual explanations into actual images.
- Using Instagram or YouTube. The schema has a slot for an expert-source reference that
  is explicitly not those, so a future phase can attach expert evidence without this
  session touching them.
- Any UI, any frontend.
- Computing a weightage number beyond the corpus (see `pyq/weightage/`; nothing here
  becomes "official weightage").
- Labelling the partial corpus as complete (`D-0016`).

## 3. Authority and provenance rules

| Rule | Statement |
| ---- | --------- |
| `R1` | The underlying question is `T2_HISTORICAL_PYQ`. Its intelligence record is an **analysis of that T2 evidence**, never new evidence, and never `T1_OFFICIAL`. |
| `R2` | Every record carries an `analysis_origin`: `OBSERVED_STANDARD`, `MODEL_DERIVED`, or `EXPERT_SOURCED`. `MODEL_DERIVED` is this model's analysis of T2 evidence and is not independently verified. A record may never present `MODEL_DERIVED` as `EXPERT_SOURCED` or as verified. |
| `R3` | A fast method's `state` is exactly one of the six: `OBSERVED_STANDARD`, `MODEL_DERIVED`, `EXPERT_SOURCED`, `VERIFIED_FAST_METHOD`, `UNVERIFIED_FAST_METHOD`, `NO_FAST_METHOD_FOUND`. Promotion to `VERIFIED_FAST_METHOD` requires a verification record whose `result` is `PASS`, produced by deterministic computation or a different provider — never by the model's own confidence. |
| `R4` | A pattern observed across PYQs is evidence of behaviour, not policy. It never becomes a topic-weightage claim about the official syllabus. Observed frequency is reported as a numerator/denominator with papers-included and coverage status, kept `PARTIAL`. |
| `R5` | An `EXPERT_SOURCED` record requires a source reference that is not Instagram or YouTube. |
| `R6` | A question that cannot be confidently classified is left **unresolved** — `topic`, `question_family_id`, `required_concept_id`, and `standard_method_id` are all `null`. It is never guessed. |

## 4. Data model and locations

The schemas (metadata) live in `knowledge/schemas/`; the records (analysis) live in a new
`pyq/intelligence/` tree. The trusted `knowledge/` layer is reserved for
`VERIFY`-grade material (per `knowledge/README.md`); the intelligence layer is an
analysis, so it sits beside the questions it classifies.

| Path | Holds | Tier |
| ---- | ----- | ---- |
| `knowledge/schemas/question_intelligence.schema.json` | Per-question analysis record | metadata |
| `knowledge/schemas/question_family.schema.json` | Teaching-unit record | metadata |
| `knowledge/schemas/concept.schema.json` | Concept record | metadata |
| `knowledge/schemas/method.schema.json` | Method record | metadata |
| `knowledge/schemas/verification.schema.json` | Fast-method verification evidence | metadata |
| `knowledge/schemas/visual_explanation.schema.json` | Visual-explanation spec | metadata |
| `pyq/intelligence/README.md` | Rules for the tree | metadata |
| `pyq/intelligence/questions.json` | One intelligence record per analysed question | `T2_HISTORICAL_PYQ` (analysis) |
| `pyq/intelligence/families.json` | Family reference records | `T2_HISTORICAL_PYQ` (analysis) |
| `pyq/intelligence/concepts.json` | Concept reference records | `T2_HISTORICAL_PYQ` (analysis) |
| `pyq/intelligence/methods.json` | Method reference records | `T2_HISTORICAL_PYQ` (analysis) |
| `pyq/intelligence/verifications.json` | Verification evidence | `T2_HISTORICAL_PYQ` (analysis) |
| `pyq/intelligence/visualizations.json` | Visual-explanation specs | `T2_HISTORICAL_PYQ` (analysis) |

ID prefixes: `INT-PYQ-` (per-question), `FAM-PYQ-` (family), `CON-PYQ-` (concept),
`MET-PYQ-` (method), `VER-PYQ-` (verification), `VIS-PYQ-` (visual), `TRAP-PYQ-` (trap).

Consolidation rule (`D`): do not create a separate file per question. Reference records
are shared; a question record points to a family, a concept, a method; a family points
to members, concepts, methods. This keeps the set small and the cross-references
enforceable in one place.

## 5. Per-question analysis fields

For every analysed question, the record carries (full shape in
`question_intelligence.schema.json`):

`intelligence_id`, `question_id`, `paper_id`, `source_question_number`,
`source_page_number`, `subject`, `topic`, `subtopic`, `question_type`,
`question_family_id`, `identification_clues` (structural first), `required_concept_id`,
`standard_method_id`, `candidate_fast_method_id`, `fast_method_state`,
`fast_method_verified_id`, `common_trap_ids`, `confusing_family_ids`,
`how_to_distinguish`, `expected_solving_complexity`, `classification_confidence`,
`unresolved`, `analysis_origin`, `evidence_tier`, `provenance`, `verification`.

## 6. Question identification is first-class

Identification is a **structural** reading of the question, not a keyword match. A
keyword ("percentage", "ratio") is a weak surface signal and is recorded as `KEYWORD`;
a structural clue (the form of the set, the relationship, the arrangement) is
`STRUCTURAL` and is preferred. Recognition cues are recorded at the family level and are
the thing a solver learns. A junk keyword list is not identification, and the validators
reject a record whose only clues are keywords.

## 7. Frequency and weightage

The intelligence layer records **what was observed** and how much of the corpus it
covered. It never produces an official weightage. An entry reports:

- `numerator` — questions in the subject/topic/family
- `denominator` — total questions over the included paper set
- `papers_included` — the paper ids counted
- `question_ids` — the actual ids counted
- `coverage_status` — `PARTIAL` unless the set is the full enumerated intake
- `basis` — `OBSERVED`, never `OFFICIAL`

No entry without a denominator, and no percentage presented as a claim about the whole
syllabus.

## 8. Method verification procedure

A candidate fast method may become `VERIFIED_FAST_METHOD` only after this sequence, run
and recorded:

1. Solve a question conventionally → record the standard method and result.
2. Derive the fast method → record it as `MODEL_DERIVED`.
3. **Check equivalence** — run both over many inputs; `fast_matches_standard` must be
   true and `mismatches` zero.
4. **Test variants** — the input families the method claims to cover.
5. **Test edge cases** — the places a shortcut is expected to break (zero, negatives,
   boundary, degenerate).

Only after 3–5 pass does it carry `VERIFIED_FAST_METHOD`. If it fails, it stays
`UNVERIFIED_FAST_METHOD` with the failure recorded, or is dropped. The verification is
deterministic computation or a different provider; never the model's own confidence.

## 9. Acceptance criteria

| # | Criterion | Verified by |
| - | --------- | ----------- |
| `AC-1` | The six schema files exist, are valid JSON, and reference the required fields | Validator + Tests 1–2 |
| `AC-2` | Every intelligence record resolves to a real question record and matches its `paper_id`; an unsourced record is rejected | Test 3 |
| `AC-3` | A record with `fast_method_state == VERIFIED_FAST_METHOD` carries a `verification_id` that resolves to a `PASS` verification; otherwise rejected | Test 4 |
| `AC-4` | A record with `fast_method_state in (UNVERIFIED, VERIFIED)` has a `candidate_fast_method_id`; `NO_FAST_METHOD_FOUND` has none | Test 5 |
| `AC-5` | An `unresolved` record has `question_family_id`, `topic`, `required_concept_id`, and `standard_method_id` all null | Test 6 |
| `AC-6` | An `analysis_origin == EXPERT_SOURCED` record has a source ref that is not Instagram/YouTube | Test 7 |
| `AC-7` | A method never relabels: a `MODEL_DERIVED`/`UNVERIFIED` method is rejected if presented as `EXPERT_SOURCED` or `VERIFIED` without matching evidence | Test 8 |
| `AC-8` | A verification record claiming `PASS` has `mismatches == 0`, non-empty variants and edge cases; an `INDEPENDENT_MODEL` record names a verifier different from the analyser | Test 9 |
| `AC-9` | A family record is grounded: `OBSERVED_FROM_CORPUS` requires non-empty `question_ids` that resolve; a candidate family has empty members | Test 10 |
| `AC-10` | Frequency entries carry a denominator, papers-included, and coverage status; no `OFFICIAL` basis | Test 11 |
| `AC-11` | The checkers themselves reject fabricated/poisoned intelligence, family, method, verification, and frequency records | Test 12+ (anti-vacuity) |

## 10. Anti-vacuity requirement

Every checker above must be able to fail. The anti-vacuity tests feed deliberately
poisoned records — an intelligence record with no question, a fast method marked
verified with no verification, a verification that claims `PASS` with a mismatch, a
family observed with no members, a frequency entry with a numerator but no denominator,
a `MODEL_DERIVED` method presented as verified — and assert each is rejected. A checker
that only ever sees a clean, correct corpus proves nothing.

## 11. Open questions

- `D-0010` (SQLite vs files) remains open; these consolidated JSON files are designed so
  a later import is mechanical.
- The General Studies component (299 questions) is scaffolded but not analysed. How deep
  the analysis of GS goes is a decision for a later session; this session records it as
  unresolved rather than attempt it.

## 12. Status

`APPROVED`. The session-009 directive is the requirements source. Work proceeds against
these criteria; the phase is `COMPLETE` only when each `AC` is satisfied and observed.
