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

## Open decisions

| ID       | Question                                              | Resolve when                                  |
| -------- | ----------------------------------------------------- | --------------------------------------------- |
| `D-0003` | Which frontend framework                              | First UI spec is `APPROVED`                    |
| `D-0009` | Which model fills each agent role                     | API access confirmed and cost/quality measured |
| `D-0010` | Knowledge storage: files, SQLite, or both             | Data-model spec is written                     |
| `D-0011` | Spaced-repetition algorithm (SM-2, FSRS, or custom)   | Revision feature spec is written               |


