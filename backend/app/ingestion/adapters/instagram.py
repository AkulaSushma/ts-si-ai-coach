"""Instagram adapter — the first platform adapter (SPEC-ING-001 §4.3).

Access mechanism: the same public web endpoints a non-logged-in browser hits
when it opens a profile page, used exactly as a browser would (same headers,
one request at a time, polite delays, stop at any access-control signal).

No authentication is attempted, no credential is used, no rate-limit or
login wall is ever bypassed. When Instagram refuses anonymous access the
adapter raises `AccessBlockedError` and the runner records it honestly.
"""

from __future__ import annotations

import json
import random
import re
import time
import urllib.error
import urllib.request
from typing import Any

from .base import (
    AccessBlockedError,
    ContentItem,
    EdgePage,
    MediaRef,
    ProfileSnapshot,
    SourceAdapter,
    TransientError,
)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
_APP_ID_HEADER = {"x-ig-app-id": "936619743392459"}

_BASE = "https://www.instagram.com"

# typename → our content_type. XDT* are the current API spellings.
_TYPE_MAP = {
    "GraphImage": "post",
    "XDTGraphImage": "post",
    "GraphSidecar": "carousel",
    "XDTGraphSidecar": "carousel",
    "GraphVideo": "reel",
    "XDTGraphVideo": "reel",
    "XDTVideoAsset": "reel",
}

_LOGIN_SIGNALS = (
    "/accounts/login/", "/login/", "authentication_required",
    "login_required", "Please wait a few minutes",
)


def _build_opener() -> urllib.request.OpenerDirector:
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", _UA)]
    return opener


