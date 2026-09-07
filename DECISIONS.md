# DECISIONS.md — Architecture Decision Record

Append-only. Never edit a past decision; supersede it with a new one and mark the old
one `SUPERSEDED`, linking both ways. Understanding *why* a choice was made is what
stops a future session from undoing it by accident.

Status values: `ACCEPTED`, `OPEN`, `SUPERSEDED`, `REJECTED`.

---

## D-0001 — Single-user, local-only system

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** user

**Decision.** The system runs on the user's own PC for the user alone. No user
accounts, no authentication, no hosting.

**Why.** The user is one candidate preparing for one exam. Authentication, hosting,
and multi-tenancy would add substantial work and cost before producing any study
value. Building them speculatively delays the thing that actually helps.

**Consequences.** The backend binds to `127.0.0.1` only. Because there is no
authentication, exposing the port on a network would publish an unauthenticated API —
so the bind address is a security control, not a detail. If multi-user access is ever
wanted, authentication must be specified and built *before* any network exposure.

---

## D-0002 — Python 3.10+, FastAPI, SQLite via stdlib `sqlite3`

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** user

**Decision.** Backend in Python. HTTP layer FastAPI. Storage SQLite through the
standard-library `sqlite3` module. No ORM until a spec justifies one.

**Why.** Python is the most readable language for a beginner to inspect, and the
libraries this project depends on — PDF parsing, transcript handling, data analysis,
AI SDKs — are strongest in Python. SQLite needs no server process to install, run, or
secure, and the whole database is a single file the user can back up by copying it.

**Consequences.** Verified present in the environment: Python 3.10.12. Concurrency is
limited by SQLite's single-writer model, which is irrelevant for one user. If the
project ever becomes multi-user, PostgreSQL would be reconsidered.

---

## D-0003 — Frontend framework deferred

**Status:** OPEN · **Date:** 2026-09-05

**Decision.** Not yet made. No UI framework is chosen or installed during bootstrap.

**Why deferred.** The right UI shape depends on what the tutor and practice engine
actually need, which is not known yet. Choosing a framework now would be guessing, and
an installed framework is harder to remove than to add.

**Resolve when.** The first screen spec in `specs/features/` reaches `APPROVED`.

---

## D-0004 — English authoritative, Telugu companion fields from day one

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** user

**Decision.** All content is authored in English. Every user-visible text field gets a
nullable Telugu companion field suffixed `_te`, created at the same time as the
English field.

**Why.** The TGPRB SI examination is conducted in English and Telugu, so Telugu
support is likely to be needed eventually. Requiring both languages now would roughly
double content effort and stall early progress. Creating the empty columns up front
costs nothing and means adding Telugu later is data entry, not a schema migration of
populated tables.

**Consequences.** Schemas and migrations must add `_te` fields at creation time —
this is enforced by review, and is a documented rule in `database/README.md`. A record
with an empty `_te` field is valid; the field is never filled by machine translation
without being labelled as such.

---

## D-0005 — Providers: Anthropic (Claude) and GLM / Z.ai (GLM 5.3)

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** user

**Decision.** Two providers are available: Anthropic (Claude) and GLM / Z.ai
(GLM 5.3). Role-to-model assignment lives in `config/model_routing.json`.

**Why.** Two independent providers is the minimum needed to make the
"a model may not verify its own output" rule enforceable rather than aspirational.

**Consequences.** With exactly two providers there is no independent third party for
`ARBITRATION`. When the two disagree, the dispute cannot be resolved by a neutral
model. Policy: such disputes stay `DISPUTED`, are recorded in
`verification/disputes/`, and are escalated to the user — never resolved by asking one
of the two disputants to judge itself. Adding a third provider later would relax this.

---

## D-0006 — Tests use the standard library `unittest`

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** architect

**Decision.** Automated checks use Python's built-in `unittest`. No pytest, no plugins,
during bootstrap.

**Why.** A test suite that requires an install step before it runs is a test suite that
stops being run. Zero dependencies means the user can verify the project at any time
with one command and no setup. The user also asked that no unnecessary frameworks be
installed during bootstrap.

**Consequences.** Some pytest conveniences are unavailable. If the suite grows to the
point where that genuinely costs time, this decision can be superseded — but not
before, and not for style reasons.

---

## D-0007 — Git repository initialised inside the existing project folder

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** architect

**Decision.** `git init` was run in place at `D:\Projects\ts-si-ai-coach` on branch
`main`. No separate project directory was created anywhere else.

**Why.** The user explicitly required that work happen inside their existing D: drive
project. Inspection confirmed the folder contained only `.claude/settings.local.json`
and no `.git`, so initialising in place risked nothing and preserved the existing file.

