# Session 006 — Phase-1 official-source completion report

Date: 2026-09-07
Session: 006
Branch: `main`
Result: **Phase-1 official-source scope COMPLETE** (with the standing directive's
"STOP after Phase 1" respected — no phase auto-started).

---

## What was requested

The standing 9-item directive (from a prior session) asked to finish **only the
remaining Phase-1 official-source work**:

1. Complete independent verification of the 25 extracted official facts against the
   actual notification PDFs.
2. Complete the exact official syllabus mapping from the notification and
   supplementary notification.
3. Reconcile the supplementary notification against the original.
4. Complete the official marks/exam-structure records.
5. Run all tests.
6. Fix any real failures found by the tests.
7. Inspect the final diff.
8. Update all required ledgers/state files.
9. Create a Git checkpoint only after everything is verified.

The directive also forbids inventing topic-wise weightage, inventing question
frequency, adding Instagram/YouTube knowledge, adding shortcuts, and auto-starting
another phase. Status words are restricted to `COMPLETE` / `PARTIAL` / `BLOCKED`.
Provenance tiers are never relabelled upward, and no model verifies its own output.

## What was actually completed

Prior sessions had already established 24 of 25 verified facts and the 27-node
syllabus. Two official-source items were still open. This session closed both:

1. **Official marks / exam-structure records** (`T-0037`) — `knowledge/weightage/
   official_marks_structure.json` now holds **14 verified entries** (6 for the
   Preliminary Written Test, 8 for the Final Written Examination), built from
   DOC-OFF-002 pages 19–24 and 42–44. The notification prints per-paper totals,
   durations, qualifying thresholds and the negative-marking rule, but **prints no
   topic-wise marks distribution**, so `official_topic_weightage_provided_by_notification`
   is `false` and no per-topic weightage is recorded. Each entry carries a
   mechanically re-checked verbatim quote.

2. **Supplementary-vs-original reconciliation** (`T-0051`, new task) — `knowledge/
   official/current_official.json` now holds **5 records** (REC-001–REC-005)
   settling the supplementary notification (DOC-OFF-003) against the base
   notification (DOC-OFF-002): DOC-OFF-003 amends **only** the upper age limit
   (GO Ms No. 122, +2 years, on top of GO Ms No. 87's +5). The governing general
   upper limit is derived as **32 years** as on 1 July 2026. It is uniquely a
   derived reading (25 + 5 + 2), presented as derived, never as a verbatim
   official figure, and is recorded as additive — not a contradiction.

3. **Test coverage** — added the two missing test categories the reconciliation
   registry requires (record well-formedness/sourcing, and additive-amendments
   must not be mislabelled as conflict), plus anti-vacuity fabricated-data cases,
   and extended the mechanical evidence test to re-check **every** quote across
   all three official registries, not just the facts file.

## What was verified (and how)

- **Validator** (`python scripts/validate_bootstrap.py`) — **21 / 21 passed**, exit
  `0`. Check 18 reports the real counts: `71 knowledge record(s), 70 VERIFIED and
  declared as such; 2 harvested item(s) (2 stored file(s), 0 raw)`.
- **Full suite** (`python -m unittest discover -s tests`) — **233 tests, OK,
  0 failures, 2 skips** (both skips correct-by-design: the pdftotext-digest test
  and the live-GLM test, both absent their required optional dependency).
- **Officially sourced arithmetic** is not self-asserted: the derived upper age
  limit is recomputed by a test from the sourced components
  (`base_maximum_age_years + raise_go87_years + raise_go122_years`), and it
  matches the recorded effective figure. Recomputing is the verification, not
  re-reading the reasoning.
- **Anti-vacuity** — the new checkers are proven capable of failing: fabricated
  records (no provenance, citation to an unretrieved document, a non-official
  tier, a derived record with no derivation label, an invalid verification
  method, an additive amendment recorded as a contradiction, a reconciliation
  with no derived reading) are each rejected. A clean record set is accepted.
- **Diff review** — the complete working-tree diff was inspected (item 7) before
  the checkpoint; see **Files created / modified** below. No invented facts, no
  relabelled tiers, no weakened tests.

## What remains

- **`OFF-F03` (application dates)** remains honestly `BLOCKED` — the base
  notification itself defers the application dates to a future press release.
  This is a source-level gap, not an extraction gap, and is recorded as such.
- **4 of 6 registered official documents** (`DOC-OFF-001`, `DOC-OFF-004`,
  `DOC-OFF-005`, `DOC-OFF-006`) remain unread; the two that matter to the SI
  (notification + supplement) are read.
- **No topic-wise official weightage exists** because the notification prints
  none; that absence is by design and is recorded, not filled with a guess.

## What is blocked

- **`B-09`** — this environment still cannot fetch a board URL (egress allowlist).
  Only the user-supplied download path resolved the two relevant documents. The
  blocker stays open: the four remaining documents and the `CONF-OFF-001` domain
  question wait on an egress-enabled fetch.
- **`B-02`** — no previous-year paper acquired, so observed weightage and
  `pyq_similarity` cannot be computed (no denominator ⇒ no number).
- **`B-08`** — Instagram access path is a user decision; both the ingestion and
  the knowledge pipeline are built and tested end-to-end but have no real raw
  content.

## Files created / modified

Modified (all on `main`, working tree):
- `knowledge/weightage/official_marks_structure.json` — 14 verified entries
- `tests/official/test_official_knowledge.py` — +13 tests (6 reconciliation,
  7 fabricated-data / anti-vacuity) and 2 new checker functions
- `tests/official/test_official_evidence.py` — extended to re-check every quote
  across all three official registries via `_all_quote_blocks()`
- `KNOWLEDGE_LEDGER.md` (prior session — count updated to 70)
- `knowledge/official/README.md` — current-state narrative
- `knowledge/weightage/README.md` — current-state narrative
- `SOURCE_LEDGER.md` — current-state narrative
- `TASK_LEDGER.md` — `T-0037` → `COMPLETE`; `T-0051` added → `COMPLETE`
- `PROJECT_STATE.md` — snapshot, component-status rows, next-action, session
  history

Created (untracked until this checkpoint):
- `knowledge/official/current_official.json` — 5 reconciliation records
- `docs/reports/2026-09-07-session006-official-completion.md` — this report

## Tests executed

- `python scripts/validate_bootstrap.py` — 21/21 PASS, exit `0`
- `python -m unittest discover -s tests` — 233 tests, OK (2 skipped)

## Test results

```
VALIDATOR: 21 passed, 0 failed, 21 checks total — RESULT: PASS
UNIT TESTS: Ran 233 tests in 127.560s — OK (skipped=2)
```

## Evidence

- Output quoted above (`21 passed, 0 failed`; `Ran 233 tests ... OK (skipped=2)`).
- Document hashes: `config/official_documents.json` (DOC-OFF-002, DOC-OFF-003)
  + `research/extractions/official/EXTRACTION_MANIFEST.json`.
- Test counts: `test_official_evidence.py` 4; `test_official_knowledge.py` 82
  (2 skips); project suite total 233.

## Recommended next task

Per the directive, session 006 is a **STOP point** — no phase is auto-started.
The single decision that unblocks the most downstream work is the Instagram
access path (`B-08`, user decision). If Instagram is deferred, the highest-value
alternative is **acquiring previous-year papers (`B-02`)**, which unlocks observed
topic weightage and `pyq_similarity`; second is **writing the data-model spec
(`D-0010`)** now that real record shapes exist; third is **resolving `CONF-OFF-001`**
once an official board URL is reachable (`B-09`).
