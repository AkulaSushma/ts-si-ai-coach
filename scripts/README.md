# scripts/ — Operational scripts

Small, single-purpose, standard-library-only Python scripts you can run directly.

## Available now

| Script                  | What it does                                                                |
| ----------------------- | --------------------------------------------------------------------------- |
| `validate_bootstrap.py` | Checks the repository structure, governance files, and configuration are intact |

Run it from the project folder:

```
python scripts/validate_bootstrap.py
```

It prints one line per check and exits with code `0` if everything passed, `1` if
anything failed. Run it any time you want to confirm nothing has been knocked out of
place.

## Rules

- Scripts must be safe to run twice. No script deletes or overwrites project data
  without an explicit `--force` flag.
- No third-party dependencies unless a spec justifies them. Standard library first.
- A script that mutates anything under `source_material/` must refuse to run. Raw
  sources are read-only.
