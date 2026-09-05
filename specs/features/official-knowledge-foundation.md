# SPEC-OFF-001 — Official knowledge foundation (TGPRB SI 2026)

**Status:** `APPROVED` · **Date:** 2026-09-06 · **Session:** 003
**Requirements source:** user instruction, session 003 ("Phase 1: Official TGPRB 2026
SI knowledge foundation"). That instruction is the requirements document for this spec,
in the same way session 002's instruction was for `SPEC-ING-001`.

## 1. Purpose

Establish the structures that hold **`T1_OFFICIAL`** examination knowledge, and the
machinery that makes it impossible to record an official fact without the official
document behind it.

This spec deliberately separates two things that are usually conflated:

- **the container** — schemas, registries, provenance slots, separation rules, tests
- **the content** — the facts themselves, which come only from an official document

The container can be built and verified with no network access. The content cannot.
Building the container is therefore legitimate work; filling it from model recall is
the single most damaging thing this project could do, and the tests below exist to
prevent it mechanically rather than by good intentions.

## 2. Non-goals

- Not a syllabus written from memory, from coaching material, or from search snippets.
- Not a guess at any mark, duration, age limit, vacancy count, or physical standard.
- Not topic-wise weightage. The notification is the only thing that could make
  weightage `T1_OFFICIAL`, and only if it states weightage explicitly.
- Not the data-model / SQLite schema (`D-0010`, still open). These are files on disk,
  designed so a later database import is mechanical.

## 3. Authority rules

| Rule | Statement |
| ---- | --------- |
| `R1` | Only a document published by TGPRB / TSLPRB may support a `T1_OFFICIAL` fact. |
| `R2` | Coaching sites, aggregators, Instagram, YouTube, Telegram, Reddit, blogs and search-result summaries may **never** support an official fact. They may later be recorded as `T3_EXPERT`, never as authority for a rule. |
| `R3` | A search engine may be used to **locate** an official document. Its snippet text is not the document and may not be quoted as the document's content. |
| `R4` | A fact carries a value only when the document it came from has been retrieved, stored, and hashed. No document, no value. |
| `R5` | Where two official documents conflict, the conflict is recorded and the controlling document is determined explicitly. Silent selection is prohibited. |

## 4. Artefacts

| Path | Holds | Tier |
| ---- | ----- | ---- |
| `config/official_documents.json` | Target document registry: URLs, retrieval status, attempts, hashes | metadata |
| `source_material/official/RETRIEVAL_LOG.md` | Verbatim retrieval attempts and responses | evidence |
| `source_material/official/` | The retrieved documents themselves, once obtainable | `T1_OFFICIAL` |
| `knowledge/official/required_facts.json` | The 25 facts Phase 1 must establish, each with a provenance slot | `T1_OFFICIAL` |
| `knowledge/official/syllabus.json` | Official syllabus, Subject → Topic → Subtopic | `T1_OFFICIAL` |
| `knowledge/weightage/official_marks_structure.json` | Marks and duration exactly as the notification states them | `T1_OFFICIAL` |
| `knowledge/weightage/historical_observed.json` | Weightage counted from real past papers | `T2_HISTORICAL_PYQ` |
| `knowledge/weightage/estimated_priority.json` | Preparation priority judgements | `T4_AI` |
| `knowledge/preparation_taxonomy/` | Coaching/PYQ-derived subtopics the official syllabus does not name | `T3_EXPERT` / `T4_AI` |
| `knowledge/schemas/*.json` | Declarative record shapes | metadata |
| `research/manifests/official/` | Acquisition accounting for official documents | evidence |

## 5. The 25 required facts

Phase 1 must establish these, and no others, as `T1_OFFICIAL`. Each is one record in
`knowledge/official/required_facts.json` with a stable id.

| id | Fact | id | Fact |
| -- | ---- | -- | ---- |
| `OFF-F01` | Notification number | `OFF-F14` | PWT marks |
| `OFF-F02` | Notification date | `OFF-F15` | PWT duration |
| `OFF-F03` | Application dates | `OFF-F16` | PWT negative marking |
| `OFF-F04` | Number of vacancies | `OFF-F17` | Minimum qualifying requirements |
| `OFF-F05` | Post codes | `OFF-F18` | PMT requirements |
| `OFF-F06` | Post names | `OFF-F19` | PET requirements |
| `OFF-F07` | Eligibility requirements | `OFF-F20` | FWE structure |
| `OFF-F08` | Educational qualifications | `OFF-F21` | FWE subjects |
| `OFF-F09` | Age requirements | `OFF-F22` | FWE marks |
| `OFF-F10` | Reservation / category rules | `OFF-F23` | FWE duration |
| `OFF-F11` | Preliminary Written Test structure | `OFF-F24` | Selection sequence |
| `OFF-F12` | PWT subjects | `OFF-F25` | Official instructions affecting preparation |
| `OFF-F13` | PWT number of questions | | |

### Record shape

```
{
  "fact_id": "OFF-F01",
  "name": "...",
  "value": null,                  // null until the document is read
  "value_te": null,               // Telugu companion field, D-0004
  "status": "BLOCKED",            // BLOCKED | UNVERIFIED | VERIFIED
  "blocked_reason": "...",        // required whenever status != VERIFIED
  "provenance_tier": "T1_OFFICIAL",
  "provenance": {
    "document_id": null,          // must resolve to a RETRIEVED document
    "page": null,
    "section": null,
    "quote": null                 // verbatim text supporting the value
  },
  "verification": { "method": null, "verified_on": null, "verified_by": null }
}
```

`OFF-F18` and `OFF-F19` (PMT / PET) additionally land in `physical/standards/` when
sourced. That folder stays empty until then; validator check 19 enforces this, and
wrong numbers there would waste months of physical training.

## 6. Syllabus model

Strict three-level hierarchy, one node per record:

```
subject  →  topic  →  subtopic
```

Every node carries `node_id`, `level`, `parent_id` (`null` only for a subject),
`title`, `title_te`, `provenance_tier`, and the same `provenance` block as a fact.
`parent_id` must resolve to an existing node of the level above.

**No node may exist without provenance pointing at a retrieved official document.**
A topic that coaching institutes always teach but the notification does not name is
not an official syllabus node. It belongs in `knowledge/preparation_taxonomy/`,
where it may be linked to an official node by `official_anchor` or marked
`NO_OFFICIAL_ANCHOR`.

## 7. Weightage: three categories that never mix

| File | Question it answers | Tier | Source |
| ---- | ------------------- | ---- | ------ |
| `official_marks_structure.json` | What marks and duration does the notification prescribe? | `T1_OFFICIAL` | Notification only |
| `historical_observed.json` | How many questions did past papers actually ask per topic? | `T2_HISTORICAL_PYQ` | Counted PYQs only |
| `estimated_priority.json` | What should be studied first? | `T4_AI` | Judgement, explicitly derived |

Each file declares exactly one tier and is tested to contain no other tier string.
Mixing them would let "coaching institutes emphasise X" be read as "the board
weights X", which is the error this project exists to prevent.

## 8. Document registry and retrieval evidence

`config/official_documents.json` registers each document Phase 1 needs. Fields:

| Field | Meaning |
| ----- | ------- |
| `document_id` | `DOC-OFF-###`, stable, never reused |
| `title` | Title as it appears on the official document or its file name |
| `publisher` | `TGPRB / TSLPRB` |
| `url` | Full URL |
| `url_status` | `OBSERVED_ON_OFFICIAL_DOMAIN` / `INFERRED_UNVERIFIED` / `UNKNOWN` |
| `url_basis` | How the URL was obtained — required, because an inferred URL is not a fact |
| `expected_content` | Which `OFF-F##` facts this document is expected to settle |
| `retrieval_status` | `RETRIEVED` / `BLOCKED` / `NOT_ATTEMPTED` |
| `blocked_reason` | Required unless `RETRIEVED` |
| `attempts` | List of `{ timestamp, tool, url, response }` — `response` verbatim |
| `local_path` | Path under `source_material/official/`, else `null` |
| `sha256` | Hash of the stored bytes, else `null` |
| `document_date` | Date printed on the document, else `null` |
| `retrieved_on` | ISO date, else `null` |

A URL discovered through a search index is `OBSERVED_ON_OFFICIAL_DOMAIN` only when the
search result's own URL is on the official domain. A URL reconstructed by analogy with
a sibling file name is `INFERRED_UNVERIFIED` and must be confirmed by a successful
retrieval before anything is built on it.

## 9. Acceptance criteria

| # | Criterion | Verified by |
| - | --------- | ----------- |
| `AC-1` | Official source records exist, are valid JSON, carry all required fields, and each appears in `SOURCE_LEDGER.md` | Test 1 |
| `AC-2` | Every official syllabus node resolves its parent, carries provenance to a retrieved document, and no node exists without one | Test 2 |
| `AC-3` | Every fact with a non-null value has status `VERIFIED`, a resolvable retrieved document, and a verbatim quote | Test 3 |
| `AC-4` | No official record carries a value while zero official documents are retrieved; `physical/standards/` empty | Test 4 |
| `AC-5` | Official, historical, expert and AI-derived structures are physically separate and each declares one tier | Test 5 |
| `AC-6` | Every non-retrieved document records a blocked reason and a verbatim attempt; the manifest's accounting identity balances | Test 6 |
| `AC-7` | The Phase-1 checkers themselves reject a fabricated record | Test 7 (anti-vacuity) |

`AC-1` to `AC-7` are container criteria and can pass while the exam facts are unknown.
Phase 1 **content** is `COMPLETE` only when every `OFF-F##` record reaches status
`VERIFIED` and the syllabus is mapped from a retrieved document. Container criteria
passing does not license reporting Phase 1 as `COMPLETE`.

## 10. Anti-vacuity requirement

Every test above must be able to fail. Test 7 constructs poisoned in-memory records —
a fact with a value but no provenance, a syllabus node with an unresolvable parent, a
preparation-taxonomy node claiming `T1_OFFICIAL`, a document marked blocked with no
reason — and asserts each checker rejects them. A suite that only ever sees an empty
tree proves nothing about a populated one.

## 11. Out of scope for this spec

Retrieval automation. There is no scripted downloader, because the current blocker is
network reachability rather than parsing: the environment's egress allowlist permits
one unrelated host, so no official URL can be fetched from here at all. When an access
path exists, the registry already holds the URLs and the log already holds the
attempted history, so retrieval is a small, well-defined addition.


