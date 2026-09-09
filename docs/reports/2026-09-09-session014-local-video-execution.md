# Session 014 - Local execution capability for the real video pilot (status: BLOCKED for the real asset)

Checkpoint at start: `18472b8d7def069e2c25333f6c278224be0a1105`, re-established from the
actual remote commit list (`18472b8d` <- `92463742` <- `ade1817e` <- `25e49e9e`), not
from a previous report.

## Environment honesty statement

The assistant environment for this session is an isolated Linux sandbox with no
access to `D:\Projects\ts-si-ai-coach`, no network egress, and a GitHub API path
that refuses blobs over 1 MB. Therefore Phases 1-9 could NOT be executed against
the real Windows checkout by the assistant. Nothing in this report claims that the
real video was decoded, transcribed or read.

What was done instead: the two capabilities that were actually missing were built
and tested, so the operator can execute the whole phase sequence locally with one
command and obtain a factual report generated from observed values.

## REAL VIDEO RESULTS (assistant environment)

- decoded: NO (asset bytes unreachable)
- ASR: NO (no engine installed here)
- OCR: NO (`tesseract` absent here)
- real timestamps: 0
- real frame evidence: 0
- source observations: 0
- candidate concepts: 0
- candidate methods: 0
- candidate PYQ links: 0
- VERIFIED new knowledge: 0

The asset identity used everywhere is the previously observed committed identity:
`SI & Constable Concepts Videos & photos/Dynasties & Founders (Tricks).mp4`,
2,347,758 bytes, Git blob SHA-1 `5766d6575b6a54ab477d188558223f319b72f8dd`.
Its SHA-256 is still unknown, because that requires the real bytes.

## What was implemented

`scripts/asr_whisper.py` - local offline Telugu-capable Whisper-class ASR adapter
for the existing `AdapterRegistry`. Fail-closed: no backend means unavailable means
BLOCKED. Verbatim text only, no translation, engine-detected language preserved
separately and normalised to `te`/`en`/`mixed`/`und`, low-confidence retained and
flagged, empty segments never emitted as evidence. Backends searched:
`faster_whisper`, then `whisper`. No cloud service.

`scripts/run_session014_local.py` - one-command orchestrator that performs Phase 1
(git ground truth, Session 013 file presence, size + SHA-256 + blob identity),
Phase 2 (ffmpeg/ffprobe/tesseract paths and versions, real `--list-langs` output,
`tel`/`eng` presence, ASR backend detection, per-language registry snapshot,
explicit gap list), Phase 3 (the real bounded pilot, exact arguments), Phase 8
(full suite + bootstrap validator, each PASSED/FAILED/UNAVAILABLE), Phase 9 (second
run compared to the first, plus tamper refusal on a COPY with re-verification that
the original SHA-256 is unchanged) and Phase 10 (counts, blockers, session status).
Session status can only be PARTIAL when decode, ASR and OCR were all observed to
succeed; otherwise it is BLOCKED.

By construction the orchestrator reports candidate concepts, candidate methods,
candidate PYQ links and verified knowledge as 0. Interpretation is a separate
evidence-gated step; this layer only produces located evidence.

`tests/test_session014_local.py` - 26 new tests.

## PIPELINE RESULTS

- full suite: `python3 -m unittest discover -s tests -v` -> **Ran 112 tests in 3.274s, OK**
  (86 prior + 26 new), executed in the assistant sandbox with ffmpeg present.
- bootstrap validator: NOT RUN here (it validates repository ledgers that only exist
  in the real checkout).
- resumability: logic implemented and unit-tested; NOT exercised against the real
  asset.
- integrity checks: tamper refusal, identity mismatch refusal and disjoint-root
  refusal are tested; the real-asset tamper check runs on a copy only.

No test was weakened. No existing module was modified.

## Phases 4-7

Not reachable. Phase 4 (metadata, audio, transcript spans), Phase 5 (observation ->
interpretation -> candidate concept -> method -> conditions -> failure conditions),
Phase 6 (actual subject, language, tricks, exceptions) and Phase 7 (candidate PYQ
relationships against existing question IDs) all require real located evidence,
which does not exist yet. Nothing was invented to fill them.

## BLOCKERS

1. The real video bytes are unreachable from the assistant environment; the pilot
   must be run in the local Windows checkout.
2. `faster-whisper` (or `whisper`) is not known to be installed in the local
   checkout; until it is, the speech stage stays BLOCKED.
3. `tesseract` with `tel` + `eng` is not known to be installed locally; until it is,
   the on-screen text stage stays BLOCKED.
4. Speed, recognition and retention still have no evidence procedure anywhere in
   the project.
5. Legacy VERIFIED labels remain untrusted and unre-verified.

## Operator command (Phases 1-9 in one run)

    pip install faster-whisper
    python scripts/run_session014_local.py --repo . --work ../si-pilot --language-hint mixed --max-frames 12

Outputs `../si-pilot/session014-orchestrator.json` and `../si-pilot/session014-report.md`,
plus `../si-pilot/video-pilot.json` and `../si-pilot/video-pilot-rerun.json`.

## Session status

BLOCKED for the real asset. Session 014 is NOT complete: no real video evidence
exists yet and no extracted intelligence has been independently verified.

## Highest-value next milestone

Run the operator command above in `D:\Projects\ts-si-ai-coach`, then return
`session014-orchestrator.json`. With real located spans in hand, the next
implementation step is the evidence-gated interpretation step that turns spans into
CANDIDATE concepts and methods in `knowledge_graph`, with applicability and failure
conditions recorded and correctness/speed/recognition/retention left UNVERIFIED.
