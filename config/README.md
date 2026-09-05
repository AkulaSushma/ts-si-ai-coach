# config/ — Configuration (never secrets)

## Files

| File                 | Purpose                                                        |
| -------------------- | -------------------------------------------------------------- |
| `model_routing.json` | Which model fills which agent role, plus fallback order          |
| `source_registry.json` | Ingestion sources: platform, username, URL, enabled, max_items |

`.env.example` at the project root documents the environment variables the project
expects. Copy it to `.env` and put your real keys there. `.env` is excluded from Git.

## The one rule that matters

**No API key, token, or password is ever written into a file in this folder, or any
other tracked file.** Secrets come from environment variables at runtime.
`config/model_routing.json` names providers; it never contains credentials.

If a key is ever committed by accident, treat it as public: revoke and reissue it.
Removing it from a later commit does not remove it from Git history.

## Changing model routing

Edit `model_routing.json` and nothing else. The role→model mapping is configuration
precisely so that swapping providers never requires touching code.

The verifier of a claim must be a **different provider** from its author. Any routing
change that puts the same provider in both an authoring role and its matching
verification role will be rejected by `scripts/validate_bootstrap.py`.

## Changing the source registry

`source_registry.json` lists every ingestion source (Instagram profiles today,
other platforms later). Each entry carries `source_id`, `platform`, `username`,
`profile_url`, `enabled`, and `max_items` (1–299; the 299 hard cap is enforced by
code, not convention). `defaults` supplies values an entry omits.

To add a source you may either edit the JSON or run:

```
python scripts/ingest.py add --url https://www.instagram.com/<name>/
```

The next `extract` run picks it up — no code change. Duplicate usernames and
`max_items` above 299 are rejected at load time. Loading it requires no network
access, so `python scripts/ingest.py status` is always safe to run.
