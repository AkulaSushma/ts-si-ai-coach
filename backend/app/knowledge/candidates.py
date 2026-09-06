"""Stage 3 — candidate knowledge + question records (SPEC-KNW-001 §5).

One validated ExtractionResult becomes N candidate records (atomic units)
plus M question records, every one carrying full provenance back to the raw
content item, and verification_status UNVERIFIED — the pipeline cannot
create anything else.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from . import taxonomy
from .scoring import exam_relevance_scores


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def candidate_id(source_id: str, content_id: str, prompt_version: str,
                 index: int, knowledge_text: str) -> str:
    """Deterministic id over (source, content, prompt, index, text): re-running
    the same extraction yields the same id, so idempotency is a file check,
    not a convention (SPEC-KNW-001 §5, §11)."""
    basis = "\x1f".join([
        source_id, content_id, prompt_version, str(index), knowledge_text,
    ])
    return "CK-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def question_id(source_id: str, content_id: str, prompt_version: str,
                index: int, question_text: str) -> str:
    basis = "\x1f".join([
        source_id, content_id, prompt_version, str(index), question_text,
    ])
    return "CQ-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def _provenance(processed, prompt_version, model_name: str) -> dict:
    return {
        "source_id": processed.source_id,
        "platform": processed.platform,
        "profile_username": processed.profile_username,
        "content_id": processed.content_id,
        "source_url": processed.source_url,
        "content_type": processed.content_type,
        "published_at": processed.published_at,
        "provenance_tier": "T3_EXPERT",
        "test_fixture": processed.is_fixture,
        "extraction_model": model_name,
        "prompt_version": prompt_version,
        "extraction_timestamp": _utcnow(),
    }


def build_candidates(processed, extraction, *, prompt_version: str,
                     model_name: str) -> list[dict]:
    """ExtractionResult.items -> candidate records. NOT_RELEVANT yields none
    (the schema already guarantees items are absent)."""
    if extraction.relevance == "NOT_RELEVANT":
        return []
    prov = _provenance(processed, prompt_version, model_name)
    records = []
    for i, item in enumerate(extraction.items):
        scores = exam_relevance_scores(item.subject, item.knowledge_type,
                                       processed.published_at)
        record = {
            "candidate_id": candidate_id(
                processed.source_id, processed.content_id, prompt_version,
                i, item.knowledge_text,
            ),
            "knowledge_text": item.knowledge_text,
            "knowledge_text_te": item.knowledge_text_te,
            "subject": item.subject,
            "topic": item.topic,
            "knowledge_type": item.knowledge_type,
            "relevance": extraction.relevance,
            "confidence": item.confidence,
            "confidence_basis": "model_self_reported",
            "exam_relevance": scores,
            "verification_status": taxonomy.INITIAL_VERIFICATION_STATUS,
            "provenance": prov,
        }
        records.append(record)
    return records


def build_questions(processed, extraction, *, prompt_version: str,
                    model_name: str) -> list[dict]:
    """ExtractionResult.questions -> question records (UNVERIFIED, answers
    only when STATED_BY_SOURCE — enforced by the schema validator)."""
    if extraction.relevance == "NOT_RELEVANT":
        return []
    prov = _provenance(processed, prompt_version, model_name)
    records = []
    for i, q in enumerate(extraction.questions):
        scores = exam_relevance_scores(q.subject, "QUESTION",
                                       processed.published_at)
        record = {
            "question_id": question_id(
                processed.source_id, processed.content_id, prompt_version,
                i, q.question_text,
            ),
            "question_text": q.question_text,
            "options": q.options,
            "answer": q.answer,
            "answer_status": q.answer_status,
            "explanation": q.explanation,
            "subject": q.subject,
            "topic": q.topic,
            "question_format": q.question_format,
            "exam_relevance": scores,
            "verification_status": taxonomy.INITIAL_VERIFICATION_STATUS,
            "provenance": prov,
        }
        records.append(record)
    return records
