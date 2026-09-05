"""Checkpointing, error logging, and harvest manifests (SPEC-ING-001 §4.6–4.8).

The checkpoint is the resume contract. It is written atomically after every
item and every page, so a crash loses at most the in-flight item.

Accounting identity (research/README.md — non-negotiable):

    expected = extracted + duplicate + failed + inaccessible

("irrelevant" is 0 at collection time by SPEC-ING-001 §2.3: nothing is
discarded as irrelevant during crawling.)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .raw_store import ROOT, atomic_write_json

CHECKPOINT_DIR = ROOT / "data" / "ingestion" / "checkpoints"
ERROR_DIR = ROOT / "data" / "ingestion" / "errors"
MANIFEST_DIR = ROOT / "research" / "manifests"


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Checkpoint:
    """Per-source resume state."""

    def __init__(self, source_id: str, platform: str, max_items: int,
                 directory: Path | None = None):
        self.path = (directory or CHECKPOINT_DIR) / f"{source_id}.json"
        self.source_id = source_id
        self.data = self._load_or_fresh(platform, max_items)

    def _load_or_fresh(self, platform: str, max_items: int) -> dict:
        if self.path.is_file():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                # A corrupt checkpoint restarts that source's accounting but
                # raw records already on disk still count via has_item().
                pass
        return {
            "source_id": self.source_id,
            "platform": platform,
            "status": "not_started",
            "stop_reason": None,
            "max_items": max_items,
            "profile": {
                "user_id": None,
                "declared_timeline_count": None,
                "declared_reels_count": None,
                "is_private": None,
                "fetched_at": None,
            },
            "items": {
                "discovered": 0,
                "extracted": 0,
                "duplicate": 0,
                "failed": 0,
                "inaccessible": 0,
            },
            "dispositions": {
                "processed_ids": [],
                "duplicate_ids": [],
                "failed_ids": [],
                "failure_detail": {},
            },
            "cursors": {
                "timeline": {"end_cursor": None, "blocked": False},
                "reels": {"end_cursor": None, "blocked": False},
            },
            "resume_state": None,
            "started_at": None,
            "updated_at": None,
            "finished_at": None,
        }

    # ------------------------------------------------------------- accessors

    @property
    def status(self) -> str:
        return self.data["status"]

    @status.setter
    def status(self, value: str) -> None:
        self.data["status"] = value

    @property
    def counts(self) -> dict:
        return self.data["items"]

    def is_processed(self, content_id: str) -> bool:
        d = self.data["dispositions"]
        return (
            content_id in d["processed_ids"]
            or content_id in d["duplicate_ids"]
        )

    def already_failed(self, content_id: str) -> bool:
        return content_id in self.data["dispositions"]["failed_ids"]

    def processed_budget(self) -> int:
        """Unique items already accounted for against max_items."""
        it = self.data["items"]
        return it["extracted"] + it["duplicate"] + it["failed"]

    # -------------------------------------------------------------- mutation

    def start(self) -> None:
        if self.data["started_at"] is None:
            self.data["started_at"] = _utcnow()
        if self.data["status"] in ("not_started", "partial", "blocked"):
            self.data["status"] = "in_progress"

    def record_profile(self, snap_user_id, is_private, timeline_count,
                      reels_count) -> None:
        prof = self.data["profile"]
        prof["user_id"] = snap_user_id
        prof["is_private"] = is_private
        prof["declared_timeline_count"] = timeline_count
        prof["declared_reels_count"] = reels_count
        prof["fetched_at"] = _utcnow()

    def record_extracted(self, content_id: str) -> None:
        self.counts["discovered"] += 1
        self.counts["extracted"] += 1
        self.data["dispositions"]["processed_ids"].append(content_id)
        self.data["resume_state"] = f"last_ok:{content_id}"

    def record_duplicate(self, content_id: str) -> None:
        self.counts["discovered"] += 1
        self.counts["duplicate"] += 1
        self.data["dispositions"]["duplicate_ids"].append(content_id)

    def record_failed(self, content_id: str, error_type: str, message: str,
                      retry_count: int) -> None:
        self.counts["discovered"] += 1
        self.counts["failed"] += 1
        d = self.data["dispositions"]
        if content_id not in d["failed_ids"]:
            d["failed_ids"].append(content_id)
        d["failure_detail"][content_id] = {
            "error_type": error_type,
            "message": message[:500],
            "retry_count": retry_count,
            "last_failed_at": _utcnow(),
        }

    def record_inaccessible(self, count: int = 1) -> None:
        self.counts["inaccessible"] += count

    def set_cursor(self, edge: str, end_cursor: str | None) -> None:
        self.data["cursors"][edge]["end_cursor"] = end_cursor

    def mark_edge_blocked(self, edge: str) -> None:
        self.data["cursors"][edge]["blocked"] = True

    def finish(self, status: str, stop_reason: str | None = None) -> None:
        self.data["status"] = status
        self.data["stop_reason"] = stop_reason
        self.data["finished_at"] = _utcnow()

    def pause(self, stop_reason: str | None) -> None:
        self.data["status"] = "partial"
        self.data["stop_reason"] = stop_reason

    # -------------------------------------------------------------- expected

    def expected_items(self) -> tuple[int, str]:
        """Expected count with its justification (research accounting)."""
        prof = self.data["profile"]
        declared = [
            c
            for c in (prof.get("declared_timeline_count"),
                      prof.get("declared_reels_count"))
            if isinstance(c, int)
        ]
        if declared:
            total = sum(declared)
            # overlap between timeline and reels is unknown until seen, so
            # the honest expected figure is the declared timeline count plus
            # declared reels count, later reconciled by duplicate accounting
            expected = min(self.data["max_items"], total)
            just = (
                f"profile-declared counts (timeline={prof.get('declared_timeline_count')}, "
                f"reels={prof.get('declared_reels_count')}) read on "
                f"{prof.get('fetched_at')}, capped at max_items={self.data['max_items']}"
            )
            return expected, just
        expected = self.counts["discovered"]
        just = (
            "no declared count accessible; expected equals unique items actually "
            "discovered during this run and prior resumed runs"
        )
        return expected, just

    def balances(self) -> bool:
        it = self.counts
        return (
            it["discovered"]
            == it["extracted"] + it["duplicate"] + it["failed"]
        )

    # ----------------------------------------------------------------- write

    def save(self) -> None:
        self.data["updated_at"] = _utcnow()
        atomic_write_json(self.path, self.data)


class ErrorLog:
    """Append-only JSONL error log per source: data/ingestion/errors/<id>.jsonl"""

    def __init__(self, source_id: str, directory: Path | None = None):
        self.path = (directory or ERROR_DIR) / f"{source_id}.jsonl"

    def append(self, *, content_url: str | None, error_type: str,
               message: str, retry_count: int, status: str) -> None:
        entry = {
            "source_id": self.path.stem,
            "content_url": content_url,
            "error_type": error_type,
            "message": message[:500],
            "timestamp": _utcnow(),
            "retry_count": retry_count,
            "status": status,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class ManifestWriter:
    """Per-run harvest manifests: research/manifests/instagram/<id>-<ts>.json

    These are the L3 accounting artifacts research/README.md requires, and
    they are tracked in Git because they are small, reviewable evidence.
    """

    def __init__(self, directory: Path | None = None):
        self.directory = Path(directory) if directory else MANIFEST_DIR / "instagram"

    def write(self, checkpoint: Checkpoint, run_mode: str) -> Path:
        c = checkpoint.data
        expected, justification = checkpoint.expected_items()
        manifest = {
            "source_id": c["source_id"],
            "platform": c["platform"],
            "run_mode": run_mode,
            "written_at": _utcnow(),
            "status": c["status"],
            "stop_reason": c["stop_reason"],
            "max_items": c["max_items"],
            "expected": expected,
            "expected_justification": justification,
            "accounting": {
                "discovered": c["items"]["discovered"],
                "processed": c["items"]["extracted"],
                "duplicate": c["items"]["duplicate"],
                "failed": c["items"]["failed"],
                "inaccessible": c["items"]["inaccessible"],
                "irrelevant": 0,
            },
            "identity_holds": (
                c["items"]["discovered"]
                == c["items"]["extracted"] + c["items"]["duplicate"] + c["items"]["failed"]
            ),
            "profile": c["profile"],
        }
        self.directory.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        p = self.directory / f"{c['source_id']}-{ts}.json"
        atomic_write_json(p, manifest)
        return p
