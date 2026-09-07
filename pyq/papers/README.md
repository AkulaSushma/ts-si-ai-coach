# pyq/papers/ — Normalized paper records

One JSON record per previous-year Telangana Police SI / Constable paper. Each record
is the normalized, machine-readable identity of a paper: which exam, which post, which
phase, which year, what it contained, and where it came from.

This folder is **empty until a paper is acquired**. An empty folder is the correct,
honest state, not a gap. Registering a paper is intent; reading it is a separate act
that requires bytes.

## Record shape

Defined in `knowledge/schemas/pyq_paper.schema.json`. Every record is `T2_HISTORICAL_PYQ`.

The three fields that keep provenance honest:

- `source_type` — `OFFICIAL_PUBLICATION` (board-served), `COACHING_COPY` (a coaching
  site's scan or transcription), or `CANDIDATE_RECALL` (reconstructed from memory).
  A coaching copy is a legitimate PYQ source but is never recorded as board-issued.
- `retrieval_status` — `RETRIEVED` / `BLOCKED` / `NOT_ATTEMPTED` / `PARTIAL`. A
  `RETRIEVED` claim requires `local_path`, `sha256` and `retrieved_on`, and the bytes
  on disk must hash to the recorded digest.
- `normalized_questions_status` — `NONE` / `PARTIAL` / `COMPLETE`. `COMPLETE` only when
  every question in the paper is extracted under `pyq/questions/`.

## Rules

- A paper record never claims a question count it has not seen. `questions_total` is
  the printed count or `null`, not an estimate.
- A paper whose incompleteness is not recorded cannot feed frequency analysis.
- A pattern observed in a paper is evidence of behaviour, never an official rule.
