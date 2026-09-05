"""Source registry: load, validate, extend `config/source_registry.json`.

A new source is added by editing the JSON (or via `cli add`); no code change
is ever needed to ingest a new profile. Validation happens at load time so a
bad entry fails loudly before any network request is made.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .taxonomy import MAX_ITEMS_HARD_CAP

ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "config" / "source_registry.json"

# Instagram username rules: 1-30 chars from [A-Za-z0-9._], no leading/trailing
# dot or underscore. Dots must not be consecutive — but we stay permissive on
# that one because we are validating *what we ingest*, not policing Instagram.
_USERNAME_RE = re.compile(r"^(?!.*\.\.)(?!.*\.\.)[A-Za-z0-9._](?:[A-Za-z0-9._]{0,28}[A-Za-z0-9._])?$")

_SOURCE_ID_RE = re.compile(r"^[A-Z]{2,4}\d{3,}$")


class RegistryError(ValueError):
    """Raised when the registry file is structurally invalid."""


@dataclass
class Source:
    source_id: str
    platform: str
    username: str
    profile_url: str
    enabled: bool = True
    max_items: int = MAX_ITEMS_HARD_CAP
    added_at: str | None = None
    notes: str | None = None
    extra: dict = field(default_factory=dict)


def _parse_profile_url(platform: str, url: str, source_id: str) -> str:
    """Validate and canonicalize a profile URL. Returns the username."""
    if not isinstance(url, str) or "://" not in url:
        raise RegistryError(f"{source_id}: profile_url '{url}' is not a URL")
    m = re.match(r"^https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]+)/?(?:\?.*)?$", url)
    if not m:
        raise RegistryError(
            f"{source_id}: '{url}' is not an Instagram profile URL "
            f"(expected https://www.instagram.com/<username>/)"
        )
    username = m.group(1)
    if not _USERNAME_RE.match(username):
        raise RegistryError(f"{source_id}: username '{username}' is not a valid Instagram username")
    return username


def load_registry(path: Path | str | None = None) -> tuple[list[Source], dict]:
    """Load and validate the registry. Returns (sources, defaults_dict)."""
    p = Path(path) if path is not None else REGISTRY_PATH
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RegistryError(f"registry not found: {p}") from None
    except json.JSONDecodeError as e:
        raise RegistryError(f"registry is not valid JSON: {e}") from None

    defaults = doc.get("defaults") or {}
    raw_sources = doc.get("sources")
    if not isinstance(raw_sources, list):
        raise RegistryError("'sources' must be a list")

    seen_ids: set[str] = set()
    seen_usernames: dict[str, str] = {}
    sources: list[Source] = []
    for i, entry in enumerate(raw_sources):
        if not isinstance(entry, dict):
            raise RegistryError(f"sources[{i}] is not an object")
        sid = entry.get("source_id")
        if not isinstance(sid, str) or not _SOURCE_ID_RE.match(sid):
            raise RegistryError(f"sources[{i}]: source_id '{sid}' must match e.g. IG001")
        if sid in seen_ids:
            raise RegistryError(f"duplicate source_id: {sid}")
        seen_ids.add(sid)

        platform = entry.get("platform")
        if platform not in ("instagram",):
            # Future adapters (youtube, telegram, website, pdf) register here.
            raise RegistryError(f"{sid}: unknown platform '{platform}'")

        url = entry.get("profile_url")
        username = _parse_profile_url(platform, url, sid)
        declared = entry.get("username")
        if isinstance(declared, str) and declared.lower() != username.lower():
            raise RegistryError(
                f"{sid}: username '{declared}' does not match profile_url '{url}'"
            )
        if username.lower() in seen_usernames:
            raise RegistryError(
                f"{sid}: username '{username}' already registered as "
                f"{seen_usernames[username.lower()]}"
            )
        seen_usernames[username.lower()] = sid

        max_items = entry.get("max_items", defaults.get("max_items", MAX_ITEMS_HARD_CAP))
        if not isinstance(max_items, int) or isinstance(max_items, bool):
            raise RegistryError(f"{sid}: max_items must be an integer, got {max_items!r}")
        if not 1 <= max_items <= MAX_ITEMS_HARD_CAP:
            raise RegistryError(
                f"{sid}: max_items {max_items} outside 1..{MAX_ITEMS_HARD_CAP} "
                f"(hard cap per SPEC-ING-001 §2)"
            )

        sources.append(
            Source(
                source_id=sid,
                platform=platform,
                username=username,
                profile_url=_canonical_url(username),
                enabled=bool(entry.get("enabled", True)),
                max_items=max_items,
                added_at=entry.get("added_at"),
                notes=entry.get("notes"),
                extra={
                    k: v
                    for k, v in entry.items()
                    if k not in {
                        "source_id", "platform", "username", "profile_url",
                        "enabled", "max_items", "added_at", "notes",
                    }
                },
            )
        )
    return sources, defaults


def _canonical_url(username: str) -> str:
    return f"https://www.instagram.com/{username}/"


def next_source_id(sources: list[Source], platform: str = "instagram") -> str:
    """Allocate the next free ID for a platform, e.g. IG033 after IG032."""
    prefix = "IG" if platform == "instagram" else platform[:2].upper() + "X"
    used = {s.source_id for s in sources if s.source_id.startswith(prefix)}
    n = 1
    while f"{prefix}{n:03d}" in used:
        n += 1
    return f"{prefix}{n:03d}"


def add_source(
    url: str,
    *,
    enabled: bool = True,
    max_items: int | None = None,
    notes: str | None = None,
    path: Path | str | None = None,
) -> Source:
    """Register a new source by URL. The next `extract` run includes it."""
    p = Path(path) if path is not None else REGISTRY_PATH
    sources, defaults = load_registry(p)
    username = _parse_profile_url("instagram", url, "new-source")
    if any(s.username.lower() == username.lower() for s in sources):
        raise RegistryError(f"'{username}' is already registered")

    eff_max = (
        MAX_ITEMS_HARD_CAP
        if max_items is None
        else max_items
    )
    if not 1 <= eff_max <= MAX_ITEMS_HARD_CAP:
        raise RegistryError(f"max_items {eff_max} outside 1..{MAX_ITEMS_HARD_CAP}")

    sid = next_source_id(sources, "instagram")
    entry = {
        "source_id": sid,
        "platform": "instagram",
        "username": username,
        "profile_url": _canonical_url(username),
        "enabled": enabled,
        "max_items": eff_max,
        "added_at": _today(),
    }
    if notes:
        entry["notes"] = notes

    doc = json.loads(p.read_text(encoding="utf-8"))
    doc.setdefault("sources", []).append(entry)
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return Source(
        source_id=sid,
        platform="instagram",
        username=username,
        profile_url=_canonical_url(username),
        enabled=enabled,
        max_items=eff_max,
        added_at=entry["added_at"],
        notes=notes,
    )


def _today() -> str:
    from datetime import date

    return date.today().isoformat()
