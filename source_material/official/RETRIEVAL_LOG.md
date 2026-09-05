# source_material/official/ — Retrieval log

Append-only, verbatim record of every attempt to obtain an official TGPRB / TSLPRB
document. Its purpose is that a future session can tell the difference between
"never tried", "tried and refused", and "obtained", without re-deriving anything.

Nothing in this folder yet holds an official document. That is a recorded state, not
an omission: see the attempts below.

## Session 003 — 2026-09-06 (timestamps in UTC; 2026-09-05T18:52Z is 2026-09-06 00:22 IST)

Target: the Telangana Police SI 2026 notification and any addenda, per
`config/official_documents.json` (`DOC-OFF-001` … `DOC-OFF-006`).

### Attempt 1 — official site root

- **URL:** `https://tgprb.in/`
- **Tool:** workspace web fetch
- **Timestamp:** 2026-09-05T18:52:00Z
- **Result:** refused before any request reached the network
- **Verbatim response:**

```
Host "tgprb.in" is not on the network allowlist (cowork-egress-blocked). Ask your
administrator to add this domain to the Cowork egress allowlist
(coworkEgressAllowedHosts). Allowed: tabitoken.com
```

### Attempt 2 — official downloads path

- **URL:** `https://www.tgprb.in/downloads.html`
- **Tool:** workspace web fetch
- **Timestamp:** 2026-09-05T19:02:00Z
- **Verbatim response:**

```
Host "www.tgprb.in" is not on the network allowlist (cowork-egress-blocked). Ask your
administrator to add this domain to the Cowork egress allowlist
(coworkEgressAllowedHosts). Allowed: tabitoken.com
```

### Attempt 3 — a notification PDF whose URL was observed on the official domain

- **URL:** `https://www.tgprb.in/SI_PC_2026/PC%20(Civil%20et%20al)%202026%20Notification%20dated%2029-07-2026.pdf`
- **Tool:** workspace web fetch
- **Timestamp:** 2026-09-05T19:02:00Z
- **Verbatim response:** identical host-level refusal as attempts 1 and 2.

## What the refusal means

The allowlist names exactly one permitted host, `tabitoken.com`, which has nothing to
do with this project. The refusal is therefore **host-level and environment-wide**: it
is not rate limiting, not a login wall, not a site outage, and not something a
different path, header, or retry would change. Requesting each remaining URL
individually would produce the same sentence six times and add no information, so the
registry records the refusal once per document and cites the attempt that established
it.

## What was deliberately not done

- **No alternative fetch route.** No `curl`, `wget`, Python `requests`, proxy, mirror,
  cache, or archive service was used after the fetch tool reported the block. The
  restriction is a rule about this environment, not an obstacle to route around.
- **No coaching-site substitution.** Search results contained mirrors of official PDFs
  hosted by exam-coaching sites, and articles stating vacancy counts, age limits,
  qualification and the selection sequence. None of it was recorded as an official
  fact. A mirror cannot be hashed against the publisher and an article is not the
  document; recording either as `T1_OFFICIAL` would be the exact relabelling that
  `CLAUDE.md` section 5 prohibits.
- **No reconstruction from model recall.** No syllabus item, mark, duration, age limit,
  vacancy count or physical standard has been written anywhere in this repository.

## Search use, and its limits

A web search restricted to the official domain was used **only to locate URLs**, which
is permitted by `SPEC-OFF-001` R3. Two useful outcomes: four candidate URLs on the
official domain were enumerated, and a possible official-domain conflict surfaced
(`CONF-OFF-001` — `tgprb.in` versus `tslprb.in`). Neither outcome is a fact about the
examination, and no snippet text was copied into any knowledge record.

## How to unblock

Any one of these turns this log's `BLOCKED` entries into retrievals:

1. Add `tgprb.in`, `www.tgprb.in` and `www.tslprb.in` to the environment's egress
   allowlist, then re-run the retrieval.
2. Download the notification PDFs manually and place them in this folder; the registry
   already holds the expected file identities, and hashing plus fact extraction can
   then proceed offline.
3. Run the retrieval from a network context where the official domain is reachable.

Options 2 and 3 need no code change. Option 1 is an environment setting outside this
repository's control.
