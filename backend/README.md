# backend/ — Python application (not yet built)

Status: **empty by design.** Bootstrap deliberately installed no frameworks.

## Planned stack (decision D-0002 in `DECISIONS.md`)

- Python 3.10+
- FastAPI for the HTTP layer
- SQLite via the standard library `sqlite3` module
- No ORM until a spec justifies one

## Layout when work begins

```
backend/
  app/
    main.py          FastAPI entry point
    routers/         one module per feature area
    services/        business logic, no HTTP concerns
    repositories/    all SQL lives here and nowhere else
    models/          request/response schemas
```

## Rules

- Nothing is written here until the matching spec in `specs/features/` or
  `specs/api/` is marked `APPROVED`.
- SQL statements live only in `repositories/`. Parameterised queries only — never
  build SQL by string formatting.
- The server binds to `127.0.0.1` only. This is a single-user local system with no
  authentication; exposing it on a network interface would publish an unauthenticated
  API. If multi-user access is ever wanted, authentication must be specified and
  built first.
- Secrets are read from environment variables only. No key ever appears in a source
  file.
