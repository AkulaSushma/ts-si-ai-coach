# database/ — Schema definition and migrations (no schema applied yet)

Status: **no schema exists yet.** The data-model spec must be written and approved
first — see `specs/data-model/`.

## Subfolders

| Folder        | Contents                                                              |
| ------------- | --------------------------------------------------------------------- |
| `migrations/` | Numbered, forward-only SQL migrations: `0001_description.sql`          |
| `seeds/`      | Reference data required for the system to function                     |

## Engine

SQLite (decision `D-0002`). The live database file is created at
`data/si_coach.db`, which is **excluded from Git** — a database is generated state,
not source. What is version-controlled is the migrations that build it.

## Rules

- Migrations are forward-only and never edited after being applied. To change
  something, add a new migration.
- Every migration is reversible in principle: state in a header comment what it does
  and what would be lost by reverting.
- Every user-visible text column gets a `_te` Telugu companion column at creation
  time, nullable. This is decision `D-0004` and exists so Telugu support later needs
  no migration of existing rows.
- Seeds may contain only `T1_OFFICIAL` or `T2_HISTORICAL_PYQ` material with source
  IDs. Never seed the database with AI-generated exam facts.
- **Back up `data/si_coach.db` by copying the file.** Git does not protect it.
