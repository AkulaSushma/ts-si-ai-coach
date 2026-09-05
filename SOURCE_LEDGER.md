# SOURCE_LEDGER.md — Register of every source ever used

Append-only. Every externally acquired item gets an entry here **in the same session
it is acquired**. Material with no ledger entry is unusable by policy, because a claim
whose origin is unknown cannot be checked, corrected, or defended.

## Current state

**Entries: 0.** No sources have been acquired yet. Research has not begun — this was
explicitly out of scope for bootstrap.

This zero is a real, verified count, not a placeholder.

## ID format

`SRC-####` — assigned sequentially, never reused, never renumbered.

## Required fields

| Field             | Meaning                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `id`              | `SRC-####`                                                          |
| `title`           | Human-readable name                                                 |
| `tier`            | `T1_OFFICIAL` / `T2_HISTORICAL_PYQ` / `T3_EXPERT` / `T4_AI`          |
| `origin`          | Full URL, or physical description for print material                |
| `publisher`       | TGPRB, channel name, author, institute                              |
| `acquired_on`     | ISO date the material was obtained                                  |
| `acquired_by`     | Session or run identifier                                           |
| `local_path`      | Path under `source_material/`, or `NOT_STORED` with the reason      |
| `checksum`        | SHA-256 of the stored file, or `N/A`                                |
| `language`        | `en` / `te` / `both`                                                |
| `access_status`   | `AVAILABLE` / `PAYWALLED` / `REMOVED` / `INACCESSIBLE`              |
| `reliability`     | `AUTHORITATIVE` / `GENERALLY_RELIABLE` / `UNKNOWN` / `UNRELIABLE`   |
| `notes`           | Known errors, caveats, corrigenda affecting this source             |

## Rules

- Record the URL even when the file is not stored locally. A dead link with a date is
  still better provenance than nothing.
- Never upgrade `tier` because a source seems trustworthy. Tier describes *what kind of
  source it is*, not how much it is liked.
- When a source is later found to contain an error, do not delete the entry. Add the
  error to `notes` and re-check every knowledge record citing it.
- Store a checksum for anything stored locally, so silent corruption or replacement is
  detectable.

## Entries

_None yet._

| id | title | tier | origin | publisher | acquired_on | access_status | reliability |
| -- | ----- | ---- | ------ | --------- | ----------- | ------------- | ----------- |
