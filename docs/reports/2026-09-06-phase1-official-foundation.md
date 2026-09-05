# Session 003 — Official TGPRB 2026 SI knowledge foundation

**Date:** 2026-09-06 · **Repository:** `D:\Projects\ts-si-ai-coach` · **Branch:** `main`

## Headline

The **container** for official knowledge is built, specified and tested. The
**content** is `BLOCKED` at zero: **0 of 25 official facts are `VERIFIED`, 0 of 6
official documents were retrieved, and 0 syllabus nodes exist.** Every official
request was refused before leaving this machine by a network egress allowlist that
permits exactly one unrelated host. No examination fact was written anywhere in the
repository, and no coaching-site copy was substituted for the board's own document.

Per the completion standard given for this phase, that makes the phase **`BLOCKED`**,
not `COMPLETE` — finding a notification listed in search results is not acquiring it.

## 1. Sources acquired

**None.** Zero bytes of official material reached `source_material/official/`; the
folder holds only `README.md` and `RETRIEVAL_LOG.md`.

Six documents were *enumerated and registered* as acquisition targets in
`config/official_documents.json` (`retrieved_count: 0`), and ledgered as
`SRC-0033`–`SRC-0038` in `SOURCE_LEDGER.md`:

| Document | Title | URL basis |
| -------- | ----- | --------- |
| `DOC-OFF-001` | TGPRB site root — notifications / downloads index | `OBSERVED_ON_OFFICIAL_DOMAIN` |
| `DOC-OFF-002` | SI (Civil et al) 2026 Notification dated 29-07-2026 | `INFERRED_UNVERIFIED` |
| `DOC-OFF-003` | Supplementary Notification 2026 dated 15-08-2026 | `OBSERVED_ON_OFFICIAL_DOMAIN` |
| `DOC-OFF-004` | PC (Civil et al) 2026 Notification dated 29-07-2026 | `OBSERVED_ON_OFFICIAL_DOMAIN` |
| `DOC-OFF-005` | ASI (FPB) 2026 Notification dated 29-07-2026 | `INFERRED_UNVERIFIED` |
| `DOC-OFF-006` | TSLPRB site root (possibly the controlling domain) | `UNKNOWN` |

Registration is not acquisition. `local_path` is `NOT_STORED` and `sha256` is `N/A`
for all six. `DOC-OFF-002` and `DOC-OFF-005` carry `INFERRED_UNVERIFIED` because their
URLs were constructed by analogy with sibling filenames and were never returned by the
board's own domain; whatever the site actually serves is the authority, and the
registry's URL gets corrected to match, never the reverse.

## 2. Sources inaccessible

All six, `INACCESSIBLE`, one cause — recorded as blocker **`B-09`**.

Outbound network access from this environment is restricted to an allowlist naming a
single host (`tabitoken.com`), unrelated to this project. Every board URL is refused
**before a request leaves the machine**. This is host-level denial: not rate limiting,
not a login wall, not a site outage, so retrying cannot help. The refusals are quoted
verbatim in `source_material/official/RETRIEVAL_LOG.md`.

No alternative transport and no mirror was tried, per `D-0017`: coaching-site copies of
these PDFs did appear in search results and were deliberately **not** registered,
because a mirror cannot be hashed against the publisher (`D-0015`). One further
official URL — a driver/mechanic selection press note — was seen and excluded as a
different recruitment stream; it is counted `irrelevant` in the manifest.

**Any one of these unblocks the phase:**