**Consequences.** `.claude/settings.local.json` is a local editor permission file. It
is excluded from Git via `.gitignore` because it is machine-specific and not project
content. The file itself was left untouched on disk.

---

## D-0008 — Raw sources kept out of Git, structured records kept in

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** architect

**Decision.** Large binaries under `source_material/` (video, audio, book scans, large
PDFs) are git-ignored. The structured records derived from them, and their
`SOURCE_LEDGER.md` entries, are committed.

**Why.** Git stores every version of every binary forever and cannot diff them; a few
hundred lecture videos would make the repository unusable within weeks. The valuable,
reviewable, diffable artefact is the extracted structured knowledge, not the raw media.

**Consequences.** Raw material is **not** protected by Git and must be backed up by
copying the folder. This is stated in `source_material/README.md` and `data/README.md`
because it is the most likely way for the user to lose real work. Provenance survives
even if a binary is lost, because the ledger records the original URL and acquisition
date.

---

## D-0012 — Ingestion subsystem: registry-driven, adapter-per-platform, collection separated from intelligence

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** user instruction, session 002

**Decision.** A multi-platform ingestion subsystem lives at
`backend/app/ingestion/` inside this project, operated via `scripts/ingest.py`.
Sources are registered in `config/source_registry.json` (adding a URL never
requires code change); each platform implements the `SourceAdapter` interface;
the runner enforces a hard per-source cap of 299 content items (posts,
carousels, and reels counted against one budget); raw records are immutable
and preserve unavailable fields as `null`; checkpointing is mandatory and
resume is idempotent; nothing is discarded as "irrelevant" during collection.

**Why.** The user's task instruction for session 002 is the requirements
document; it mandates exactly this separation (registry / raw / normalized /
candidate / verified / questions / provenance) and the 299 cap, and prohibits
creating a separate project. Instagram is the first adapter; the interface
(`adapters/base.py`) leaves room for YouTube, Telegram, websites, and PDFs
without runner/storage/CLI changes.

**Consequences.** Raw Instagram content is `T3_EXPERT` tier and never enters
the trusted knowledge base directly. OCR/transcription and GLM classification
are later stages; the normalized record carries their scaffold with null
values so no later stage can claim ingestion produced classifications.

---

## D-0013 — Platform access refusals are recorded, never bypassed

**Status:** ACCEPTED · **Date:** 2026-09-05 · **Decided by:** architect, per user instruction

**Decision.** When a platform refuses access (HTTP 401/403/429, login wall,
empty-but-ok payload), the adapter raises `AccessBlockedError`, the runner
writes a `blocked`/`partial` checkpoint with an error-log entry and a balanced
manifest, and stops. Polite behavior only: single requests, delays with
jitter, bounded retries with backoff. No credential use, no request
escalation, no bypass of any access control, and no fabrication of data that
was never received.

**Why.** The user's instruction is explicit: respect available access
mechanisms, rate limits, authentication requirements, and platform rules.
It also aligns with the project's honesty principle — a blocked source is a
recorded fact, and pretending otherwise (by hammering or spoofing) would both
violate platform terms and produce unreliable data.

**Consequences.** Session 002's live test (IG001) is `BLOCKED` by an
Instagram 429 refusal of anonymous API access; the profile HTML page is a
JS-only shell with no posts. Resolution is a user decision (`B-08` in
`PROJECT_STATE.md`): authenticated access the platform permits, a different
network context, or deferral. The subsystem needs no code change for any of
these outcomes — only the access mechanism or the network does.

---

## D-0015 — Only the board's own domain is authority for an official fact

**Status:** ACCEPTED · **Date:** 2026-09-06 · **Decided by:** user instruction, session 003

**Decision.** A `T1_OFFICIAL` fact may cite only a document served from a TGPRB /
TSLPRB host (`tgprb.in`, `tslprb.in`, or a subdomain). Coaching websites, Instagram,
YouTube, Telegram, Reddit, blogs, PDF re-hosts and search-result summaries are never
authority for an official rule, even when they reproduce the notification exactly and
even when the official domain is unreachable. Such material may enter
`SOURCE_LEDGER.md` later as `T3_EXPERT`; it may never be relabelled upward.

**Why.** The user's instruction says so directly, and the reason holds independently:
a mirror cannot be hashed against the publisher. If a coaching site drops a clause,
renumbers a section, or reproduces a superseded version, nothing downstream can detect
it. Physical standards and mark schemes are the facts a candidate trains against for
months — a wrong number there is not a cosmetic error.

