"""Ingestion subsystem.

Shared package implementing `SPEC-ING-001` (`specs/features/ingestion-subsystem.md`).
Standard library only (`D-0006`). Operated through `scripts/ingest.py`; nothing here
is imported by the future FastAPI app until that app's spec is approved.

Layout:

```
ingestion/
  __init__.py
  taxonomy.py       fixed enums: subjects, knowledge types, relevance, statuses
  registry.py       source registry loading, validation, id assignment
  adapters/
    __init__.py
    base.py         SourceAdapter interface + shared dataclasses + errors
    instagram.py    Instagram adapter (first adapter; others later)
  storage/
    __init__.py
    raw_store.py    durable raw records under data/raw/<platform>/<source_id>/
    normalized.py   normalization to data/normalized/<platform>/<source_id>/
    checkpoint.py   checkpoint documents + error log + harvest manifest writers
  runner.py         platform-agnostic extraction loop
  cli.py            command line entry points
```

Rules:

- Raw records are immutable once written. Idempotency depends on this.
- Nothing here writes to `knowledge/`, `pyq/`, or any trusted store. Raw
  Instagram content is `T3_EXPERT` provenance and stays in the raw/normalized
  runtime stores until the verification pipeline exists.
- Platform access controls are respected. `AccessBlockedError` means "record
  honestly and stop", never "retry harder" or "bypass".
"""
