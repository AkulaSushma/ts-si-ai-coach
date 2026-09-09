# SPEC-INT-012 — Exam-solving knowledge graph and deterministic rule derivation

Status: PARTIAL (implemented and tested at this checkpoint; not complete)
Supersedes nothing. Extends SPEC-INT-010 (integrity/intake) and SPEC-INT-011 (expert-source intelligence).

## Problem

SPEC-INT-011 produced located evidence spans and candidate interpretations from one real
image, but the project still had no structure in which candidate intelligence could be
related to concepts, questions and evidence, and no mechanism to derive a rule when the
source shows only data and states no rule. Without both, media analysis degenerates into
transcription and the learning layer would have nothing trustworthy to read from.

## Design decisions

### D-012-1 Status is derived, never stored
`knowledge_graph.node_status` computes one of
`VERIFIED / SUPPORTED / CANDIDATE / UNVERIFIED / FAILED / INCOMPLETE / BLOCKED`
at read time from the evidence journal. No code path writes a status string onto a node,
so the historical promotion defect cannot recur by construction: there is nothing to
overwrite.

Precedence is pessimistic:
`BLOCKED > FAILED > INCOMPLETE > VERIFIED > SUPPORTED > CANDIDATE > UNVERIFIED`.
Any FAIL attempt on the node's current subject revision makes the node read FAILED even if
other dimensions passed. Any exception while reading evidence yields BLOCKED, not a guess.

### D-012-2 Dimensions stay separate
`REQUIRED_DIMENSIONS` states, per node kind, which of
`correctness / applicability / speed / recognition / retention / source_fidelity`
must each independently pass before the node can read VERIFIED. A fast method requires
correctness *and* applicability *and* speed. Correct-but-unmeasured is never VERIFIED.

### D-012-3 Origin is intrinsic and separate from status
`SOURCE_DERIVED / MODEL_DERIVED / INDEPENDENTLY_DERIVED / OFFICIAL_DOCUMENT`.
A source-derived node with located evidence reads SUPPORTED (the source did say it), which
is explicitly *not* VERIFIED (it may still be wrong). A model-derived node with no passing
evidence reads CANDIDATE regardless of how plausible it looks.

### D-012-4 Exam relationships require evidence
`solves`, `applies_to_pyq`, `recognizes` and `contradicts` are refused unless the caller
supplies located evidence files (digested at write time) plus a written justification, and
the target PYQ id is in a caller-supplied known-id set. This makes fabricated
question-method links impossible through the normal API rather than merely discouraged.

### D-012-5 Append-only, hash-sealed graph
Each node/edge is a separate hashed JSON record written with `open('xb')` + fsync + link,
matching the evidence journal. Re-adding a node id raises. Tampering with a record is
detected on read. History is preserved rather than corrected.

### D-012-6 Gaps are nodes, not silence
When a needed observation cannot be produced (no ASR engine, video unreachable), a node is
created with `blocked_reason` and reads BLOCKED. The absence of audio intelligence is
therefore visible in the graph instead of being an invisible hole.

### D-012-7 Rule derivation searches a declared space and may return FAIL
`series_derive.derive` searches a finite, declared space (closed forms `a*n**p + b*n + c`
for p in 1..3 with coefficients in -12..12, and step rules `a(n) = a(n-1) + f(n)`), tests
every observed pair, and returns `FAIL` when nothing reproduces the data. It never returns
a nearest match. It also reports whether the fitting rule is *unique*, because a rule that
is not uniquely determined cannot be taught as "the" trick. `interpretation_limits` states
explicitly that absence of a match does not prove no rule exists.

## Pilot outcome (real asset)

Asset `Screenshot_2026-09-01-19-51-42-53_….jpg`, git blob `b1705377…`, sha256 `e743b6d7…`,
423,178 bytes, 1080x2414. Visible handwritten table: 1-1, 2-5, 3-13, 4-27, 5-48, 6-78,
7-118, 8-170. No rule, no worked steps and no question stem are visible.

First differences 4, 8, 14, 21, 30, 40, 52; second differences 4, 6, 7, 9, 10, 12 — not
constant at any depth. 90,000 declared rules were tested; none reproduced all eight pairs.
Result: correctness FAIL, method node status FAILED, zero PYQ links. The likely causes are
recorded as limitations (the rule was probably spoken aloud, or one handwritten digit is
misread) rather than resolved by adjusting the data to fit.

This is the intended behaviour. A pipeline that cannot return FAIL on real material is not
an evidence system.

## Not implemented

- Speed, recognition and retention assessment procedures (dimensions exist; no harness).
- Any PYQ edge from media intelligence (none is currently justified by evidence).
- OCR and ASR adapters; all video content remains unreachable in this environment.
- Weightage/sequencing model.
- Concurrency safety: single-writer, hardlink-based, POSIX-validated only.
