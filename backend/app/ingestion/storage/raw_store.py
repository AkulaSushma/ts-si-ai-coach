"""Durable raw record storage — the immutable evidence layer.

Layout: data/raw/<platform>/<source_id>/<content_id>.json
Profile snapshots: data/raw/<platform>/<source_id>/_profile.json

Records are written atomically and exactly once: if the file already exists the
store reports `stored=False` and does not touch it. This is what makes resume
idempotent (SPEC-ING-001 §4.4, §4.6).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ..adapters.base import ContentItem, ProfileSnapshot

ROOT = Path(__file__).resolve().parents[4]


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write_json(path: Path, payload: dict) -> None:
    """Write JSON durably: temp file in the same directory, then replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


class RawStore:
    def __init__(self, base: Path | None = None):
        self.base = Path(base) if base else ROOT / "data" / "raw"

    def source_dir(self, platform: str, source_id: str) -> Path:
        return self.base / platform / source_id

    def item_path(self, platform: str, source_id: str, content_id: str) -> Path:
        safe = content_id.replace("/", "_").replace("\\", "_") or "unknown"
        return self.source_dir(platform, source_id) / f"{safe}.json"

    def has_item(self, platform: str, source_id: str, content_id: str) -> bool:
        return self.item_path(platform, source_id, content_id).is_file()

    def store_profile(self, platform: str, source_id: str,
                      snap: ProfileSnapshot) -> Path:
        payload = {
            "source_id": source_id,
            "platform": platform,
            "username": snap.username,
            "user_id": snap.user_id,
            "is_private": snap.is_private,
            "declared_counts": snap.declared_counts,
            "edges": snap.edges,
            "raw": snap.raw,
            "extraction": {"status": "raw", "extracted_at": _utcnow()},
        }
        p = self.source_dir(platform, source_id) / "_profile.json"
        atomic_write_json(p, payload)
        return p

    def store_item(self, source_id: str, platform: str, username: str,
                   item: ContentItem) -> tuple[Path, bool]:
        """Persist one raw record. Returns (path, stored).

        stored=False means the record already existed and was left untouched.
        """
        p = self.item_path(platform, source_id, item.content_id)
        if p.is_file():
            return p, False

        images = [
            {
                "index": m.index,
                "url": m.url,
                "accessibility_caption": m.accessibility_caption,
                "media_kind": m.media_kind,
            }
            for m in item.media
            if m.media_kind == "image"
        ]
        video = None
        for m in item.media:
            if m.media_kind == "video":
                thumb = next(
                    (x.url for x in item.media if x.media_kind == "image"),
                    None,
                )
                video = {"url": m.url, "thumbnail_url": thumb}
                break

        slides = [
            {
                "index": m.index,
                "image_url": m.url,
                "accessibility_caption": m.accessibility_caption,
                "ocr_text": None,      # filled by the later OCR stage
                "ocr_text_raw": None,   # original OCR output, never overwritten
            }
            for m in item.media
            if m.media_kind == "image"
        ]

        record = {
            "source_id": source_id,
            "platform": platform,
            "profile_username": username,
            "content_id": item.content_id,
            "shortcode": item.shortcode,
            "content_url": item.content_url,
            "content_type": item.content_type,
            "published_at": item.published_at,
            "caption": item.caption,
            "hashtags": item.hashtags,
            "media": {"images": images, "video": video},
            "slides": slides,
            "text": {
                "caption_text": item.caption,
                "ocr_text": None,        # later OCR stage
                "transcript": None,      # later transcription stage
                "on_screen_text": item.on_screen_text or None,
            },
            "engagement": {"likes": item.likes, "comments": item.comments},
            "platform_data": item.platform_data,
            "extraction": {"status": "raw", "extracted_at": _utcnow()},
        }
        atomic_write_json(p, record)
        return p, True
