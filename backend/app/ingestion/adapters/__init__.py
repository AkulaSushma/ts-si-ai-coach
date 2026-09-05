"""Platform adapters. Register new platforms by adding a module and adding
one entry to `get_adapter` — nothing else changes."""

from __future__ import annotations

from .base import (
    AccessBlockedError,
    AdapterError,
    ContentItem,
    EdgePage,
    MediaRef,
    ProfileSnapshot,
    SourceAdapter,
    TransientError,
)
from .instagram import InstagramAdapter

_ADAPTERS = {
    "instagram": InstagramAdapter,
}


def get_adapter(platform: str, **kwargs) -> SourceAdapter:
    try:
        return _ADAPTERS[platform](**kwargs)
    except KeyError:
        raise ValueError(
            f"no adapter for platform '{platform}'; registered: {sorted(_ADAPTERS)}"
        ) from None
