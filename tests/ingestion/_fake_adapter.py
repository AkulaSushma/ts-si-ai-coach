"""Shared fixtures for ingestion tests: a FakeAdapter that yields
deterministic content without any network access, plus temp dirs."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.ingestion.adapters.base import (  # noqa: E402
    AccessBlockedError,
    ContentItem,
    EdgePage,
    MediaRef,
    ProfileSnapshot,
    SourceAdapter,
    TransientError,
)


def make_item(i: int, *, kind: str = "post", caption: str | None = None) -> ContentItem:
    return ContentItem(
        content_id=f"item{i:04d}",
        content_type=kind,
        content_url=f"https://www.instagram.com/p/SHRT{i:04d}/",
        shortcode=f"SHRT{i:04d}",
        published_at="2026-01-01T00:00:00+00:00",
        caption=caption if caption is not None else f"caption #{i} #study",
        hashtags=[f"tag{i}"],
        media=[MediaRef(index=0, url=f"https://cdn.example/img{i}.jpg")],
        likes=i,
        comments=i % 10,
        platform_data={"pk": f"item{i:04d}", "fake": True},
    )


class FakeAdapter(SourceAdapter):
    """Deterministic adapter for tests. No network, instant, injectable."""

    platform = "fakegram"

    def __init__(self, *, timeline_pages=None, reels_pages=None,
                 profile=None, fail_items=None, fail_pages=None,
                 block_profile=False, block_edges=()):
        self.polite_delay_seconds = 0.0
        self.max_retries = 2
        self.timeline_pages = timeline_pages or []   # list[list[ContentItem]]
        self.reels_pages = reels_pages or []
        self.profile = profile
        self.fail_items = set(fail_items or [])     # content_ids to raise on
        self.fail_pages = set(fail_pages or [])      # (edge, page_index)
        self.block_profile = block_profile
        self.block_edges = set(block_edges)          # edge names that 403
        self.request_count = 0

    def fetch_profile(self, username: str) -> ProfileSnapshot:
        self.request_count += 1
        if self.block_profile:
            raise AccessBlockedError(f"login required for {username}")
        if self.profile is not None:
            return self.profile
        return ProfileSnapshot(
            platform=self.platform,
            username=username,
            user_id="user-1",
            is_private=False,
            declared_counts={"timeline": len(sum(self.timeline_pages, [])),
                             "reels": len(sum(self.reels_pages, []))},
            edges=(["timeline"] if self.timeline_pages else [])
            + (["reels"] if self.reels_pages else []),
            raw={"username": username},
        )

    def fetch_page(self, edge: str, user_id: str, cursor: str | None) -> EdgePage:
        self.request_count += 1
        page_index = int(cursor) if cursor is not None else 0
        if edge in self.block_edges:
            raise AccessBlockedError(f"{edge} pagination refused")
        if (edge, page_index) in self.fail_pages:
            raise TransientError(f"boom on {edge} page {page_index}")
        pages = self.timeline_pages if edge == "timeline" else self.reels_pages
        items = pages[page_index] if page_index < len(pages) else []
        has_next = page_index + 1 < len(pages)
        next_cursor = str(page_index + 1) if has_next else None
        return EdgePage(edge=edge, items=items, has_next=has_next,
                        end_cursor=next_cursor)

    def fetch_item(self, item: ContentItem) -> ContentItem:
        if item.content_id in self.fail_items:
            raise TransientError(f"item {item.content_id} exploded")
        return item


class TmpDirs:
    """Temp data-root so tests never touch the real data/ tree."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="ingest-test-")

    def __enter__(self):
        root = Path(self._tmp.name)
        return {
            "raw": root / "raw",
            "normalized": root / "normalized",
            "checkpoints": root / "checkpoints",
            "errors": root / "errors",
            "manifests": root / "manifests",
        }

    def __exit__(self, *exc):
        self._tmp.cleanup()
        return False