1. Add `tgprb.in`, `www.tgprb.in`, `www.tslprb.in` to the egress allowlist, then re-run retrieval.
2. **Simplest, needs no code and no network change:** open `https://tgprb.in/` in an ordinary browser, download the SI (Civil et al) 2026 notification and the supplementary notification, and save them into `D:\Projects\ts-si-ai-coach\source_material\official\`.
3. Run retrieval from a network context where the board domain is reachable.

The registry already holds the expected file identities, so hashing, ledgering and
fact extraction then proceed offline with no code change.

## 3. Official facts extracted

**0 of 25 `VERIFIED`. All 25 are `BLOCKED` with a written reason.**

`knowledge/official/required_facts.json` holds `OFF-F01`–`OFF-F25`, one slot per fact
the phase committed to answering: notification number and date, application window,
vacancies, post codes and names, eligibility, educational qualification, age
requirements, reservation rules, PWT structure / subjects / question count / marks /
duration / negative marking / minimum qualifying requirement, PMT requirements, PET
requirements, FWE structure / subjects / marks / duration, selection sequence, and
official preparation instructions.

Every slot carries `value: null`, `status: BLOCKED`, the `expected_document` it should
come from, and a `blocked_reason`. A slot is a question, not an answer, and is never
counted as knowledge — `KNOWLEDGE_LEDGER.md` still states `Verified knowledge records: 0`.

One conflict is recorded rather than silently resolved: `CONF-OFF-001`, whether
`tgprb.in` or `tslprb.in` is the legally controlling domain, status `UNRESOLVED`, with
`DOC-OFF-006` registered specifically to settle it (`D-0018`, `T-0038`).

## 4. Syllabus coverage count

**0 nodes mapped, out of an unknown total** — the denominator is itself unknown until
the notification is read, and inventing one would be a fabricated exam fact.

`knowledge/official/syllabus.json` exists as a hierarchical Subject → Topic → Subtopic
container with `record_count: 0` and a written reason for its emptiness. Two tests
guard it in opposite directions: an empty syllabus must state why it is empty, and it
may not remain empty once any document is `RETRIEVED`.

Coaching-derived and PYQ-derived subtopics have a separate home,
`knowledge/preparation_taxonomy/taxonomy.json`, which **forbids** the `T1_OFFICIAL`
tier by construction. Weightage is split into three files that may never be mixed:
official marks structure (`T1_OFFICIAL`, 0 entries), historical observed weightage
(`T2_HISTORICAL_PYQ`), and estimated preparation priority (`T4_AI`).

## 5. Tests and exact results

Both commands were run from the project folder after the final file change.

```
python scripts/validate_bootstrap.py
```

```
21 passed, 0 failed, 21 checks total
RESULT: PASS - repository structure and governance are intact.
exit code 0
```

Check 18 now prints real counts rather than a self-declared stub:

```
[PASS] 18. ledger claims match the filesystem
         25 knowledge record(s), 0 VERIFIED and declared as such; 0 harvested item(s)
         (0 stored file(s), 0 raw); area files {'knowledge': 9, 'pyq': 0,
         'expert_methods': 0, 'source_material': 1, 'verification': 0};
         no value without verification
```

```
python -m unittest discover -s tests -v
```

```
Ran 157 tests in 49.234s

OK
```

Per-folder, each run separately:

| Suite | Tests | Result |
| ----- | ----: | ------ |
| `tests/bootstrap` | 45 | `OK` |
| `tests/ingestion` | 43 | `OK` |
| `tests/official`  | 69 | `OK` |
| **Total**         | **157** | **`OK` — 0 failures, 0 errors, 0 skips** |

### The six required tests

Each is a test class in `tests/official/test_official_knowledge.py`:

| Required test | Class | Sample of what it enforces |
| ------------- | ----- | -------------------------- |
| 1. Official source records exist | `TestOfficialSourceRecordsExist` | registry non-empty and well-formed, ids unique, `retrieved_count` accurate, **every URL on a board host**, every `DOC-OFF-###` present in `SOURCE_LEDGER.md`, retrieval log substantive, ≥1 manifest |
| 2. Every official syllabus item mapped | `TestOfficialSyllabusIsFullyMapped` | `record_count` accurate, ids unique, every node sourced and correctly placed, sibling ordinals contiguous from 1, every node reaches a subject root, emptiness justified and forbidden once a document is retrieved |
| 3. Every official fact has provenance | `TestEveryOfficialFactHasProvenance` | all 25 ids present exactly once, every `expected_document` registered, `verified_count` accurate, whole-set status declared |
| 4. No unsupported official claim | `TestNoUnsupportedOfficialClaim` | every `RETRIEVED` document hashes to its recorded digest, every file in the official folder is registered, a fact with a value names a document whose bytes exist, and with nothing retrieved there is no fact value, no syllabus node and no marks entry |
| 5. Official and inferred stay separated | `TestOfficialAndInferredStaySeparated` | taxonomy forbids `T1_OFFICIAL`, three weightage files hold three fixed tiers, no entry claims another file's tier, no document is both `INFERRED_UNVERIFIED` and `RETRIEVED`, excluded source types declared |
| 6. Missing / blocked sources recorded | `TestBlockedSourcesAreRecordedExplicitly` | every manifest balances `expected = processed + inaccessible + irrelevant + duplicate + failed`, item lists match their counts, every unretrieved document named in a manifest, unresolved conflicts name what would settle them, every recorded attempt appears verbatim in the retrieval log, every cited `B-##` declared in `PROJECT_STATE.md` |