**Consequences.** `official_host()` in `tests/official/test_official_knowledge.py`
enforces the host rule mechanically, and
`test_every_registered_url_is_on_an_official_host` rejects any registry URL that is
not on a board domain. When the board site is unreachable the correct outcome is
`BLOCKED` with the refusal recorded — this is what happened in session 003 (`B-09`),
and several coaching mirrors of the notification appeared in search results and were
deliberately not registered.

---

## D-0016 — A complete container never implies complete content

**Status:** ACCEPTED · **Date:** 2026-09-06 · **Decided by:** architect, per user instruction

**Decision.** Structure and content carry separate statuses. A phase whose schemas,
registries, slots, manifests and tests are all verifiable offline may report those
artefacts `COMPLETE` while the phase itself is `BLOCKED` because no fact was
extracted. Passing container tests is explicitly not a licence to report the phase
`COMPLETE`; that sentence is written into `SPEC-OFF-001` §9 so a later session cannot
mistake one for the other.

**Why.** This is the failure mode the whole project is built to prevent. 25 fact slots
with a schema, a registry of 6 documents and 69 passing tests look like an achievement
and can be produced without ever reading the notification. The user's completion
standard is unambiguous: `COMPLETE` requires acquired documents, extracted facts, a
mapped syllabus and recorded provenance — "Do NOT report COMPLETE merely because you
found a notification."

**Consequences.** `PROJECT_STATE.md` states the split in its Snapshot and Current
Phase sections; `KNOWLEDGE_LEDGER.md` keeps `Verified knowledge records: 0` while 25
slots exist; and the reconciliation in `scripts/validate_bootstrap.py` check 18 fails
if any slot ever holds a value without being `VERIFIED`, so the split cannot quietly
collapse in either direction.

---

## D-0017 — An egress refusal is recorded, never routed around

**Status:** ACCEPTED · **Date:** 2026-09-06 · **Decided by:** architect, per environment policy

**Decision.** When this environment refuses an outbound request, the refusal is quoted
verbatim into `source_material/official/RETRIEVAL_LOG.md` and the dependent work is
marked `BLOCKED`. No alternative transport is attempted: no `curl`, `wget` or `lynx`,
no Python HTTP client, no other language, and no cached, archived or mirrored copy of
the blocked page.

**Why.** The environment's fetch restrictions exist for legal and compliance reasons
and apply to every retrieval method, not just the fetch tool. Beyond that, an archive
copy would fail `D-0015` anyway: it is not served by the board, so it cannot be hashed
against the publisher.

**Consequences.** Session 003's six document requests were all refused before leaving
the machine by an egress allowlist naming exactly one unrelated host (`tabitoken.com`),
recorded as `B-09`. Because the refusal is host-level rather than a rate limit, a login
wall or an outage, retrying changes nothing — the unblock routes are a network change
or a manual download into `source_material/official/`. The registry already holds the
six expected file identities, so hashing and fact extraction proceed offline with no
code change once bytes exist.

---

## D-0019 — Candidate knowledge is UNVERIFIED by construction; corroboration is not verification

**Status:** ACCEPTED · **Date:** 2026-09-06 · **Decided by:** user instruction, session 005 (SPEC-KNW-001)

**Decision.** Social-media-derived content flows through a separate candidate
layer and may never be treated as verified truth. The pipeline
(`backend/app/knowledge/`) can only create records with `verification_status:
UNVERIFIED`; it has no verify method at all. Multiple accounts repeating a
claim are recorded as corroboration (`source_count`, `supporting_sources`,
`source_diversity`) on a single concept — and every concept carries
`corroboration_is_not_verification: true`. Verification remains a separate
stage consuming the append-only queue, whose required verifier provider is
resolved at queue time from `config/model_routing.json` and must differ from
the authoring provider.

**Why.** The user's instruction is explicit: social-media content must
initially become candidate knowledge; a claim repeated by many coaching
accounts is still one social-media claim, possibly copied from a single wrong
origin. This also aligns with `VERIFICATION_POLICY.md` (no self-verification;
capability is not evidence) and with the provenance-tier rule (coaching
content is `T3_EXPERT`, never relabelled upward).

**Consequences.** The trusted `knowledge/` layer is untouched by the pipeline.
Test `test_pipeline_has_no_verify_method` asserts the structural
impossibility, and queue tests assert every line is `UNVERIFIED` with a
distinct verifier provider. Promotion to `VERIFIED` requires a future
verification run recorded under `verification/runs/` — none exists yet.

---

## D-0020 — Deterministic dedup via curated synonym data, not fuzzy similarity

**Status:** ACCEPTED · **Date:** 2026-09-06 · **Decided by:** architect, per user instruction session 005

