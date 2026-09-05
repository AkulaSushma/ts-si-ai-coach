# Ingestion subsystem — multi-platform source ingestion

| Field       | Value                                             |
| ----------- | ------------------------------------------------- |
| ID          | `SPEC-ING-001`                                    |
| Status      | `APPROVED`                                        |
| Approved by | User instruction, session 002 (2026-09-05)       |
| Implements  | Instagram adapter; architecture for future adapters |

## 1. Purpose

A reusable ingestion subsystem inside the existing SI & Constable project that
visits configured source profiles (Instagram first), extracts publicly accessible
content into a durable raw layer, and hands normalized records to later
pipeline stages (OCR, AI classification, verification) — **without** any raw
content reaching the trusted knowledge base.

The subsystem is **not** a new project. It lives in `backend/app/ingestion/`
and is operated through `scripts/ingest.py`.

## 2. Requirements source

The user's task instruction for session 002 is the requirements document. Its
non-negotiables, restated here so the spec stands alone:

1. Maximum **299 content items per profile** — posts, carousels, and reels all
   count against the same 299 budget (never 299 + 299). Default 299,
   configurable per source in the registry, hard-capped at 299.
2. Registry-driven: a new Instagram profile URL is added to
   `config/source_registry.json` and processed with **no code change**.
3. Separate collection from intelligence: nothing is discarded as "irrelevant"
   during crawling.
4. Raw record preserved as extracted; unavailable fields are `null`, never
   invented.
5. Mandatory checkpointing and resumable, idempotent extraction.
6. Per-item and per-profile failure isolation, with retries and error records.
7. Deduplication by stable content identifier plus content hashing.
8. Layer separation: registry / raw / normalized / candidate knowledge /
   verified knowledge / questions / provenance.
9. Platform access controls respected: no aggressive requesting, no bypass of
   authentication or rate limits. Blocked access is recorded honestly, not
   worked around.
10. Design for future adapters (YouTube, Telegram, websites, PDFs) through a
    common interface; do not implement them now.

## 3. Pipeline position

```
source registry ─→ adapter (platform-specific) ─→ raw store        (this build)
                                                        │
                                                        ▼
                                              normalized store     (this build)
                                                        │
                                                        ▼
                                    OCR / transcription               (later stage)
                                                        │
                                                        ▼
                                    AI relevance + knowledge          (later GLM stage)
                                                        │
                                                        ▼
                                    classification / dedup            (later)
                                                        │
                                                        ▼
                                    verification ─→ knowledge/       (existing policy)
```

This build implements everything down to the normalized store. The normalized
record carries scaffolded `ai_processing` fields (all `null`) so the later GLM
stage can fill them; nothing in this build fabricates values.

## 4. Component design

### 4.1 Source registry — `config/source_registry.json`

```json
{
  "version": 1,
  "defaults": { "max_items": 299, "polite_delay_seconds": 2.5, "max_retries": 3 },
  "sources": [
    {
      "source_id": "IG001",
      "platform": "instagram",
      "username": "example",
      "profile_url": "https://www.instagram.com/example/",
      "enabled": true,
      "max_items": 299,
      "added_at": "2026-09-05"
    }
  ]
}
```

Rules enforced by the loader (and tested):

- `source_id` unique, `^[A-Z]{2}[0-9]{3,}$`-shaped for Instagram (`IG###`).
- `profile_url` is a valid Instagram **profile** URL (username path only, no
  `/p/`, `/reel/`, `/explore/`, query tolerated and canonicalized away).
- Username matches Instagram's rules: 1–30 chars, `[A-Za-z0-9._]`, no leading
  or trailing dot/underscore. Usernames are stored lowercase.
- `max_items` is an integer in `[1, 299]`. Anything above 299 is rejected at
  load time — the cap is a mechanical rule, not a convention.
- Duplicate usernames across entries are rejected (the original source list
  contained `sudheergenzacademy` twice; it is stored once).
- Registry may list more platforms later; `platform` selects the adapter.

### 4.2 Common adapter interface — `backend/app/ingestion/adapters/base.py`

```python
class SourceAdapter(abc.ABC):
    platform: str
    def fetch_profile(self, username: str) -> ProfileSnapshot
    def fetch_page(self, edge: str, user_id: str, cursor: str | None) -> EdgePage
```

- `ProfileSnapshot` carries neutral, platform-independent fields plus the
  original platform JSON under `raw` (the raw record is never discarded).
- `EdgePage` carries `items` (parsed neutral stubs), `has_next`, `end_cursor`.
- Adapters raise `AccessBlockedError` when the platform refuses anonymous
  access; the runner records that honestly and stops that source.

### 4.3 Instagram adapter — `adapters/instagram.py`

- Primary access: `GET https://www.instagram.com/api/v1/users/web_profile_info/?username=<u>`
  with a browser `User-Agent` and the web app id header. This is the endpoint
  the public profile page itself uses; it is used exactly as a browser would.
