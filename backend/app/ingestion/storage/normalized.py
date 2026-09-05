"""Normalization: raw records → normalized records (SPEC-ING-001 §4.5).

The normalized record adds the mandatory provenance block and the
`ai_processing` scaffold whose every field is null until the GLM stage
exists. It derives a combined text representation and content hashes used by
the later deduplication stage. It never invents values: a field that is null
in the raw record stays null here.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .raw_store import ROOT, atomic_write_json


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalized_key(text: str) -> str:
    """Lowercase, collapse whitespace, strip hashtags/punctuation — the basis
    for content-equivalence hashing."""
    t = text.lower()
    t = re.sub(r"#[\w]+", " ", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_record(raw: dict) -> dict:
    """Build the normalized record from one raw record (dict, not path)."""
    caption = raw.get("caption")
    slide_texts = [
        s.get("ocr_text")
        for s in (raw.get("slides") or [])
        if s.get("ocr_text")
    ]
    parts = [caption] if caption else []
    parts.extend(t for t in slide_texts if t)
    normalized_text = "\n\n".join(parts) if parts else None

    norm_key = _normalized_key(normalized_text or "")
    content_hash = (
        _sha256(norm_key) if norm_key
        else _sha256((raw.get("content_id") or "") + "|" + (raw.get("content_url") or ""))
    )

    media = raw.get("media") or {}
    images = media.get("images") or []
    video = media.get("video") or {}
    video_url = video.get("url") if isinstance(video, dict) else None

    return {
        "source_id": raw.get("source_id"),
        "platform": raw.get("platform"),
        "content_id": raw.get("content_id"),
        "shortcode": raw.get("shortcode"),
        "content_url": raw.get("content_url"),
        "content_type": raw.get("content_type"),
        "published_at": raw.get("published_at"),
        "caption": raw.get("caption"),
        "hashtags": sorted({(h or "").lower() for h in (raw.get("hashtags") or [])}),
        "media_counts": {
            "images": len(images),
            "video": bool(video_url),
        },
        "normalized_text": normalized_text,
        "text": {
            "caption_text": (raw.get("text") or {}).get("caption_text"),
            "ocr_text": None,        # filled by the OCR stage
            "transcript": None,      # filled by the transcription stage
            "on_screen_text": (raw.get("text") or {}).get("on_screen_text"),
        },
        "engagement": {
            "likes": (raw.get("engagement") or {}).get("likes"),
            "comments": (raw.get("engagement") or {}).get("comments"),
        },
        "hashes": {
            "content_hash": content_hash,
            "url_hash": _sha256(raw.get("content_url") or ""),
        },
        "provenance": {
            "source_id": raw.get("source_id"),
            "profile_username": raw.get("profile_username"),
            "content_id": raw.get("content_id"),
            "original_url": raw.get("content_url"),
            "content_type": raw.get("content_type"),
            "published_at": raw.get("published_at"),
            "extracted_at": (raw.get("extraction") or {}).get("extracted_at"),
            "provenance_tier": "T3_EXPERT",
        },
        "ai_processing": {
            "status": "not_processed",
            "subject": None,
            "knowledge_type": None,
            "si_relevance": None,
            "constable_relevance": None,
            "telangana_relevance": None,
            "pyq_similarity": None,
            "revision_priority": None,
            "confidence": None,
            "verification_status": None,
            "processed_at": None,
        },
        "normalization": {
            "normalized_at": (raw.get("extraction") or {}).get("extracted_at"),
            "raw_file": None,   # filled by NormalizedStore with the relative path
        },
    }


class NormalizedStore:
    def __init__(self, base: Path | None = None):
        self.base = Path(base) if base else ROOT / "data" / "normalized"

    def store(self, raw_record: dict, source_id: str) -> Path:
        norm = normalize_record(raw_record)
        p = self.base / norm["platform"] / source_id / f"{norm['content_id']}.json"
        rel = Path("data") / "raw" / norm["platform"] / source_id / f"{norm['content_id']}.json"
        norm["normalization"]["raw_file"] = rel.as_posix()
        atomic_write_json(p, norm)
        return p