**Decision.** Concept deduplication groups candidates by a key over
stopword-stripped, order-insensitive content words, canonicalized through a
small human-reviewed synonym table (`config/dedup_synonyms.json`), plus the
knowledge type. No embedding, no similarity threshold, no model call.
Negation words are never stopwords or synonyms, so a fact and its negation
can never merge. Provenance is append-only: a concept keeps its first
representative text and gains every supporting source.

**Why.** A similarity threshold (e.g. token-overlap ≥ 0.8) would silently
merge genuinely different facts that merely share vocabulary ("The President
is elected by an electoral college" vs "The Vice President is elected by an
electoral college"), and would make dedup nondeterministic across model
versions. The user's own example — "Fundamental Duties were added by the 42nd
Amendment" vs "The 42nd Amendment introduced Fundamental Duties" — differs by
one surface verb, exactly the variation a curated table handles safely and a
threshold handles dangerously.

**Consequences.** New phrasings that should collide require adding a row to
`dedup_synonyms.json` — a data review, not a code change, each row auditable.
The 42nd-Amendment pair is a fixture test and must keep colliding. A future
embedding-based assistant may *propose* merges, but only deterministic keys
decide.

---

## D-0021 — pyq_similarity stays null until a counted PYQ denominator exists

**Status:** ACCEPTED · **Date:** 2026-09-06 · **Decided by:** architect, session 005

**Decision.** The `pyq_similarity` field exists on every candidate but is
always `null` until previous-year papers are acquired and counted. No
estimated, model-guessed, or rounded value is ever written.

**Why.** TEST_PLAN.md L3 forbids percentages from uncounted denominators; a
"similarity to PYQs" number with no PYQ database would be fabricated
precision. The user's required schema asks for the field — so the field
exists, and its basis string records why it is null.

**Consequences.** `docs/relevance_scale.md` §5 documents the rule; scoring
tests assert the null. When `B-02` unblocks, the rule is recomputed and the
scale version is bumped.

---

## D-0022 — A coaching copy of a paper is T2 evidence of behaviour; a coaching copy of an official document is never T1

**Status:** ACCEPTED · **Date:** 2026-09-07 · **Decided by:** architect, per user instruction session 007 (SPEC-PYQ-001)

**Decision.** Previous-year **papers** are evidence of what was asked, not policy.
A coaching site's scan or transcription of a paper is recorded as
`source_type: COACHING_COPY` and is legitimately `T2_HISTORICAL_PYQ` — it is
evidence of the questions that appeared, subject to its answer being tracked
separately by `answer_source` (`OFFICIAL_KEY` / `COACHING_KEY` / `UNVERIFIED`).
This does **not** contradict `D-0015`, which governs a different object: a
coaching copy of an **official document** (a notification, a physical standard, a
mark scheme) is never authority for a `T1_OFFICIAL` rule. A paper copy being `T2`
is not a relabel upward to `T1`.

**Why.** The board does not publish solved papers, so coaching copies are the
realistic route to a paper set; treating them as `T3_EXPERT` would wrongly equate
a *paper's contents* (historical evidence) with a *coach's opinion or method*
(also `T3_EXPERT`). But the two provenance tiers must stay distinct, and the
distinction must be written down or a future session will read `D-0015` and
`SPEC-PYQ-001 R2` as a contradiction.

**Consequences.** In the PYQ registries, a paper records both `source_type`
(how it was obtained) and `provenance_tier` (always `T2_HISTORICAL_PYQ`); a
question records `answer_source`. An `OFFICIAL_PUBLICATION` paper must point at a
board host (`tests/pyq` enforces with `board_host()`), and a question labelled
`OFFICIAL_PUBLICATION` must have a board-host provenance URL. Coaching material as
*opinion or method* remains `T3_EXPERT`.

---

## Open decisions

| ID       | Question                                              | Resolve when                                  |
| -------- | ----------------------------------------------------- | --------------------------------------------- |
| `D-0003` | Which frontend framework                              | First UI spec is `APPROVED`                    |
| `D-0009` | Which model fills each agent role                     | API access confirmed and cost/quality measured |
| `D-0010` | Knowledge storage: files, SQLite, or both             | Data-model spec is written                     |
| `D-0011` | Spaced-repetition algorithm (SM-2, FSRS, or custom)   | Revision feature spec is written               |
| `D-0014` | Instagram access mechanism: anonymous (currently refused) / permitted authenticated access / different network context / defer | User decision, tracked as `B-08` / `T-0019` |
| `D-0018` | Which board domain is legally controlling — `tgprb.in` or `tslprb.in` (`CONF-OFF-001`) | Both site roots can be read; tracked as `T-0038` |


