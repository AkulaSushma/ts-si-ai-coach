# scripts/ — Operational scripts

Small, single-purpose, standard-library-only Python scripts you can run directly.

## Available now

| Script                  | What it does                                                                |
| ----------------------- | --------------------------------------------------------------------------- |
| `validate_bootstrap.py` | Checks the repository structure, governance files, and configuration are intact |
| `ingest.py`             | Operates the ingestion subsystem (extract / resume / status / add sources)   |

Run them from the project folder:

```
python scripts/validate_bootstrap.py
```

It prints one line per check and exits with code `0` if everything passed, `1` if
anything failed. Run it any time you want to confirm nothing has been knocked out of
place.

```
python scripts/ingest.py extract                  # all enabled sources
python scripts/ingest.py extract --source IG001   # one registered source
python scripts/ingest.py extract --url https://www.instagram.com/<name>/
python scripts/ingest.py resume [--source IG001]  # resume interrupted runs
python scripts/ingest.py status [IG001]           # registry + checkpoints
python scripts/ingest.py add --url https://www.instagram.com/<name>/
```

`status` makes no network requests and is safe any time. Extraction visits only
sources registered in `config/source_registry.json`, caps every profile at its
`max_items` (299 by default), and records platform refusals instead of
bypassing them. See `specs/features/ingestion-subsystem.md` for the contract.

## Rules

- Scripts must be safe to run twice. No script deletes or overwrites project data
  without an explicit `--force` flag.
- No third-party dependencies unless a spec justifies them. Standard library first.
- A script that mutates anything under `source_material/` must refuse to run. Raw
  sources are read-only.
