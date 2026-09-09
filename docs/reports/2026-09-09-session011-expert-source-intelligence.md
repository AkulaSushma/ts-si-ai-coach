# Session 011 — Expert-source intelligence checkpoint

Status: **PARTIAL**
Base checkpoint: `b8facd44483937e14a1e031ed244e4c7704a80a2`
Spec: SPEC-INT-011 (`specs/features/session011-expert-source-intelligence.md`)

## 1. Actual repository state (observed, not reported)

- Branch `main`, base HEAD `b8facd44483937e14a1e031ed244e4c7704a80a2`, unprotected.
- Media collection `SI & Constable Concepts Videos & photos`: **62 files,
  539,873,070 bytes**, 37 `.mp4` and 25 `.jpg`, machine-counted from the
  committed tree. All 62 blob SHA-1 values are distinct; semantic duplication was
  not assessed.
- Root ledgers (`PROJECT_STATE.md`, `TASK_LEDGER.md`, `SOURCE_LEDGER.md`,
  `KNOWLEDGE_LEDGER.md`) remain **stale** with respect to Sessions 010 and 011 and
  were deliberately not rewritten.

## 2. Actual media-processing state

- Real images decoded and processed through the intake path: **2**
  (`IMG_20260906_192918.jpg` in Session 010,
  `Screenshot_2026-09-01-19-57-10-82_...jpg` in this session).
- Real videos processed: **0**. No video bytes were opened, decoded, sampled or
  transcribed. No synthetic substitute was used.
- Remaining 60 assets: `processing_state: NOT_STARTED` in the asset plan.

## 3. Integrity status

- The unsafe promoter `outputs/verify_fast_methods.py` remains retired (refuses to
  run, changes nothing). Its original source is preserved in Git history.
- A **second** unsafe mutator was found at the base checkpoint,
  `outputs/correct_fast_method_assignments.py`, which rewrote
  `pyq/intelligence/questions.json` in place from a hardcoded mapping with no
  evidence gate and no history retention. It is now retired the same way. **No
  historical intelligence record was modified.**
- Stored legacy `VERIFIED` / `VERIFIED_FAST_METHOD` labels in
  `verification/` and `pyq/intelligence/` were produced by the defective
  mechanism and are **not** trusted or re-verified by this checkpoint.

## 4. Architectural decisions

1. Identity precedes intelligence: every asset is bound to its committed Git blob
   SHA-1 plus a content SHA-256 before anything is derived from it.
2. Evidence is located: `image_region` (validated against real pixel dimensions)
   or `video_interval` (validated against probed duration).
3. Derivatives are evidence: extracted frames are hashed and journalled per
   (asset, timestamp, engine, processor version), and reused only if the artifact
   still hashes identically.
4. Fail closed: missing OCR/ASR yields a `BLOCKED` attempt with `output: null`,
   which can never become a span, a candidate or a verified claim.
5. Origin separation: `SOURCE_DERIVED` must preserve exact extracted wording;
   paraphrase is `MODEL_DERIVED`; independent recomputation is a third category.
6. Dimensions stay independent; `VERIFIED_FAST_METHOD` requires correctness AND
   applicability AND speed, each separately evidenced.
7. Revision-bound history: a corrected method statement is a new revision; the
   earlier revision keeps its FAIL forever.

## 5. Changes actually implemented

- `scripts/video_intake.py` — video-capable intake (identity, probe, hashed
  frames, blocked extraction slots, sampling policy).
- `scripts/build_asset_plan.py` + `data/expert_media/asset_plan.jsonl` — durable
  inventory of all 62 assets, identity/size/class only.
- `scripts/reasoning_verify.py` — deterministic independent recomputation,
  applicability boundary detection, rule-underdetermination counting.
- `scripts/run_reasoning_pilot.py` — bounded real-image pilot.
- `outputs/correct_fast_method_assignments.py` — retired, non-mutating.
- `tests/test_session010_video_path.py` (15 tests),
  `tests/test_session011_reasoning.py` (11 tests).
- SPEC-INT-011 and this report.

## 6. Real assets actually processed this session

`SI & Constable Concepts Videos & photos/Screenshot_2026-09-01-19-57-10-82_1c337646f29875672b5a61192b9010f9.jpg`