### Proof the tests are not vacuous

A suite that cannot fail proves nothing, so every checker is a pure function over plain
data and `TestCheckersRejectFabrication` feeds each one poisoned records: a value with
no provenance document, a value citing an unretrieved document, a missing verbatim
quote, `SELF_REVIEW` offered as a verification method, a value held while `BLOCKED`, an
upgraded tier, `VERIFIED` with no value, a missing hash, a truncated hash, `BLOCKED`
with no recorded attempt, an unretrieved document claiming stored bytes, a thin
`url_basis`, an unsourced syllabus node, a subject with a parent, a subtopic hung
directly off a subject, a missing parent, a `T1_OFFICIAL` node inside the preparation
taxonomy, an empty `derived_from`, a bad anchor, an unbalanced manifest, an `expected`
count with no basis, a blocked-but-processed source, a **hash mismatch against a real
temporary file**, an absent file, a path outside `source_material/official/`, and a
coaching-domain host. Each is required to be rejected. Two further tests —
`test_a_clean_record_set_is_accepted` and `test_a_balanced_manifest_is_accepted` —
prove the checkers are not simply always-failing.

### The one bootstrap change, and why it was necessary

The instruction was not to rebuild the bootstrap unless a genuine defect was found. One
was: check 18 and its mirrored test both **said in their own output** that real
counting was "not implemented yet", and the test additionally instructed that once
records existed on disk it "must be updated to check real counts". Session 003's 25
fact slots are exactly that condition.

Both were replaced with real two-directional reconciliation — registry-declared counts
against actual records, and ledger-declared figures against computed totals, plus "no
value without `VERIFIED`" and "`VERIFIED` requires a provenance document". The
replacement test drives a pure `reconcile()` over fabricated data: a value without
verification, a `VERIFIED` record with no provenance, a wrong `record_count`, a
`record_count` with no record list, an overstated knowledge ledger, an overstated
source ledger, an `AVAILABLE` row with nothing stored, and a ledger stating no figure
at all are each rejected — while a consistent zero state *and* a consistent
one-file/one-verified-record state are both accepted, proving it is not hardwired to
zero. Strictly stronger than what it replaced; no test was weakened, skipped or deleted.

Two tests failed on their first run, and were fixed by correcting the repository rather
than the tests: `test_every_blocker_referenced_is_declared_in_project_state` reported
`['B-09']` (the blocker had not yet been declared) and
`test_every_document_appears_in_the_source_ledger` reported all six `DOC-OFF-###` ids
(the ledger rows were missing). The tests forced the ledger updates.

## 6. Files created / modified

**Created**

