# SOURCE_LEDGER.md — Register of every source ever used

Append-only. Every externally acquired item gets an entry here **in the same session
it is acquired**. Material with no ledger entry is unusable by policy, because a claim
whose origin is unknown cannot be checked, corrected, or defended.

## Current state

**Entries: 32 registered Instagram sources (IG001–IG032); harvested items: 0
— no content has been obtained from any of them.** The registry lives in
`config/source_registry.json`; this ledger records each registered source and
every extraction attempt against it.

The single-source live verification run (IG001, 2026-09-05) was refused by
Instagram (HTTP 429, anonymous access). Its checkpoint, error log, and
manifest are the evidence; no content was obtained from any source yet. This
zero-harvest count is a real, verified state, not a placeholder.

## ID format

`SRC-####` — assigned sequentially, never reused, never renumbered.
Ingestion sources additionally carry the registry's platform-scoped id
(`IG001`…), which is what raw records and provenance cite.

## Required fields

| Field             | Meaning                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `id`              | `SRC-####`                                                          |
| `title`           | Human-readable name                                                 |
| `tier`            | `T1_OFFICIAL` / `T2_HISTORICAL_PYQ` / `T3_EXPERT` / `T4_AI`          |
| `origin`          | Full URL, or physical description for print material                |
| `publisher`       | TGPRB, channel name, author, institute                              |
| `acquired_on`     | ISO date the material was obtained                                  |
| `acquired_by`     | Session or run identifier                                           |
| `local_path`      | Path under `source_material/`, or `NOT_STORED` with the reason      |
| `checksum`        | SHA-256 of the stored file, or `N/A`                                |
| `language`        | `en` / `te` / `both`                                                |
| `access_status`   | `AVAILABLE` / `PAYWALLED` / `REMOVED` / `INACCESSIBLE`              |
| `reliability`     | `AUTHORITATIVE` / `GENERALLY_RELIABLE` / `UNKNOWN` / `UNRELIABLE`   |
| `notes`           | Known errors, caveats, corrigenda affecting this source             |

## Rules

- Record the URL even when the file is not stored locally. A dead link with a date is
  still better provenance than nothing.
- Never upgrade `tier` because a source seems trustworthy. Tier describes *what kind of
  source it is*, not how much it is liked.
- When a source is later found to contain an error, do not delete the entry. Add the
  error to `notes` and re-check every knowledge record citing it.
- Store a checksum for anything stored locally, so silent corruption or replacement is
  detectable.

## Entries

_Session 002: the 32 Instagram sources below were **registered** (directed for
extraction, `max_items` 299 each). Registration is not acquisition — no content
has been obtained from any of them yet. The first extraction attempt (IG001)
was refused by the platform; see `notes`._

