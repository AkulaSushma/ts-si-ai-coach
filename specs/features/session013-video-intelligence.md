# SPEC-INT-013 — Video intelligence path (status: PARTIAL)

## Purpose

Remove the largest evidence bottleneck in the project: no real video had ever been
turned into located evidence. This spec defines a resumable, fail-closed pipeline
from a committed video asset to located source evidence, and stops deliberately
short of asserting teaching claims.

## Stage chain

    identity -> probe -> audio_extract -> scene_sample -> frames -> ocr -> asr

Every stage appends an `attempt` record to the SPEC-INT-010 journal. Each stage is
keyed by `revision({asset sha256, stage, processor version, engine version, params})`.
Re-running an unchanged asset finds the prior PASS record, re-verifies the artifact
digest, and reuses it. Only the identity check is intentionally re-recorded on every
run, because each run genuinely re-verifies the local bytes against the committed
Git blob SHA-1.

## Fail-closed capability model

`AsrAdapter` and `OcrAdapter` are interfaces. The default registry contains only
`TesseractOcrAdapter`, whose availability is decided from the actual installed
language packs, so a Telugu request on an English-only install is BLOCKED rather
than silently mis-read. No ASR adapter ships in the repository.

When no adapter can serve the requested language the pipeline records a BLOCKED
attempt naming the missing capability. BLOCKED never produces a span, a span is
required for a candidate, and a candidate is required for any graph node, so a
missing engine can never become knowledge.

`CapabilityUnavailable` raised inside an adapter is also converted to BLOCKED.

## Evidence locations

- `video_interval` — `{start_seconds, end_seconds}` for speech, validated inside the
  probed duration (existing `media_intake.span`).
- `video_frame_region` — `{at_seconds, xyxy, frame_sha256}` for on-screen text, added
  as `VideoPipeline.frame_span`. `media_intake.span` was left untouched so its
  already-validated behaviour is unchanged.

Sampled timestamps come from ffmpeg scene detection (`scene > 0.30`), because in
this collection a cut usually marks a new board state, which is exactly where
on-screen teaching text changes. When no cut is detected the pipeline falls back to
the SPEC-INT-011 fixed fractions and records `sampling_policy` so a reader can tell
a detected cut from a blind sample.

## Multilingual rules

- Recognised text is stored verbatim in the source language (`te`, `en`, `mixed`, `und`).
- No translation or normalisation is produced by this pipeline. A translation would be
  a separate MODEL_INTERPRETED candidate carrying its own uncertainty.
- ASR output below `min_confidence` (0.55) is retained with `low_confidence: true`.
  Ambiguous words are never repaired or dropped.
- An ASR segment with an unexpected language label, an empty text, or an invalid or
  out-of-duration interval raises rather than being coerced.

## What this pipeline deliberately does not do

It does not create a concept, method, shortcut, applicability condition, translation,
publisher attribution, PYQ relationship or any VERIFIED label. Those remain the job of
separate evidence-gated calls into `knowledge_graph` (SPEC-INT-012), where status is
derived from the evidence journal at read time and the six dimensions (correctness,
applicability, speed, recognition, retention, source_fidelity) stay independent.

## Operator invocation (real checkout, one bounded asset)

    python scripts/run_video_pilot.py --source-root . --relative "SI & Constable Concepts Videos & photos/Dynasties & Founders (Tricks).mp4" --git-blob 5766d6575b6a54ab477d188558223f319b72f8dd --state-root ../si-pilot/state --artifact-root ../si-pilot/artifacts --collection SI-Constable-media-25e49e9 --language-hint mixed --max-frames 12 --out ../si-pilot/video-pilot.json

State and artifact roots must be outside the media root; the constructor refuses
otherwise, so raw media can never be written to.

## Status

PARTIAL. The pipeline, its refusal behaviour and its resumability are implemented and
tested. No real video has been decoded yet: the chat/remote environment cannot fetch
blobs over 1 MB and has no ASR engine, so the real-asset run is BLOCKED there and must
be executed in the local checkout.
