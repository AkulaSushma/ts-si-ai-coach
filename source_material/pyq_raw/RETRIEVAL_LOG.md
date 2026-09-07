# PYQ retrieval log — verbatim attempts and responses

Every attempt to fetch a previous-year paper source, recorded verbatim. Per `D-0017`,
a refusal is quoted exactly and is never routed around. There is no alternative
transport attempted: no `curl`, `wget`, `lynx`, no Python HTTP client, no other
language, no cached, archived or mirrored copy.

## Session 007 — 2026-09-07

Attempted to locate and then fetch previous-year Telangana Police SI / Constable
papers. The environment's web search returned no content, and direct fetch was refused
at the host level.

### Attempt 1
- **Tool:** workspace web_fetch
- **URL:** `https://www.google.com/search?q=Telangana+Police+SI+previous+year+question+paper`
- **Response (verbatim):**
  ```
  Host "www.google.com" is not on the network allowlist (cowork-egress-blocked). Ask your administrator to add this domain to the Cowork egress allowlist (coworkEgressAllowedHosts). Allowed: api.lumosel.vip
  ```
- **Note:** Host-level refusal. It applies to every path on any host outside the
  allowlist, so no individual paper URL can be tried separately with a different result.

### Attempt 2
- **Tool:** workspace web_fetch
- **URL:** `https://www.tgprb.in/`
- **Response (verbatim):**
  ```
  Host "www.tgprb.in" is not on the network allowlist (cowork-egress-blocked). Ask your administrator to add this domain to the Cowork egress allowlist (coworkEgressAllowedHosts). Allowed: api.lumosel.vip
  ```
- **Note:** The board's own domain is likewise blocked, so no official paper source can
  be reached from here (`D-0015`).

### Attempt 3
- **Tool:** web_search
- **URL (query):** `Telangana Police SI previous year question papers download`
- **Response:** Web search returned no result content in this environment.
- **Note:** Recorded as an environment capability observation, not as a negative
  finding about whether the papers exist.

## Implications

No paper, question, or verified source URL has been acquired. The PYQ phase is
`BLOCKED` on acquisition (`B-02`), with the exact refusal above. The registries under
`config/` and `pyq/` are built and ready; unblocking is a network change
(`coworkEgressAllowedHosts`) or a manual download of paper files into this folder.