| id | title | tier | origin | publisher | acquired_on | access_status | reliability |
| -- | ----- | ---- | ------ | --------- | ----------- | ------------- | ----------- |
| SRC-0001 | Instagram: venkis_alphanumerics (IG001) | `T3_EXPERT` | https://www.instagram.com/venkis_alphanumerics/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (429, anonymous) | `UNKNOWN` |
| SRC-0002 | Instagram: amruthasacademy (IG002) | `T3_EXPERT` | https://www.instagram.com/amruthasacademy/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed, same refusal) | `UNKNOWN` |
| SRC-0003 | Instagram: mallamcreations (IG003) | `T3_EXPERT` | https://www.instagram.com/mallamcreations/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0004 | Instagram: mindsign_learners (IG004) | `T3_EXPERT` | https://www.instagram.com/mindsign_learners/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0005 | Instagram: knowledge_is_divine01 (IG005) | `T3_EXPERT` | https://www.instagram.com/knowledge_is_divine01/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0006 | Instagram: upttake_jobs (IG006) | `T3_EXPERT` | https://www.instagram.com/upttake_jobs/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0007 | Instagram: theknowledgeboard (IG007) | `T3_EXPERT` | https://www.instagram.com/theknowledgeboard/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0008 | Instagram: scoreup_careers (IG008) | `T3_EXPERT` | https://www.instagram.com/scoreup_careers/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0009 | Instagram: govtjobswale_notes (IG009) | `T3_EXPERT` | https://www.instagram.com/govtjobswale_notes/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0010 | Instagram: reviseinseconds (IG010) | `T3_EXPERT` | https://www.instagram.com/reviseinseconds/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0011 | Instagram: bhagyanagarbip (IG011) | `T3_EXPERT` | https://www.instagram.com/bhagyanagarbip/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0012 | Instagram: onset_exam_app (IG012) | `T3_EXPERT` | https://www.instagram.com/onset_exam_app/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0013 | Instagram: sscstudydiary (IG013) | `T3_EXPERT` | https://www.instagram.com/sscstudydiary/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0014 | Instagram: thekushwahasir (IG014) | `T3_EXPERT` | https://www.instagram.com/thekushwahasir/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0015 | Instagram: chandan_logics (IG015) | `T3_EXPERT` | https://www.instagram.com/chandan_logics/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0016 | Instagram: times_of_india_g.k (IG016) | `T3_EXPERT` | https://www.instagram.com/times_of_india_g.k/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0017 | Instagram: pi_academy_arni (IG017) | `T3_EXPERT` | https://www.instagram.com/pi_academy_arni/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0018 | Instagram: successpathtelugu (IG018) | `T3_EXPERT` | https://www.instagram.com/successpathtelugu/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0019 | Instagram: guinnessandmathguy (IG019) | `T3_EXPERT` | https://www.instagram.com/guinnessandmathguy/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0020 | Instagram: trickify_brains (IG020) | `T3_EXPERT` | https://www.instagram.com/trickify_brains/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0021 | Instagram: sudheergenzacademy (IG021) | `T3_EXPERT` | https://www.instagram.com/sudheergenzacademy/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0022 | Instagram: deepakk.maths (IG022) | `T3_EXPERT` | https://www.instagram.com/deepakk.maths/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0023 | Instagram: conhecimento.matematico2024 (IG023) | `T3_EXPERT` | https://www.instagram.com/conhecimentomatematico2024/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0024 | Instagram: ashusir_pw (IG024) | `T3_EXPERT` | https://www.instagram.com/ashusir_pw/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0025 | Instagram: ap_dsc_2027 (IG025) | `T3_EXPERT` | https://www.instagram.com/ap_dsc_2027/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0026 | Instagram: math_station_by_pj (IG026) | `T3_EXPERT` | https://www.instagram.com/math_station_by_pj/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0027 | Instagram: focus40_academy (IG027) | `T3_EXPERT` | https://www.instagram.com/focus40_academy/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0028 | Instagram: venkislogics (IG028) | `T3_EXPERT` | https://www.instagram.com/venkislogics/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0029 | Instagram: mathsbyrajat9196 (IG029) | `T3_EXPERT` | https://www.instagram.com/mathsbyrajat9196/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0030 | Instagram: gk_madhu_sir (IG030) | `T3_EXPERT` | https://www.instagram.com/gk_madhu_sir/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0031 | Instagram: bsk.social (IG031) | `T3_EXPERT` | https://www.instagram.com/bsk.social/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |
| SRC-0032 | Instagram: bikshuyadav_official (IG032) | `T3_EXPERT` | https://www.instagram.com/bikshuyadav_official/ | profile owner | 2026-09-05 (registered) | `INACCESSIBLE` (assumed) | `UNKNOWN` |

**Notes (2026-09-05, session 002):**

- The original user-supplied list contained `sudheergenzacademy` twice; it is
  registered once (IG021), per instruction.
- Only IG001 has had an extraction attempt. Instagram returned HTTP 429 for
  the anonymous web-profile API request, and the profile HTML page served to
  anonymous clients contains no post data (JavaScript shell only). No other
  source has been attempted, so their access status is an explicit assumption
  based on the same client being refused — it must be re-tested, not assumed,
  once an access path is chosen (`B-08`).
- `local_path`: `NOT_STORED` for all 32 — no content files obtained. Raw
  records, when extraction succeeds, will live under
  `data/raw/instagram/<IG-id>/` (git-ignored runtime data, per `D-0008`).
- `IG021`'s registration notes in `config/source_registry.json` record the
  duplicate-in-original-list fact.
