# SPEC-INT-010 — Fail-closed verification and bounded local media intake

## Purpose

Stop the existing unsafe verification writer and establish auditable, revision-bound evidence and local media intake without changing historical PYQs, official facts, or source records.

## Scope

Additive Python standard-library operational modules. The legacy verifier becomes a non-mutating refusal entry point, with its exact previous source retained in the existing Git checkpoint and a local audit artifact. New verification attempts are immutable files; eligibility is a read-time projection, not a rewrite of historical VERIFIED labels. A PASS supports only its explicitly evaluated dimension, never speed/retention by implication. No automatic trusted knowledge write. Local intake registers supplied paths by SHA-256, probes with optional ffprobe, records attempts and evidence locations, and creates only UNVERIFIED candidates. No automatic OCR/ASR or paid provider calls. No UI or bulk processing.

Tasks recorded before implementation: T-0065 integrity engine/regressions PARTIAL; T-0066 immutable bounded intake/regressions PARTIAL; T-0067 real-media pilot PARTIAL; T-0068 repository integration/full-suite validation BLOCKED pending actual development-checkout access. Root ledger reconciliation remains a separate outstanding integration task; this task section is not a replacement for TASK_LEDGER.md.

## Acceptance Criteria

1. Importing/running the legacy verifier cannot mutate historical registers; running it fails with a clear explanation.
2. Preserve its exact prior bytes as evidence with Git blob 5cf50b98af72bec6629271c322730a7376869029.
3. A verification attempt binds subject ID, exact revision hash, dimension, procedure, assessor, cases and hashed evidence files. Record PASS, FAIL and INCONCLUSIVE; never overwrite an existing attempt.
4. Eligibility rejects absent/incomplete/malformed evidence, hash mismatch, wrong subject/revision/dimension, self-review, FAIL, INCONCLUSIVE and contradictory attempts. All attempts on the revision must be considered; later PASS never erases earlier failure. A corrected method uses a new revision; disputed same-revision resolution is deferred.
5. A structurally complete deterministic PASS with actual observed matching cases and checked boundary cases can support mathematical eligibility only. Genuine verifier independence remains reviewable and is not inferred merely from different names. Test fixtures prove gate mechanics, not real method correctness.
6. Register bounded explicitly selected local media paths using streamed SHA-256. Preserve distinct occurrences for duplicate bytes; keep unknown publisher/URL/publication date null; never modify originals.
7. Probe jobs are keyed by asset digest and processor version. Successful retries reuse only intact evidence; failed attempts persist. Refuse path traversal/symlinks and files changing during read.
8. Evidence spans preserve original language and valid image boxes/video time intervals; candidate provenance is explicit SOURCE_DERIVED/T3_EXPERT or MODEL_DERIVED/T4_AI, UNVERIFIED only, with authored text/_te fields and extraction provenance.
9. Unit tests include clean PASS and deliberately poisoned verification cases, append-only retry, duplicate paths, resumability, corrupt artifacts, span bounds, no source/model relabeling, and real image intake. No synthetic media passed off as real.
10. Existing project data remain unchanged. Full suite/bootstrap are attempted only with a genuine available checkout; report unavailable gates honestly. No COMPLETE claim for the overall session from targeted tests.

## Open Questions

Existing Windows checkout execution is not exposed to this chat. Full repository validation and root-ledger integration remain blocked. OCR/ASR providers, full video pilot, attribution and real method re-verification remain partial. No historical failure reconstruction is authorized.

## Status

APPROVED

Scope authority: user's explicit Session 010 engineering request; this bounded specification is the implementation decomposition, not approval for binary migration, history rewriting or new external services.
