# knowledge/official/ — `T1_OFFICIAL` records only

Everything in this folder must be traceable to a TGPRB / TSLPRB document that has been
retrieved, stored under `source_material/official/`, and hashed. Nothing else may be
written here, at any time, for any reason.

## Files

| File | Holds |
| ---- | ----- |
| `required_facts.json` | The 25 facts Phase 1 must establish (`OFF-F01`…`OFF-F25`), each a slot with a provenance block |
| `syllabus.json` | The official syllabus as Subject → Topic → Subtopic nodes |

Specification: `specs/features/official-knowledge-foundation.md` (`SPEC-OFF-001`).

## Current state — 2026-09-06

**`BLOCKED`. Zero facts verified, zero syllabus nodes.** No official document has been
retrieved: this environment's network egress permits exactly one host, which is
unrelated to this project, so no official URL can be fetched from here at all. The
verbatim refusals are recorded in `source_material/official/RETRIEVAL_LOG.md` and in
`config/official_documents.json`, and the blocker is `B-09` in `PROJECT_STATE.md`.

An empty folder here is the correct state, not an unfinished one. The structures, the
provenance slots and the tests exist; the content requires the document.

## What must never happen here

- A value written without `provenance.document_id` resolving to a `RETRIEVED` document.
  `tests/official/test_official_knowledge.py` fails if one appears.
- A syllabus node taken from a coaching syllabus, a YouTube description, an aggregator
  article, or model recall. Those are `T3_EXPERT` or `T4_AI` and belong elsewhere.
- Quoting a search-result snippet as if it were the document. A snippet is evidence
  that a document exists, not evidence of what it says.
- Physical standards written into this folder as a workaround for `physical/standards/`
  being enforced empty. `OFF-F18` and `OFF-F19` stay `BLOCKED` until sourced.

## When a document does arrive

1. Store the file under `source_material/official/`, record its SHA-256, and set the
   matching entry in `config/official_documents.json` to `RETRIEVED`.
2. Add a `SOURCE_LEDGER.md` row in the same session.
3. Fill facts one at a time, each with page, section and a verbatim quote.
4. Build syllabus nodes strictly from the document's own wording and order.
5. Run `python -m unittest discover -s tests` — the Phase-1 tests then check
   provenance for every populated record rather than merely checking emptiness.