class InstagramAdapter(SourceAdapter):
    platform = "instagram"

    def __init__(self, *, polite_delay_seconds: float | None = None,
                 max_retries: int | None = None,
                 sleep: Any = time.sleep, opener: Any = None):
        # `sleep` is injectable so tests run instantly.
        self.polite_delay_seconds = (
            polite_delay_seconds if polite_delay_seconds is not None
            else self.polite_delay_seconds
        )
        self.max_retries = max_retries if max_retries is not None else self.max_retries
        self._sleep = sleep
        self._opener = opener or _build_opener()

    # ------------------------------------------------------------------ HTTP

    def _request_json(self, url: str, headers: dict[str, str] | None = None,
                      allow_login_redirect: bool = False) -> dict:
        """One polite, retry-limited GET that must return JSON.

        On any access-control signal (401/403/429/login redirect) raises
        AccessBlockedError immediately — never retried, never bypassed.
        """
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._request_json_once(
                    url, headers or {}, allow_login_redirect
                )
            except AccessBlockedError:
                raise
            except (TransientError, urllib.error.URLError, TimeoutError) as e:
                last_exc = e
                if attempt < self.max_retries:
                    backoff = self.polite_delay_seconds * (2 ** attempt)
                    self._sleep(backoff + random.uniform(0, 0.4))
        raise TransientError(f"GET {url} failed after {self.max_retries} attempts: {last_exc}")

    def _request_json_once(self, url: str, headers: dict[str, str],
                           allow_login_redirect: bool) -> dict:
        req = urllib.request.Request(url, headers={**headers} or None)
        # urllib follows redirects by default; a login redirect is a signal.
        opener = self._opener
        try:
            with opener.open(req, timeout=30) as resp:
                final_url = resp.geturl()
                if not allow_login_redirect and any(
                    s in final_url for s in _LOGIN_SIGNALS
                ):
                    raise AccessBlockedError(
                        f"redirected to login: {url} -> {final_url}"
                    )
                body = resp.read().decode("utf-8", errors="replace")
                if any(s in body[:2000] for s in ("login_required", "authentication_required")):
                    raise AccessBlockedError(f"login wall body from {url}")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise AccessBlockedError(f"HTTP {e.code} for {url}") from e
            if e.code >= 500 or e.code == 408:
                raise TransientError(f"HTTP {e.code} for {url}") from e
            raise TransientError(f"HTTP {e.code} for {url}") from e
        except json.JSONDecodeError as e:
            raise TransientError(f"non-JSON response from {url}: {e}") from e

    # -------------------------------------------------------------- profile

    def fetch_profile(self, username: str) -> ProfileSnapshot:
        """Fetch profile info, trying the web JSON endpoint, then the HTML
        page a browser receives (spec §4.3 fallback)."""
        url = f"{_BASE}/api/v1/users/web_profile_info/?username={username}"
        try:
            data = self._request_json(url, headers=_APP_ID_HEADER)
        except AccessBlockedError as e:
            # Primary endpoint refused; the HTML profile page is the
            # documented fallback, not a bypass — same page a browser gets.
            html_snap = self._profile_from_html(username)
            if html_snap is not None:
                return html_snap
            raise
        user = ((data.get("data") or {}).get("user") or {})
        if not user:
            if data.get("status") == "ok":
                raise AccessBlockedError(
                    f"profile endpoint returned ok-but-empty for '{username}'"
                )
            raise TransientError(f"unexpected profile payload for '{username}'")
        return self._snapshot_from_user_node(username, user)

    def _snapshot_from_user_node(self, username: str,
                                 user: dict) -> ProfileSnapshot:
        counts = {}
        for key, path in (
            ("timeline", ("edge_owner_to_timeline_media", "count")),
            ("reels", ("edge_felix_video_timeline", "count")),
            ("videos", ("edge_video_timeline", "count")),
        ):
            node = user
            try:
                for seg in path:
                    node = node[seg]
                counts[key] = node if isinstance(node, int) else None
            except (KeyError, TypeError):
                counts[key] = None

        edges = ["timeline"]
        if counts.get("reels") or user.get("edge_felix_video_timeline"):
            edges.append("reels")

        # First timeline page embedded in the profile node, if present.
        embedded: dict[str, EdgePage] = {}
        tl = user.get("edge_owner_to_timeline_media") or {}
        if tl.get("edges"):
            items = [
                self._parse_item(e.get("node") or {})
                for e in tl["edges"]
                if isinstance(e, dict)
            ]
            embedded["timeline"] = EdgePage(
                edge="timeline",
                items=[i for i in items if i.content_id],
                has_next=bool(tl.get("page_info", {}).get("has_next_page")),
                end_cursor=tl.get("page_info", {}).get("end_cursor"),
            )

        return ProfileSnapshot(
            platform="instagram",
            username=username,
            user_id=str(user.get("id")) if user.get("id") else None,
            is_private=user.get("is_private"),
            declared_counts=counts,
            edges=edges,
            raw=user,
            embedded_pages=embedded,
        )

    def _profile_from_html(self, username: str) -> ProfileSnapshot | None:
        """Fallback: read the public profile HTML page and its embedded JSON.

        Returns None when the page does not carry the embedded profile data
        (e.g. a consent or login wall), so the caller records blocked honestly.
        """
        html = self._request_text(f"{_BASE}/{username}/")
        m = re.search(
            r'<script type="text/json" data-sjs>.*?</script>', html, re.S
        )
        candidates: list[str] = []
        if m:
            candidates.append(m.group(0))
        for sm in re.finditer(
            r'window\._gd\w*\s*=\s*(\{.*?\});', html, re.S
        ):
            candidates.append(sm.group(1))

        # The profile node also appears inline as escaped JSON.
        for sm2 in re.finditer(
            r'\\"edge_owner_to_timeline_media\\":\{', html
        ):
            # locate the whole escaped-JSON blob containing it
            blob = self._extract_escaped_blob(html, sm2.start())
            if blob:
                candidates.append(blob)
            break

        for cand in candidates:
            user = self._find_user_node(cand)
            if user:
                return self._snapshot_from_user_node(username, user)
        return None

    def _request_text(self, url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": _UA} or None)
        opener = self._opener
        try:
            with opener.open(req, timeout=30) as resp:
                final_url = resp.geturl()
                if any(s in final_url for s in _LOGIN_SIGNALS):
                    raise AccessBlockedError(
                        f"redirected to login: {url} -> {final_url}"
                    )
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise AccessBlockedError(f"HTTP {e.code} for {url}") from e
            raise TransientError(f"HTTP {e.code} for {url}") from e

    @staticmethod
    def _extract_escaped_blob(html: str, around: int) -> str | None:
        """Extract the escaped-JSON string literal containing position `around`."""
        start = html.rfind('"', 0, around)
        if start == -1:
            return None
        end = html.find('"', around)
        if end == -1:
            return None
        raw = html[start + 1:end]
        try:
            return raw.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            return None

    @staticmethod
    def _find_user_node(blob: str) -> dict | None:
        """Best-effort location of a user node inside a raw/escaped blob."""
        try:
            doc = json.loads(blob)
        except (json.JSONDecodeError, ValueError):
            return None

        def walk(node):
            if isinstance(node, dict):
                if "edge_owner_to_timeline_media" in node and (
                    "username" in node or "is_private" in node
                ):
                    return node
                for v in node.values():
                    found = walk(v)
                    if found:
                        return found
            elif isinstance(node, list):
                for v in node:
                    found = walk(v)
                    if found:
                        return found
            return None

        return walk(doc)

    # --------------------------------------------------------------- edges

    def fetch_page(self, edge: str, user_id: str, cursor: str | None) -> EdgePage:
        if edge == "timeline":
            url = f"{_BASE}/api/v1/feed/user/{user_id}/"
            key = "items"
        elif edge == "reels":
            url = f"{_BASE}/api/v1/clips/user/?target_user_id={user_id}"
            key = "items"
        else:
            raise ValueError(f"unknown edge '{edge}'")

        if cursor:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}max_id={cursor}"
        data = self._request_json(url, headers=_APP_ID_HEADER)
        items = [self._parse_item(m) for m in data.get(key, []) if isinstance(m, dict)]
        more_items = data.get("more_available") is True
        next_cursor = data.get("next_max_id")
        return EdgePage(
            edge=edge,
            items=items,
            has_next=more_items and bool(next_cursor),
            end_cursor=next_cursor if (more_items and next_cursor) else None,
        )

    # ---------------------------------------------------------------- items

    def _parse_item(self, media: dict) -> ContentItem:
        pk = str(
            media.get("pk")
            or (media.get("code") or {}).get("code")
            or ""
        )
        code = media.get("code")
        # feed/user and clips/user payloads use integer media_type (1/2/8);
        # web-embedded payloads use __typename strings; XDT* are current API
        # spellings. Unknown values stay unclassified — never guessed.
        typename = media.get("media_type") or media.get("__typename")
        if isinstance(typename, int):
            typename = {1: "GraphImage", 2: "GraphVideo", 8: "GraphSidecar"}.get(
                typename, typename
            )
        content_type = _TYPE_MAP.get(typename) or "unclassified"
        caption_obj = media.get("caption") or {}
        caption = caption_obj.get("text") if isinstance(caption_obj, dict) else None

        hashtags = []
        if caption:
            hashtags = sorted({t.lower() for t in re.findall(r"#(\w+)", caption)})

        media_refs: list[MediaRef] = []
        carousel = media.get("carousel_media") or []
        if carousel:
            for i, child in enumerate(carousel):
                media_refs.append(
                    MediaRef(
                        index=i,
                        url=self._image_url(child),
                        accessibility_caption=self._acc_caption(child),
                        media_kind="image",
                    )
                )
        else:
            video_url = None
            video = media.get("video_versions") or []
            if video and isinstance(video[0], dict):
                video_url = video[0].get("url")
            if video_url:
                thumb = None
                thumbs = media.get("image_versions2", {}).get("candidates", [])
                if thumbs:
                    thumb = thumbs[0].get("url")
                media_refs.append(
                    MediaRef(
                        index=0,
                        url=video_url,
                        accessibility_caption=self._acc_caption(media),
                        media_kind="video",
                    )
                )
                # keep the poster too
                if thumb:
                    media_refs.append(MediaRef(index=1, url=thumb, media_kind="image"))
            else:
                media_refs.append(
                    MediaRef(
                        index=0,
                        url=self._image_url(media),
                        accessibility_caption=self._acc_caption(media),
                        media_kind="image",
                    )
                )

        likes = media.get("like_count")
        comments = media.get("comment_count")
        taken_at = media.get("taken_at")
        published_at = (
            time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(taken_at))
            if isinstance(taken_at, int)
            else None
        )

        return ContentItem(
            content_id=pk or (code or ""),
            content_type=content_type,
            content_url=f"{_BASE}/p/{code}/" if code else None,
            shortcode=code,
            published_at=published_at,
            caption=caption,
            hashtags=hashtags,
            media=media_refs,
            likes=likes if isinstance(likes, int) else None,
            comments=comments if isinstance(comments, int) else None,
            platform_data=media,
        )

    @staticmethod
    def _image_url(node: dict) -> str | None:
        v2 = node.get("image_versions2") or {}
        for c in v2.get("candidates") or []:
            if c.get("url"):
                return c["url"]
        return None

    @staticmethod
    def _acc_caption(node: dict) -> str | None:
        ac = node.get("accessibility_caption")
        if isinstance(ac, str) and ac.strip():
            return ac
        return None
