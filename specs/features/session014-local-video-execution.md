# SPEC-INT-014 - Local execution of the real video pilot (status: PARTIAL)

## Why this exists

Session 013 built the video pipeline but could not execute it on a real asset:
the chat/remote environment cannot fetch blobs over 1 MB and ships no ASR engine,
so every real run correctly returned BLOCKED. The bottleneck is therefore not the
pipeline design but the absence of (a) the real bytes and (b) a speech engine.

SPEC-INT-014 closes both gaps for a local checkout:

1. `scripts/asr_whisper.py` - a local, offline, Telugu-capable Whisper-class ASR
   adapter for the existing `AdapterRegistry`.
2. `scripts/run_session014_local.py` - a one-command orchestrator that performs the
   ground-truth, capability, pilot, test, resumability and integrity phases in the
   real checkout and writes a factual report of what was actually observed.

No cloud or external processing service is introduced. Both backends
(`faster_whisper`, `whisper`) run locally against a downloaded model.

## ASR adapter rules

- If no backend package is importable, `available()` is False, `transcribe()` raises
  `CapabilityUnavailable`, and the pipeline records BLOCKED. A missing engine can
  never become evidence.
- `te` and `en` hints are passed to the engine; `mixed` and `und` let the engine
  auto-detect. The engine's detected label is preserved as `detected_language`.
- The emitted `language` label is normalised to `te` / `en` / `mixed` / `und`.
  A detected language outside that vocabulary becomes `und`; it is never coerced
  into Telugu or English.
- Text is emitted verbatim. This adapter produces no translation, no normalisation
  and no repair of ambiguous words. A translation would be a separate
  MODEL_INTERPRETED candidate carrying its own uncertainty.
- Confidence is a monotonic transform of the engine's own log-probability, not an
  independent accuracy estimate. It is used only to flag low-confidence evidence;
  low-confidence segments are retained, never dropped.
- Empty segments are skipped, because a segment with no observable content is not
  evidence.

## Orchestrator phases

| Phase | What is recorded |
| --- | --- |
| 1 | `git status --short`, `git rev-parse HEAD`, `git log --oneline -10`, branch, Session 013 file presence, asset size + SHA-256 + Git blob SHA-1 vs the expected `5766d657...` |
| 2 | ffmpeg / ffprobe / tesseract paths and version lines, actual `tesseract --list-langs` output, `tel` and `eng` presence, ASR backend searched and found, model size, registry snapshot per language, explicit capability gaps |
| 3 | The real bounded pilot invoked exactly as specified, with the returned JSON attached verbatim |
| 8 | Full unittest suite and the bootstrap validator, each classified PASSED / FAILED / UNAVAILABLE |
| 9 | A second pilot run compared against the first (asset hash, stage results, span count, frame count, BLOCKED stages still recorded), plus a tamper-refusal check performed on a COPY of the asset in a temporary directory |
| 10 | REAL VIDEO RESULTS counts and BLOCKERS, with session status PARTIAL only when decode, ASR and OCR were all observed to succeed |

The original media file is opened read-only. The tamper check copies the asset,
mutates the copy, asserts refusal, and re-verifies that the original SHA-256 is
unchanged.

## What the orchestrator deliberately does not do

It reports `candidate_concepts`, `candidate_methods`, `candidate_pyq_links` and
`verified_new_knowledge` as 0 by construction. This layer produces located evidence
only. Interpretation, candidate concepts, candidate methods, applicability and
failure conditions, and PYQ relationships must be created by a separate
evidence-gated step against `knowledge_graph` (SPEC-INT-012), where status is
derived from the evidence journal at read time and correctness, applicability,
speed, recognition, retention and source fidelity remain independent dimensions.

## Operator invocation

    pip install faster-whisper
    python scripts/run_session014_local.py --repo . --work ../si-pilot --language-hint mixed --max-frames 12

Windows OCR prerequisite: install Tesseract (UB Mannheim build) with the `tel` and
`eng` language data, and ensure `tesseract` is on PATH. If it is absent the OCR
stage stays BLOCKED and the report says so.

## Status

PARTIAL. The adapter and orchestrator are implemented and tested. No real video has
been decoded yet in any environment available to the assistant; the real run must be
executed in the local checkout, and its observed output is what decides the Session
014 outcome.
