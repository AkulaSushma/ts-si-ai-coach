# config/ — Configuration (never secrets)

## Files

| File                 | Purpose                                                        |
| -------------------- | -------------------------------------------------------------- |
| `model_routing.json` | Which model fills which agent role, plus fallback order          |

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
