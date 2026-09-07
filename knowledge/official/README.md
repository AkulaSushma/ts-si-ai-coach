# knowledge/official/ — `T1_OFFICIAL` records only

Everything in this folder must be traceable to a TGPRB / TSLPRB document that has been
retrieved, stored under `source_material/official/`, and hashed. Nothing else may be
written here, at any time, for any reason.

## Files

| File | Holds |
| ---- | ----- |
| `required_facts.json` | The 25 facts Phase 1 must establish (`OFF-F01`…`OFF-F25`), each a slot with a provenance block |
| `syllabus.json` | The official syllabus as Subject → Topic → Subtopic nodes |
| `current_official.json` | The reconciliation of the base notification (DOC-OFF-002) with the supplementary one (DOC-OFF-003) — the answer to OFF-F09's `current_official_resolution` |

Specification: `specs/features/official-knowledge-foundation.md` (`SPEC-OFF-001`).

## Current state — 2026-09-07

**Two of the six registered documents retrieved and read.** DOC-OFF-002 (the SI
2026 notification, Rc No. 225 dated 29-07-2026) and DOC-OFF-003 (the supplementary
notification dated 15-08-2026) were supplied by the user as browser downloads,
stored under `source_material/official/`, and hashed. From them:

- **24 of 25 facts** are `VERIFIED` with page/section/verbatim-quote provenance
  (`OFF-F01`…`OFF-F25`, minus `OFF-F03` which is honestly `BLOCKED` — the
  notification defers application dates to a future press release).
- **27 syllabus nodes** from Annexures II–III (pages 42–44), verbatim wording, no
  invented layer.
- **5 reconciliation records** (`current_official.json`) settling the
  supplementary against the original: DOC-OFF-003 amends only the upper age limit
  (GO Ms No. 122, +2 years on top of GO Ms No. 87's +5). The governing general
  upper limit is derived as 32 years as on 1 July 2026.

Every quote in these records is mechanically re-checked by
`tests/official/test_official_evidence.py` and `tests/official/test_official_knowledge.py`.
The other four documents (DOC-OFF-001, DOC-OFF-004, DOC-OFF-005, DOC-OFF-006)
remain `INACCESSIBLE` under blocker `B-09`.

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