- Fallback: the profile HTML page, scanned for embedded timeline JSON.
- Pagination: `GET https://www.instagram.com/api/v1/feed/user/<user_id>/?max_id=<cursor>`.
- One request at a time, `polite_delay_seconds` (+ jitter) between requests,
  at most `max_retries` attempts with exponential backoff, and **stop on any
  authentication/rate-limit signal** (401/403/429/login redirect → blocked).
- Content types: `GraphImage`→`post`, `GraphSidecar`→`carousel`,
  `GraphVideo`→`reel`; `XDT*` variants map the same way; unknown typenames are
  preserved and typed `unclassified` (never guessed).
- Media: URLs and per-slide ordering are preserved; binaries are **not**
  downloaded in this build (OCR is a later stage that will fetch on demand).
  `accessibility_caption`, where Instagram provides it, is retained verbatim.

### 4.4 Raw store — `data/raw/instagram/` (git-ignored, decision D-0008)

- `data/raw/instagram/<source_id>/_profile.json` — profile snapshot as fetched.
- `data/raw/instagram/<source_id>/<content_id>.json` — one item per file,
  written atomically (temp file + replace), never rewritten once written
  (idempotency). The item's `platform_data` block preserves the original
  per-item platform JSON.

Canonical raw record schema (unavailable → `null`, never invented):

```json
{
  "source_id": "IG001",
  "platform": "instagram",
  "profile_username": "example",
  "content_id": "<platform media id>",
  "shortcode": "ABcdEfGhIjK",
  "content_url": "https://www.instagram.com/p/<shortcode>/",
  "content_type": "post|carousel|reel|unclassified",
  "published_at": "ISO-8601 or null",
  "caption": "full caption or null",
  "hashtags": [],
  "media": {
    "images": [{"index": 0, "url": "...", "accessibility_caption": "…|null"}],
    "video": {"url": "…|null", "thumbnail_url": "…|null"}
  },
  "slides": [{"index": 0, "image_url": "…", "accessibility_caption": null,
               "ocr_text": null}],
  "text": {
    "caption_text": "…|null",
    "ocr_text": null,
    "transcript": null,
    "on_screen_text": null
  },
  "engagement": {"likes": null, "comments": null},
  "platform_data": { "original item JSON, preserved" },
  "extraction": {"status": "raw", "extracted_at": "ISO-8601"}
}
```

`slides` preserves carousel order; `text.ocr_text` / `transcript` /
`on_screen_text` stay `null` until the OCR/transcription stage exists — the
pipeline order in §3 puts OCR *after* raw storage, so this is correct, not a
gap. Per-slide `ocr_text` placeholders exist so the OCR stage can fill them
without schema changes, and the original OCR output is never overwritten
(OCR stage writes `ocr_text_raw` alongside).

### 4.5 Normalized store — `data/normalized/instagram/` (derived, git-ignored)

`normalize.py` derives, per item: combined `normalized_text` (caption + slide
text when OCR later fills it), deduplicated lowercase hashtags, ISO dates, and
adds the mandatory blocks:

- `provenance`: `source_id`, `profile_username`, `content_id`, `original_url`,
  `content_type`, `published_at`, `extracted_at`, `provenance_tier`
  (`T3_EXPERT` for these Instagram coaching sources).
- `ai_processing` scaffold — every field `null` / empty until the GLM stage:

```json
"ai_processing": {
  "status": "not_processed",
  "subject": null, "knowledge_type": null,
  "si_relevance": null, "constable_relevance": null, "telangana_relevance": null,
  "pyq_similarity": null, "revision_priority": null,
  "confidence": null, "verification_status": null, "processed_at": null
}
```

Allowed values are fixed in `taxonomy.py` (subjects: Indian History,
Telangana History, Indian Polity, Constitution, Geography, Telangana
Geography, Economy, General Science, Current Affairs, Telangana GK,
Arithmetic, Reasoning, English, Telugu, Other SI/Constable subjects;
knowledge types: FACT, CONCEPT, DEFINITION, DATE, PERSON, PLACE, LAW, ARTICLE,
AMENDMENT, FORMULA, SHORTCUT, MCQ, QUESTION, CURRENT_AFFAIRS, EXPLANATION,
OTHER). The schema forbids values outside these enums — a later stage cannot
quietly invent a category.

### 4.6 Checkpoints — `data/ingestion/checkpoints/<source_id>.json`

```json
{
  "source_id": "IG001",
  "platform": "instagram",
  "status": "not_started|in_progress|partial|complete|blocked",
  "stop_reason": null,
  "max_items": 299,
  "profile": {"user_id": null, "declared_timeline_count": null,
               "declared_reels_count": null, "is_private": null,
               "fetched_at": null},
  "items": {"discovered": 0, "extracted": 0, "duplicate": 0,
            "failed": 0, "inaccessible": 0},
  "dispositions": {"processed_ids": [], "duplicate_ids": [],
                   "failed_ids": [], "failure_detail": {}},
  "cursors": {"timeline": {"end_cursor": null, "blocked": false},
              "reels": {"end_cursor": null, "blocked": false}},
  "resume_state": null,
  "started_at": null, "updated_at": null, "finished_at": null
}
```