- 324,098 bytes; Git blob `5b4835709335954246a0bf603da4b7eb4b3c394b`
- SHA-256 `9aa1e4e9bf39af36cde3bb24623beaf4591ea303dbf1079693936caf618605ad`
- probed dimensions 1080 × 2414 (mjpeg), evidence region `[0, 0, 1080, 2414]`

## 7. Evidence actually extracted

Visible text read from the decoded image, recorded verbatim as the source span:

```
Reasoning Trick
86 : 288 :: 36 : ? 108
(a) 95
(b) 108
(c) 172
(d) 102
8x6=48
48x6 = 288
3x6=18
18x6 = 108
```

Also visible: a phone status-bar time and a comment bar, indicating a screenshot
of a social video frame. **Publisher, account, upload date, audio and any spoken
explanation were not observed and are recorded as unobserved.**

## 8. Source-derived versus model-derived

- SOURCE_DERIVED (T3_EXPERT, UNVERIFIED): the verbatim text above.
- MODEL_DERIVED (T4_AI, UNVERIFIED): the rule statement “multiply the digits of
  the term together, then multiply by 6”, the recognition cue, and the caution
  that a single shown pair does not determine a unique rule.
- INDEPENDENTLY DERIVED: the recomputation in `scripts/reasoning_verify.py`
  (86 → 48 → 288; 36 → 18 → 108; zero-digit inputs degenerate to 0).

## 9. Verification results

- First pilot run recorded **FAIL** for correctness because the initial model
  rule statement applied the factor twice (86 → 1728 ≠ 288). That FAIL is
  retained and still blocks that revision — a real fail-closed demonstration.
- After the rule statement was corrected (a **new** subject revision), correctness
  was assessed **PASS** by deterministic recomputation with two valid cases and
  one boundary case.
- `fast_method_state` = **UNVERIFIED_FAST_METHOD**. Applicability, speed,
  recognition and retention have no evidence. `pyq_links` = `[]`.
- Verified knowledge promoted to trusted stores: **0**.

## 10. Tests actually executed

`python3 -m unittest discover -s tests -v` over the staged Session 010/011 test
modules: **46 tests, OK, 1.277s** (20 integrity + 15 video path + 11 reasoning).
The full pre-existing repository suite and `scripts/validate_bootstrap.py` were
**not** run in this environment.

## 11. Unresolved uncertainty

- Legacy `VERIFIED` labels: untrusted, not re-verified.
- Five unresolved PYQ classifications remain unresolved.
- Base-checkpoint contradictions (five VERIFIED fast labels versus the reported
  “four verified plus one failed”, stale ledgers, schema/type mismatches) are
  retained without silent repair.
- Video path correctness is demonstrated only against a locally generated ffmpeg
  **test fixture**, not against any asset in this collection.
- Journal durability under Windows, hardlink-less filesystems and concurrency is
  unvalidated.

## 12. Blocked capabilities

- **Real video bytes are unobtainable from this environment.** Repository file
  reads fail for blobs larger than about 1 MB with
  `unsupported content encoding: none, this may occur when file size > 1 MB`, and
  no raw-blob download tool is exposed. The smallest video is 2,347,758 bytes, so
  **all 37 videos are unreachable here**. The supported solution is to run
  `scripts/video_intake.py` in the local checkout, where the real bytes and
  ffmpeg/ffprobe are both available.
- No OCR engine, no ASR engine, no Telugu transcription.
- No speed measurement harness, no PYQ-relationship evidence, no near-duplicate
  detection, no bulk queue.

## 13. Exact Git commit

See the commit that adds this file; the preceding code commit is
`7fd3679ac3d7f0a2ab54865c615853956b47cc40`.

## 14. What should happen next

1. In the local checkout, run `scripts/video_intake.py` against one video
   (suggested: `Dynasties & Founders (Tricks).mp4`, 2,347,758 bytes, blob
   `5766d657…`) and commit the resulting probe/frame attempt records.
2. Add a real OCR adapter for the sampled frames, then a Telugu-capable ASR
   adapter; keep both fail-closed.
3. Build the speed-evidence harness (operation counting plus timed solving) so
   speed can ever be assessed independently of correctness.
4. Only then propose PYQ relationships, each requiring its own evidence.
5. Add a resumable work queue with leases before scaling past a handful of assets.
6. Reconcile the stale root ledgers honestly, recording contradictions rather
   than overwriting them.

This checkpoint is **PARTIAL**: capability and evidence advanced, but no video was
processed and no verified fast method exists.
