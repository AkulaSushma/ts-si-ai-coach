"""Stage 1 — content processing (SPEC-KNW-001 §3).

Turns one raw ingestion record (SPEC-ING-001 §4.4 schema) into one processed
record. Null-safe by construction: every text source is checked, missing ones
are skipped, none are invented. OCR and transcription are interfaces only in
this build — the processor reads whatever text already exists on the raw
record and plugs providers in later without structural change.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


class OcrProvider(Protocol):
    """Interface for a future OCR stage. Not implemented in this build —
    raw media is unavailable (B-08) and the pipeline order puts OCR after
    raw storage anyway (SPEC-ING-001 §3)."""

    def ocr_image(self, url: str) -> str | None: ...


class TranscriptionProvider(Protocol):
    """Interface for a future audio transcription stage. Not implemented
    here; same rationale as OcrProvider."""

    def transcribe(self, url: str) -> str | None: ...


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean(text: str | None) -> str | None:
    """Return trimmed text, or None for null/empty. Never fabricates."""
    if text is None:
        return None
    t = text.strip()
    return t if t else None


@dataclass
class ProcessedRecord:
    """The null-safe, text-assembled view of one raw record."""
    source_id: str
    platform: str
    content_id: str
    content_type: str | None
    source_url: str | None
    published_at: str | None
    profile_username: str | None
    text_parts: list[dict] = field(default_factory=list)  # [{"kind","text"}]
    skipped_reason: str | None = None
    processing_hash: str | None = None
    processed_at: str | None = None
    hashtags: list[str] = field(default_factory=list)
    media_counts: dict = field(default_factory=dict)
    is_fixture: bool = False
    raw_path: str | None = None

    @property
    def has_text(self) -> bool:
        return bool(self.text_parts)

    def assembled_text(self) -> str:
        return "\n\n".join(p["text"] for p in self.text_parts)


def assemble_text_parts(raw: dict) -> list[dict]:
    """Collect available text from a raw record, in reading order.

    Kinds: caption, slide_ocr (slide order preserved), transcript,
    on_screen. Null and empty values are skipped — never invented.
    """
    parts: list[dict] = []

    text_block = raw.get("text") or {}
    caption = _clean(text_block.get("caption_text") or raw.get("caption"))
    if caption:
        parts.append({"kind": "caption", "text": caption})

    for slide in raw.get("slides") or []:
        ocr = _clean((slide or {}).get("ocr_text"))
        if ocr:
            parts.append({"kind": "slide_ocr", "text": ocr})

    transcript = _clean(text_block.get("transcript"))
    if transcript:
        parts.append({"kind": "transcript", "text": transcript})

    on_screen = _clean(text_block.get("on_screen_text"))
    if on_screen:
        parts.append({"kind": "on_screen", "text": on_screen})

    return parts


def processing_hash(parts: list[dict]) -> str:
    """Stable digest over assembled text, so identical content across sources
    is detectable before any model call (cost control, SPEC-KNW-001 §9)."""
    basis = "\n".join(f"{p['kind']}:{p['text']}" for p in parts)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def process_raw_record(raw: dict, *, raw_path: str | None = None) -> ProcessedRecord:
    """One raw record -> one ProcessedRecord. Raises nothing for missing
    fields; a record with no text anywhere is returned with skipped_reason
    set, and the pipeline performs no model call for it."""
    parts = assemble_text_parts(raw)
    media = raw.get("media") or {}
    images = media.get("images") or []
    video = media.get("video") or {}

    return ProcessedRecord(
        source_id=raw.get("source_id") or "unknown",
        platform=raw.get("platform") or "unknown",
        content_id=raw.get("content_id") or "unknown",
        content_type=raw.get("content_type"),
        source_url=raw.get("content_url"),
        published_at=raw.get("published_at"),
        profile_username=raw.get("profile_username"),
        text_parts=parts,
        skipped_reason=None if parts else "no_text",
        processing_hash=processing_hash(parts) if parts else None,
        processed_at=_utcnow(),
        hashtags=[(h or "").lower() for h in (raw.get("hashtags") or [])],
        media_counts={
            "images": len(images),
            "video": bool(video.get("url")) if isinstance(video, dict) else False,
        },
        is_fixture=bool(raw.get("test_fixture")),
        raw_path=raw_path,
    )
