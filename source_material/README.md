# source_material/ — Raw acquired material (treat as read-only)

This folder holds material **exactly as acquired**. It is the evidence base for
every factual claim the system will ever make.

## Subfolders

| Folder     | Contents                                                                     | Provenance tier      |
| ---------- | ---------------------------------------------------------------------------- | -------------------- |
| `official/`| TGPRB notifications, official syllabus PDFs, official corrigenda             | `T1_OFFICIAL`        |
| `pyq_raw/` | Previous-year question papers and answer keys, as acquired                    | `T2_HISTORICAL_PYQ`  |
| `books/`   | Scans, extracts, and notes from published preparation books                   | `T3_EXPERT`          |
| `web/`     | Saved web pages and articles                                                  | `T3_EXPERT`          |
| `media/`   | YouTube / Instagram / Telegram captures and their transcripts                 | `T3_EXPERT`          |

## Rules

- **Never edit a file in this folder after it lands.** Corrections belong in
  `knowledge/`, never in the raw source. If a source is wrong, record that fact in
  `SOURCE_LEDGER.md`.
- Every item added here must get a `SOURCE_LEDGER.md` entry in the same session,
  with a stable source ID, the original URL or physical origin, and the acquisition
  date. Material with no ledger entry is unusable by policy.
- Never place API keys, personal data, or paid copyrighted material that you do not
  have the right to store here.
- Large binaries (video, full book scans) are intentionally excluded from Git by
  `.gitignore`. They live on disk only, so **back this folder up yourself** — Git
  will not do it for you.
