# backend/ — Python application

Status: **in partial use.** The ingestion subsystem (`backend/app/ingestion/`,
spec `SPEC-ING-001`) lives here and is fully tested offline. The FastAPI HTTP
layer remains unbuilt until its spec is approved.

## Planned stack (decision D-0002 in `DECISIONS.md`)

- Python 3.10+
- FastAPI for the HTTP layer
- SQLite via the standard library `sqlite3` module
- No ORM until a spec justifies one

## Layout

```
backend/
  app/
    ingestion/           multi-platform source ingestion (spec SPEC-ING-001)
      registry.py         source registry loading/validation
      adapters/           platform adapters (base interface + Instagram)
      storage/            raw store, normalizer, checkpoints, error log, manifests
      runner.py           platform-agnostic extraction loop
      cli.py              command implementations (used via scripts/ingest.py)
    main.py              FastAPI entry point       (not yet built)
    routers/             one module per feature area (not yet built)
    services/            business logic             (not yet built)
    repositories/        all SQL lives here         (not yet built)
    models/              request/response schemas    (not yet built)
```

Operate the ingestion subsystem from the project folder:

```
python scripts/ingest.py extract [--source IG001 | --url <profile-url>]
python scripts/ingest.py resume  [--source IG001]
python scripts/ingest.py status   [IG001]
python scripts/ingest.py add --url <profile-url>
```

## Rules

- Nothing is written here beyond `app/ingestion/` until the matching spec in
  `specs/features/` or `specs/api/` is marked `APPROVED`.
- SQL statements live only in `repositories/`. Parameterised queries only — never
  build SQL by string formatting.
- The server binds to `127.0.0.1` only. This is a single-user local system with no
  authentication; exposing it on a network interface would publish an unauthenticated
  API. If multi-user access is ever wanted, authentication must be specified and
  built first.
- Secrets are read from environment variables only. No key ever appears in a
  source file.
- Ingestion respects platform access controls: a refusal is recorded
  (`blocked` checkpoint + error log), never bypassed (decision `D-0013`).
