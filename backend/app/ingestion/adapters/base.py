"""Common adapter interface. Every platform implements this, the runner and
storage layers stay platform-agnostic (SPEC-ING-001 §4.2).

Instagram is the first adapter. YouTube / Telegram / website / PDF adapters
will subclass `SourceAdapter` later without changes to runner, storage, or CLI.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


class AdapterError(RuntimeError):
    """Base class for adapter failures."""


class AccessBlockedError(AdapterError):
    """The platform refused access (auth wall, login redirect, rate limit).

    The runner records this honestly and stops the source. It is never a
    signal to retry harder or to bypass the platform's controls.
    """


class TransientError(AdapterError):
    """A network hiccup that is legitimate to retry with backoff."""


@dataclass
class MediaRef:
    """A single media reference inside an item, with its ordering index."""
    index: int
    url: str | None
    accessibility_caption: str | None = None
    media_kind: str = "image"   # image | video


@dataclass
class ContentItem:
    """Platform-neutral representation of one discovered content item.

    `platform_data` preserves the original platform JSON so the raw record is
    never lossy. Every field the platform does not expose stays None — the
    raw store writes null rather than inventing a value.
    """
    content_id: str
    content_type: str            # taxonomy.CONTENT_TYPES
    content_url: str | None = None
    shortcode: str | None = None
    published_at: str | None = None
    caption: str | None = None
    hashtags: list[str] = field(default_factory=list)
    media: list[MediaRef] = field(default_factory=list)
    likes: int | None = None
    comments: int | None = None
    on_screen_text: str | None = None      # platform-provided, if any
    transcript_hint: str | None = None    # platform-provided, if any
    platform_data: dict = field(default_factory=dict)


@dataclass
class EdgePage:
    """One page of items from a profile edge (e.g. timeline, reels)."""
    edge: str
    items: list[ContentItem]
    has_next: bool
    end_cursor: str | None


@dataclass
class ProfileSnapshot:
    """Platform-neutral profile information, plus the raw platform payload."""
    platform: str
    username: str
    user_id: str | None
    is_private: bool | None
    declared_counts: dict[str, int | None] = field(default_factory=dict)
    edges: list[str] = field(default_factory=list)   # e.g. ["timeline", "reels"]
    raw: dict = field(default_factory=dict)
    # Pages embedded in the profile response itself (e.g. Instagram's profile
    # HTML embeds the first timeline page). Consumed by the runner before any
    # separate page fetch. Keys are edge names.
    embedded_pages: dict[str, "EdgePage"] = field(default_factory=dict)


class SourceAdapter(abc.ABC):
    """Common ingestion interface for all platforms."""

    platform: str = "abstract"

    #: requests are issued one at a time with at least this delay (+jitter)
    polite_delay_seconds: float = 2.5
    max_retries: int = 3

    @abc.abstractmethod
    def fetch_profile(self, username: str) -> ProfileSnapshot:
        """Fetch profile metadata. Raises AccessBlockedError if walled."""

    @abc.abstractmethod
    def fetch_page(self, edge: str, user_id: str, cursor: str | None) -> EdgePage:
        """Fetch one page of an edge. `cursor=None` starts from the top."""

    def fetch_item(self, item: ContentItem) -> ContentItem:
        """Optional: enrich a single item (default: already complete)."""
        return item
