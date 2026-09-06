"""Knowledge processing subsystem (SPEC-KNW-001).

Implements the layer after ingestion: raw content records → processed content
→ GLM-based atomic knowledge extraction → relevance filtering → classification
→ CANDIDATE knowledge → deduplication → source corroboration → verification
queue. The trusted knowledge/ layer is never touched by this package.

Layout:

```
knowledge/
  __init__.py
  taxonomy.py        subjects / knowledge types / relevance enums (extended)
  processor.py       stage 1: null-safe text assembly from raw records
  extraction_schema.py  stage 2: strict validation of model output
  candidates.py      stage 3: candidate + question record construction
  scoring.py         documented, deterministic exam-relevance scores
  dedup.py           concept grouping + cross-source corroboration
  verify_queue.py    UNVERIFIED queue with provider separation
  pipeline.py        batch runner: checkpoint / resume / idempotency
  stores.py          atomic file stores for processed/candidates/questions
  client.py          GLM client (routed, env-keyed) + injectable interface
  prompts/
    knowledge_extraction_v1.py   versioned extraction prompt
```

Rules (SPEC-KNW-001 §1):

- Social-media content is T3_EXPERT and enters as CANDIDATE knowledge with
  verification_status UNVERIFIED. Nothing here can mark anything VERIFIED.
- Raw records are read-only. Every downstream record preserves provenance.
- No invented values: unavailable fields stay null.
- No test in this package performs a network call.
"""
