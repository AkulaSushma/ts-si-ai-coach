# Session 013 — Video intelligence path (status: PARTIAL)

Checkpoint at start: `25e49e9ed3fc3e8da07bdcce972abfcdcaf34bb9`, re-established from the
actual commit list rather than from a previous report.

## What was requested

Remove the largest remaining evidence bottleneck by establishing the first genuine
end-to-end video intelligence path, starting from the smallest suitable real video,
with fail-closed multilingual handling, resumable processing and no manufactured
teaching claims or PYQ links.

## Asset discovery (source-derived)

The media directory was listed from the repository at the current checkpoint. The
smallest video is real and its committed name matches the one suggested:

- `SI & Constable Concepts Videos & photos/Dynasties & Founders (Tricks).mp4`
- size 2,347,758 bytes, Git blob SHA-1 `5766d6575b6a54ab477d188558223f319b72f8dd`
- 37 videos and 25 images remain in the collection; nothing was modified.

## What was actually completed

`scripts/video_pipeline.py` (new) — resumable, fail-closed stage chain
`identity -> probe -> audio_extract -> scene_sample -> frames -> ocr -> asr`, built on
the existing `VideoIntake` / `Journal`, plus `frame_span` for timestamp+region evidence
and `AdapterRegistry` / `AsrAdapter` / `OcrAdapter` / `TesseractOcrAdapter` /
`CapabilityUnavailable`.

`scripts/run_video_pilot.py` (new) — bounded single-asset operator runner that verifies
the local bytes against the committed Git blob before deriving anything.

`tests/test_session013_video_pipeline.py` (new) — 26 regression tests.

`specs/features/session013-video-intelligence.md` (new) — SPEC-INT-013, status PARTIAL.

No existing module was modified; `media_intake.span` was deliberately left untouched.

## Video decoding, audio and speech in the remote/chat environment

- Real asset run: **BLOCKED**. The chat environment cannot fetch blobs over 1 MB
  (`unsupported content encoding: none ... consider using DownloadContents`, and no
  such tool is exposed), and there is no local checkout there. The runner reported
  `status: BLOCKED`, `capability_gaps: [{stage: identity, ...}]`, exit code 1.
- Decoding, audio extraction, scene sampling, frame extraction and OCR/ASR wiring were
  validated only against a locally generated ffmpeg TEST FIXTURE.
- ffmpeg and ffprobe are present there. `tesseract` is absent, so the default OCR
  adapter reports zero available languages and resolves to `None`. No ASR engine exists.

## What was independently verified

Only pipeline behaviour, by test, on a fixture: identity mismatch refusal, decode and
audio success, BLOCKED on missing engines with zero spans, verbatim multilingual span
creation, low-confidence marking without repair, language-capability BLOCKED instead of
substitution, stage reuse on re-run, refusal after source tampering, disjoint-root
refusal, invalid and out-of-duration interval refusal, region-outside-frame refusal,
sampling-policy recording.

## What remains unverified

Everything about the real video: no teaching observation, no concept, no method, no
shortcut, no applicability condition, no PYQ relationship, no verified label. Zero real
video frames, zero real transcripts, zero PYQ links were produced.

## Tests

`python3 -m unittest discover -s tests -v` — **Ran 86 tests, OK** (67 prior plus the new
Session 013 tests).

One test initially failed (`test_rerun_reuses_work_and_does_not_duplicate`, 7 != 8
attempts). Cause: `register_committed` records an identity attempt on every run by
design. The test was corrected to assert per-stage reuse plus exactly one additional
identity record; the pipeline was not weakened to make the test pass.

## Remaining blockers

1. No real video bytes reachable from the chat environment.
2. No Telugu-capable ASR engine anywhere in the project.
3. `tesseract` and its `tel` language pack are not installed in the chat environment.
4. Speed, recognition and retention dimensions still have no evidence procedure.

## Highest-value next milestone

Run `scripts/run_video_pilot.py` in the local checkout on
`Dynasties & Founders (Tricks).mp4`, then register a real ASR adapter (a Telugu-capable
engine) and install `tesseract` with `tel`+`eng`, so the BLOCKED asr/ocr stages become
located spans that a separate evidence-gated step can turn into candidate concepts.