Semantics (each unique content item has exactly one disposition):

- `discovered` = unique items seen; `extracted` = stored; `duplicate` =
  re-appearances across edges (timeline ∩ reels) or re-listings; `failed` =
  errored and not stored; `inaccessible` = within the expected target but not
  reachable (blocked pagination, private profile).
- `expected = min(max_items, declared_total)` when the profile declares a
  total, else `discovered`. The accounting identity
  `expected = extracted + duplicate + failed + inaccessible` (irrelevant is 0
  at collection by §2.3) must hold at every manifest write.
- Resume: already-dispositioned items are skipped (no re-fetch of stored
  items, no double counting); failed items are retried up to `max_retries`;
  blocked pagination is re-attempted only on an explicit `resume` invocation.
- Checkpoints are written atomically after every item and after every page, so
  a crash mid-profile loses at most the in-flight item.

### 4.7 Error log — `data/ingestion/errors/<source_id>.jsonl`

One JSON line per failure event: `source_id`, `content_url`, `error_type`,
`message`, `timestamp`, `retry_count`, `status`. Appended, never rewritten.

### 4.8 Harvest manifests — `research/manifests/instagram/`

Per run, `<source_id>-<timestamp>.json`, satisfying the research accounting
identity with a `expected_justification` field recording how the expected
count was obtained (profile-declared counts read on date X, or
items-actually-discovered when no declaration is accessible). These are the
L3 accounting artifacts `research/README.md` requires, and they are tracked in
Git because they are small, reviewable evidence.

### 4.9 Runner — `runner.py`

Platform-agnostic loop: for each source, fetch profile → walk edges
(`timeline`, then `reels`) → per item: skip / store / record failure → stop at
`max_items` → write manifest. A per-item exception records an error and
continues the profile; a per-profile exception records the source as
`blocked`/`partial` and continues the batch. Never restarts completed work:
sources whose checkpoint says `complete` are skipped unless forced.

### 4.10 CLI — `backend/app/ingestion/cli.py` via `scripts/ingest.py`

```
python scripts/ingest.py extract                    # all enabled Instagram sources
python scripts/ingest.py extract --source IG001     # one source by id
python scripts/ingest.py extract --url https://www.instagram.com/example/   # direct URL
python scripts/ingest.py resume [--source IG001]    # resume interrupted extraction
python scripts/ingest.py status [IG001]            # registry + checkpoint summary
python scripts/ingest.py add --url https://www.instagram.com/example/       # register new source
```

`extract --url` runs an ad-hoc extraction (hash-derived source id, not
registered). `add` writes the registry entry so the next `extract` includes
it — no code change. All commands are safe to run twice.

## 5. Conventions honoured

- Standard library only (`D-0006`): `urllib` for HTTP, `unittest` for tests,
  `sqlite3` not used at this stage (no database yet — the raw and normalized
  stores are files under `data/`, which is what `data/README.md` reserves for
  runtime data).
- Raw data is git-ignored (`D-0008`); manifests and registry are tracked.
- Raw Instagram content never enters `knowledge/`, `pyq/`, or any trusted
  store; provenance tier stays `T3_EXPERT`.
- Nothing under `source_material/` is touched.
- Status vocabulary is `COMPLETE` / `PARTIAL` / `BLOCKED` as everywhere else.

## 6. Acceptance criteria

1. Registry loads with 32 unique, valid Instagram entries; `sudheergenzacademy`
   stored once; every `max_items` ≤ 299.
2. URL validation accepts canonical profile URLs (incl. dotted usernames) and
   rejects non-profile, non-Instagram, malformed, and overlong usernames.
3. A 350-item fake profile extracts exactly 299 items, not one more; a
   combined timeline+reels profile with no overlap extracts 299 total, never
   299 + 299.
4. The same shortcode in two edges is stored once and counted `duplicate`.
5. Re-running a completed source stores nothing new.
6. An interrupted run resumes: already-stored items are not re-fetched;
   final counts equal the uninterrupted run.
7. A failing item records an error with type/timestamp/retry count and the
   profile continues; a failing profile records its state and the batch
   continues.
8. Raw files persist with the schema in §4.4, `null` where inaccessible,
   slides in order.
9. A new URL added to the registry (via `add` or by editing the JSON) is
   extractable with no code change — demonstrated by test.
10. Every written manifest balances the accounting identity.
11. Live verification: extraction runs against exactly one configured source
    and the real outcome — items discovered/extracted/failed and checkpoint
    state — is reported verbatim, whatever it is, including "blocked by
    platform access control".

Bulk extraction of all sources is explicitly out of scope until criterion 11
is reviewed.
