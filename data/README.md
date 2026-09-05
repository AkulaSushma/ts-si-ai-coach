# data/ — Local runtime data (excluded from Git)

Everything in this folder except this README is ignored by Git. That is deliberate:
the database is *generated* from `database/migrations/`, so the migrations are the
source of truth and the database file is a build product.

## What will live here

| Path                | Contents                                       |
| ------------------- | ---------------------------------------------- |
| `si_coach.db`       | The SQLite database (not created yet)           |
| `exports/`          | Generated reports and exports                   |
| `cache/`            | Temporary caches, safe to delete at any time    |

## Backup warning — read this

Git will **not** protect your study history. Your practice attempts, timings, error
analysis, and revision schedule will live in `si_coach.db`, and Git ignores it.

To back it up, close the application and copy `data/si_coach.db` somewhere else. A
copy on the same drive is not a backup.

This is the single most likely way to lose real work on this project, which is why it
is written here in the folder itself rather than only in the documentation.
