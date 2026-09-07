# SPEC-PYQ-001 — Previous-year question (PYQ) acquisition and analysis preparation

**Status:** `APPROVED` · **Date:** 2026-09-07 · **Session:** 007
**Requirements source:** user instruction, session 007 ("PYQ acquisition and analysis
preparation"). That instruction is the requirements document for this spec, in the same
way session 003's instruction was for `SPEC-OFF-001`.

## 1. Purpose

Establish the structures that hold **`T2_HISTORICAL_PYQ`** material — previous-year
Telangana Police SI / Constable question papers and the questions they contain — and
the machinery that makes it impossible to (a) present a past question as an official
rule, or (b) compute a topic-weightage number that is not counted over a real,
enumerated paper set.

Like `SPEC-OFF-001`, this spec separates the **container** from the **content**:

- **the container** — source registry, document/paper registry, question schema,
  extraction structure, provenance slots, weightage expose fields, tests
- **the content** — the papers and questions themselves, which come only from actual
  acquisition and extraction

The container is built and verified with no network access. The content is not. Building
the container is legitimate work; inventing a past paper, a question, a weightage
percentage, or a "PYQ similarity" from model recall is the single most damaging thing
this project could do, and the tests below make it mechanically impossible rather than
discouraged.

## 2. Non-goals

- **No weightage is computed.** This spec builds the recording structure and the
  expose fields. It does not produce a single observed-frequency number, because no
  verified paper set exists yet. Any number produced before such a set would be
  fabricated precision.
- Not Instagram or YouTube knowledge. That is a separate phase; do not start it here.
- Not the final UI. No frontend work.
- Not a modification or re-do of the completed Phase-1 official-source work
  (`SPEC-OFF-001`, session 006 checkpoint `7ef3a59`).
- Not the data-model / SQLite schema (`D-0010`, still open). These are files on disk,
  designed so a later database import is mechanical.

## 3. Authority and provenance rules

PYQ material is evidence of past behaviour. It is **never** official policy.

| Rule | Statement |
| ---- | --------- |
| `R1` | Everything under `pyq/` is `T2_HISTORICAL_PYQ`. A pattern observed across papers may never be relabelled `T1_OFFICIAL`; that needs a TGPRB document. |
| `R2` | A paper is not silently treated as an official document. Every paper records a `source_type`: `OFFICIAL_PUBLICATION` (served by the board), `COACHING_COPY` (a coaching site's scan or transcription of a paper), or `CANDIDATE_RECALL` (reconstructed from memory). Coaching copies are the realistic route and are legitimate `T2_HISTORICAL_PYQ`, but they are recorded as coaching copies, never as board-issued. |
| `R3` | Every question records `answer_source`: whether the correct answer came from an official key, a coaching key, or is `UNVERIFIED`. Unofficial keys contain errors; the system must be able to distinguish them. |
| `R4` | A question record must resolve to a registered paper, and a paper's retrieved state must be consistent with the bytes on disk (hash match). A question with no paper is unsourced. |
| `R5` | No weightage entry may be computed unless its paper set is enumerated and its denominator is stated — see §7. |

## 4. What previous-year papers are required

Frequency analysis needs a **paper set** that covers both broad components of the 2026
structure, because each component has its own subject and topic distribution. From the
official marks structure (`knowledge/weightage/official_marks_structure.json`,
`MS-PWT-*`, `MS-FWE-*`):

| Component | Where it appears | Question count in the current structure |
| --------- | ---------------- | --------------------------------------- |
| Arithmetic & Test of Reasoning / Mental Ability | Preliminary Written Test and FWE Paper III | 100 (PWT) / 200 (FWE Paper III) |
| General Studies | Preliminary Written Test and FWE Paper IV | 100 (PWT) / 200 (FWE Paper IV) |

A paper is eligible for frequency analysis when all of the following hold:

1. It is a **Telangana Police SI or Constable written examination paper** (the user's
   directive names both).
2. It is **complete or its incompleteness is recorded** — the total question count is
   known, or the count is explicitly labelled `PARTIAL` with a numerator/denominator.
3. It has **provenance** — a source that is recorded with its `source_type`, a URL or
   `local_path`, and (for retrieved bytes) a hash.
4. Every question has a **subject / topic / subtopic assignment**, each with a recorded
   **classification confidence**.

**The specific set of years and papers is `UNVERIFIED`.** This session could not reach
any source (see §5), so no concrete paper identity has been enumerated. The requirement
above is the eligibility rule that a future acquisition session applies, not a claim
that any specific paper exists.

## 5. Acquisition state

The acquisition path is currently `BLOCKED`. This environment's egress allowlist names
one unrelated host, and web search returns no content. The exact refusal, recorded
verbatim, is in `source_material/pyq_raw/RETRIEVAL_LOG.md` and
`config/pyq_source_registry.json`. Per `D-0017` this was not routed around.

No paper, question, or verified source URL exists yet. All registries below hold zero
records, and `expected = processed + inaccessible + irrelevant + duplicate + failed`
holds at `0 = 0 + 0 + 0 + 0 + 0`.

## 6. Artefacts

| Path | Holds | Tier |
| ---- | ----- | ---- |
| `config/pyq_source_registry.json` | Candidate sources for papers: categories, eligibility, retrieval state | metadata |
| `config/pyq_documents.json` | Target / acquired paper registry: each paper's identity, source, hashes, extraction state | metadata |
| `source_material/pyq_raw/RETRIEVAL_LOG.md` | Verbatim retrieval attempts and responses | evidence |
| `source_material/pyq_raw/` | Raw paper files, once obtainable (git-ignored per `D-0008`) | `T2_HISTORICAL_PYQ` |
| `pyq/papers/` | One normalized record per paper | `T2_HISTORICAL_PYQ` |
| `pyq/questions/` | One normalized record per question | `T2_HISTORICAL_PYQ` |
| `pyq/weightage/` | Historical frequency analysis outputs and the inputs used | `T2_HISTORICAL_PYQ` |
| `knowledge/schemas/pyq_paper.schema.json` | Paper record shape | metadata |
| `knowledge/schemas/pyq_question.schema.json` | Question record shape | metadata |
| `knowledge/schemas/pyq_weightage.schema.json` | Weightage output shape (expose fields) | metadata |
| `research/manifests/pyq/` | Acquisition accounting for PYQ sources | evidence |

## 7. Weightage: recording structure, no computation

Weightage (observed frequency) lives in `pyq/weightage/`. Every entry exposes, so a
reader can always see what a number actually counts:

| Expose field | Meaning |
| ------------ | ------- |
| `numerator` | Number of classified questions in this subject / topic / question-type |
| `denominator` | Total classified questions across the included paper set |
| `papers_included` | Which paper ids were counted |
| `years_included` | Which years those papers came from |
| `classification_confidence` | How confidently each question was assigned (e.g. `EXACT`, `NEAR`, `AMBIGUOUS`, `UNKNOWN`) |
| `basis` | `OBSERVED` (counted from PYQs) — never `OFFICIAL`; the official number is a different file (`official_marks_structure.json`) |

Two hard rules:

- **No entry without a denominator.** An entry with a `numerator` but no `denominator`,
  or with `denominator == 0`, is invalid and rejected by the tests.
- **Partial coverage is labelled.** A percentage computed over an incomplete paper set
  is recorded as `PARTIAL` with its coverage stated, never rounded up to a claim about
  the whole set.

**No weightage entry may be created until the paper set is enumerated.** The current
`pyq/weightage/` therefore holds a documented shape, not a number.

## 8. Question record shape

Every field the user's directive requires is present, nullable where not yet known.
Full shape in `knowledge/schemas/pyq_question.schema.json`. Summary of the required
fields:

`question_id`, `paper_id`, `question_number`, `page_number`, `stem`, `stem_te`,
`options`, `correct_answer`, `answer_source`, `subject`, `topic`, `subtopic`,
`question_type`, `concept_tested`, `difficulty`, `paper_year`, `post_code`,
`source_type`, `solving_method`, `estimated_normal_time_s`, `verified_fast_method`,
`fast_method_source`, `identification_clues`, `confusion_pairs`,
`extraction_confidence`, `extraction_issues`, `provenance_tier`, `provenance`,
`verification`.

## 9. Acceptance criteria

| # | Criterion | Verified by |
| - | --------- | ----------- |
| `AC-1` | PYQ source and paper registries exist, are valid JSON, carry the required fields, and record the current blocked state | Tests 1–2 |
| `AC-2` | Every paper record carries a `source_type`, a provenance block, and a consistent retrieved/stored state; a `RETRIEVED` claim matches the bytes on disk | Tests 3, 7 |
| `AC-3` | Every question resolves to a registered paper, records an `answer_source`, and carries a `T2_HISTORICAL_PYQ` tier | Test 4 |
| `AC-4` | Duplicate questions and duplicate (paper, question-number) pairs are rejected; missing question numbers are rejected | Test 5 |
| `AC-5` | Invalid subject / topic / subtopic assignments and missing classification confidence are rejected | Test 6 |
| `AC-6` | No weightage entry exists with a numerator but no denominator, a zero denominator, or an unenumerated paper set | Test 8 |
| `AC-7` | The research accounting identity holds for the PYQ source set, and the PYQ manifests are balanced | Tests 9–10 |
| `AC-8` | The checkers themselves reject a fabricated paper, question, and weightage entry | Test 11 (anti-vacuity) |

`AC-1` to `AC-8` are container criteria and pass while not a single paper exists.
PYQ **content** is `COMPLETE` only when papers have been acquired, hashed, extracted,
classified, and counted. Container criteria passing does not license reporting the
phase `COMPLETE` (`D-0016`).

## 10. Anti-vacuity requirement

Every checker above must be able to fail. The anti-vacuity test constructs poisoned
in-memory records — a question with no paper, a paper claiming retrieved bytes that do
not hash, a question with no `answer_source`, a weightage entry with a numerator but no
denominator, a coaching copy labelled as an official publication, a question with a
missing question number — and asserts each checker rejects them. A suite that only
sees an empty `pyq/` tree proves nothing about a populated one.

## 11. Out of scope for this spec

Retrieval automation. There is no scripted downloader, because the current blocker is
network reachability rather than parsing. When an access path exists, the registries
already hold the intent and the log already holds the attempted history, so retrieval
is a small, well-defined addition. The user must supply downloaded paper files into
`source_material/pyq_raw/`, or an egress allowlist must name a real source host.