| Path | Purpose |
| ---- | ------- |
| `specs/features/official-knowledge-foundation.md` | `SPEC-OFF-001`, status `APPROVED`; §6 acceptance criteria, §9 container-vs-content rule |
| `config/official_documents.json` | 6-document registry, conflicts, `not_registered`, `excluded_source_types` |
| `knowledge/official/required_facts.json` | 25 fact slots, all `null` / `BLOCKED` |
| `knowledge/official/syllabus.json` | Subject → Topic → Subtopic container, 0 nodes, reason recorded |
| `knowledge/preparation_taxonomy/taxonomy.json` | Non-official taxonomy; forbids `T1_OFFICIAL` |
| `knowledge/weightage/official_marks_structure.json` | `T1_OFFICIAL`, 0 entries |
| `knowledge/weightage/historical_observed.json` | `T2_HISTORICAL_PYQ` |
| `knowledge/weightage/estimated_priority.json` | `T4_AI` |
| `knowledge/schemas/official_document.schema.json`, `official_fact.schema.json`, `syllabus_node.schema.json` | Declarative schemas, enforced by hand-written checks |
| `knowledge/official/README.md`, `knowledge/preparation_taxonomy/README.md`, `knowledge/weightage/README.md` | Folder rules for each new area |
| `source_material/official/RETRIEVAL_LOG.md` | Verbatim refusals for every attempt |
| `research/manifests/official/2026-09-06-tgprb-si-2026.json` | Balanced accounting manifest |
| `research/plans/PLAN-OFF-001-official-source-acquisition.md` | Retrieval plan and document expectations |
| `tests/official/test_official_knowledge.py` | 69 tests — the six required tests plus anti-vacuity cases |
| `tests/official/__init__.py` | Package marker so `unittest discover` finds the folder |
| `docs/reports/2026-09-06-phase1-official-foundation.md` | This report |

**Modified**

| Path | Change |
| ---- | ------ |
| `scripts/validate_bootstrap.py` | Check 18 rewritten from a self-declared stub into real reconciliation |
| `tests/bootstrap/test_bootstrap.py` | `TestHonestyOfState` rewritten around a pure `reconcile()`; 1 stub test → 11 tests |
| `SOURCE_LEDGER.md` | `SRC-0033`–`SRC-0038` added; state line now reads 38 entries, harvested items 0 |
| `KNOWLEDGE_LEDGER.md` | 25 blocked slots and the container/content split recorded; still `Verified knowledge records: 0` |
| `PROJECT_STATE.md` | `B-09` added; snapshot, component status, phase narrative and session history updated |
| `TASK_LEDGER.md` | `T-0023`–`T-0032`, `T-0039` completed; `T-0033`–`T-0038` opened as `BLOCKED` |
| `DECISIONS.md` | `D-0015`, `D-0016`, `D-0017` accepted; `D-0018` opened |

## 7. Git status

Verification was run **before** committing, as instructed. Both checks passed, so three
checkpoints were created on `main`:

```
fa76278 docs(state): record session 003 — 0 of 25 official facts, blocker B-09
77967da test(bootstrap): replace ledger reconciliation stubs with real counting
a209e05 feat(official): official knowledge foundation — container COMPLETE, facts BLOCKED
```

`git status --short` is empty — the working tree is clean. Both checks were re-run
after the final commit: validator `21 passed, 0 failed`, exit `0`; suite `Ran 157
tests … OK`. No `.env`, `*.key`, `*.pem` or credentials file is tracked (checked with
`git ls-files`). Nothing under `source_material/`, `knowledge/`, `pyq/`,
`expert_methods/`, `verification/` or `data/` was deleted.

## 8. Recommended next task

**`T-0033` — get the two SI notification PDFs into `source_material/official/`.**

This is the highest-value action in the whole project and it needs no code: 25 fact
slots, the official syllabus, the marks structure, `physical/standards/` and
`CONF-OFF-001` are all waiting on bytes. Download from `https://tgprb.in/` in a normal
browser and save into `D:\Projects\ts-si-ai-coach\source_material\official\`; the next
session hashes each file, ledgers it, and extracts the facts one at a time with
document id, page or section, and a verbatim quote.

Still open in parallel: the Instagram access decision (`T-0019` / `B-08`) — permitted
authenticated access, a different network context, or deferral. The offline pipeline is
ready either way.
