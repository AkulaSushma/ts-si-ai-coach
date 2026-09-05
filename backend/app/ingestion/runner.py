"""Platform-agnostic extraction runner (SPEC-ING-001 §4.9).

Responsibilities:
- walk each source's edges one page at a time
- enforce the per-source max_items cap (299 default, hard cap 299)
- deduplicate by content_id within and across edges (timeline ∩ reels)
- checkpoint after every item and page (crash-safe resume)
- isolate failures: one item never stops a profile; one profile never stops
  the batch
- stop honestly at any access-control signal (AccessBlockedError)

The runner never restarts completed work: a source whose checkpoint status is
`complete` is skipped unless force=True; already-dispositioned items are
skipped on resume.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path

from .adapters import get_adapter
from .adapters.base import AccessBlockedError, AdapterError, SourceAdapter
from .registry import Source
from .storage import Checkpoint, ErrorLog, ManifestWriter, NormalizedStore, RawStore
from .taxonomy import MAX_ITEMS_HARD_CAP


@dataclass
class RunSummary:
    source_id: str
    status: str
    stop_reason: str | None
    discovered: int
    extracted: int
    duplicate: int
    failed: int
    inaccessible: int
    manifest_path: str | None


class IngestionRunner:
    def __init__(self, *, raw_store: RawStore | None = None,
                 normalized_store: NormalizedStore | None = None,
                 manifest_writer: ManifestWriter | None = None,
                 checkpoint_dir: Path | None = None,
                 error_dir: Path | None = None,
                 adapter_factory=None,
                 sleep=time.sleep):
        self.raw = raw_store or RawStore()
        self.normalized = normalized_store or NormalizedStore()
        self.manifests = manifest_writer or ManifestWriter()
        self.checkpoint_dir = checkpoint_dir
        self.error_dir = error_dir
        # adapter_factory(platform) -> SourceAdapter; overrides get_adapter.
        # Used by tests so no test ever makes a network request.
        self.adapter_factory = adapter_factory
        self._sleep = sleep   # injectable for instant tests

    def _adapter_for(self, source: Source) -> SourceAdapter:
        if self.adapter_factory is not None:
            return self.adapter_factory(source)
        return get_adapter(source.platform)

    def _new_checkpoint(self, source: Source) -> Checkpoint:
        return Checkpoint(
            source.source_id, source.platform, source.max_items,
            directory=self.checkpoint_dir,
        )

    def _new_error_log(self, source: Source) -> ErrorLog:
        return ErrorLog(source.source_id, directory=self.error_dir)

    # ------------------------------------------------------------- one item

    def _process_item(self, adapter: SourceAdapter, source: Source,
                      item, cp: Checkpoint, errors: ErrorLog,
                      this_run: set) -> str:
        """Disposition one item. Returns stored|duplicate|failed|skipped|capped.

        `this_run` holds content_ids already dispositioned during the current
        run. A re-encounter of an item dispositioned *this run* is a genuine
        duplicate (cross-edge overlap or re-listing) and counts as one. A
        re-encounter of an item dispositioned in a *prior* run is resume
        overlap: already accounted, so skipped without recounting.
        """
        cid = item.content_id
        if cp.is_processed(cid) or cid in cp.data["dispositions"]["failed_ids"]:
            if cid in this_run:
                cp.record_duplicate(cid)
                cp.save()
                return "duplicate"
            return "skipped"

        # hard safety: never exceed the cap even if a page lied
        if cp.counts["extracted"] + cp.counts["duplicate"] + cp.counts["failed"] >= source.max_items:
            return "capped"

        if self.raw.has_item(source.platform, source.source_id, cid):
            # crash between raw write and checkpoint save — count it, don't rewrite
            this_run.add(cid)
            cp.record_duplicate(cid)
            cp.save()
            return "duplicate"

        for attempt in range(1, adapter.max_retries + 1):
            try:
                enriched = adapter.fetch_item(item)
                path, stored = self.raw.store_item(
                    source.source_id, source.platform, source.username, enriched
                )
                if stored:
                    # normalize immediately after raw persistence
                    self.normalized.store(
                        self._read_json(path), source.source_id
                    )
                    this_run.add(cid)
                    cp.record_extracted(cid)
                    cp.save()
                    return "stored"
                this_run.add(cid)
                cp.record_duplicate(cid)
                cp.save()
                return "duplicate"
            except AccessBlockedError as e:
                errors.append(
                    content_url=item.content_url, error_type="access_blocked",
                    message=str(e), retry_count=attempt, status="blocked",
                )
                cp.record_failed(cid, "access_blocked", str(e), attempt)
                cp.save()
                raise
            except (AdapterError, OSError, ValueError) as e:
                if attempt < adapter.max_retries:
                    backoff = adapter.polite_delay_seconds * (2 ** attempt)
                    self._sleep(backoff + random.uniform(0, 0.4))
                    continue
                errors.append(
                    content_url=item.content_url,
                    error_type=type(e).__name__,
                    message=str(e), retry_count=attempt, status="failed",
                )
                this_run.add(cid)
                cp.record_failed(cid, type(e).__name__, str(e), attempt)
                cp.save()
                return "failed"
        # unreachable: the loop either returns or raises
        return "failed"

    @staticmethod
    def _read_json(path):
        import json

        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ---------------------------------------------------------- one profile

    def extract_source(self, source: Source, *, force: bool = False,
                       adapter: SourceAdapter | None = None) -> RunSummary:
        if adapter is None:
            adapter = self._adapter_for(source)

        cp = self._new_checkpoint(source)
        errors = self._new_error_log(source)

        if cp.status == "complete" and not force:
            m = self.manifests.write(cp, "skip_completed")
            return self._summary(cp, m)

        cp.start()
        cp.save()

        try:
            snap = adapter.fetch_profile(source.username)
        except AccessBlockedError as e:
            errors.append(
                content_url=source.profile_url, error_type="access_blocked",
                message=str(e), retry_count=0, status="blocked",
            )
            if cp.counts["extracted"] > 0:
                cp.pause(f"profile access blocked after partial extraction: {e}")
            else:
                cp.record_inaccessible(0)
                cp.finish("blocked", f"anonymous access refused: {e}")
            cp.save()
            m = self.manifests.write(cp, "extract")
            return self._summary(cp, m)
        except AdapterError as e:
            cp.pause(f"profile fetch error: {e}")
            cp.save()
            errors.append(
                content_url=source.profile_url, error_type=type(e).__name__,
                message=str(e), retry_count=0, status="partial",
            )
            m = self.manifests.write(cp, "extract")
            return self._summary(cp, m)

        cp.record_profile(
            snap.user_id,
            snap.is_private,
            snap.declared_counts.get("timeline"),
            snap.declared_counts.get("reels"),
        )
        self.raw.store_profile(source.platform, source.source_id, snap)
        cp.save()

        if snap.is_private:
            cp.finish(
                "blocked",
                "profile is private; no content is publicly accessible",
            )
            cp.save()
            m = self.manifests.write(cp, "extract")
            return self._summary(cp, m)

        budget_used = 0
        blocked_edges: list[str] = []
        this_run: set = set()

        # Pages embedded in the profile response itself (spec §4.3 fallback):
        # consume them before any separate page fetch. They still respect
        # max_items, dedup, and checkpointing exactly like fetched pages.
        for edge, page in (snap.embedded_pages or {}).items():
            for item in page.items:
                if cp.processed_budget() >= source.max_items:
                    break
                if not item.content_id:
                    continue
                try:
                    self._process_item(adapter, source, item, cp, errors,
                                       this_run)
                except AccessBlockedError:
                    blocked_edges.append(edge)
                    cp.mark_edge_blocked(edge)
                    cp.record_inaccessible(1)
                    cp.save()
                    break
            if page.end_cursor:
                cp.set_cursor(edge, page.end_cursor)
            cp.save()

        for edge in snap.edges:
            cursor = cp.data["cursors"].get(edge, {}).get("end_cursor")
            edge_blocked_previously = cp.data["cursors"].get(edge, {}).get("blocked", False)
            pages = 0
            while True:
                if cp.processed_budget() >= source.max_items:
                    break
                if pages >= 60:   # defensive page ceiling per edge per run
                    break
                try:
                    page = adapter.fetch_page(edge, snap.user_id, cursor)
                except AccessBlockedError as e:
                    errors.append(
                        content_url=source.profile_url,
                        error_type="access_blocked",
                        message=f"{edge} pagination blocked: {e}",
                        retry_count=0, status="blocked",
                    )
                    blocked_edges.append(edge)
                    cp.mark_edge_blocked(edge)
                    cp.record_inaccessible(1)   # the page we could not read
                    cp.save()
                    break
                except (AdapterError, OSError) as e:
                    errors.append(
                        content_url=source.profile_url,
                        error_type=type(e).__name__,
                        message=f"{edge} page error: {e}",
                        retry_count=0, status="partial",
                    )
                    cp.pause(f"{edge} page error: {e}")
                    cp.save()
                    blocked_edges.append(edge)
                    break

                for item in page.items:
                    if cp.processed_budget() >= source.max_items:
                        break
                    if not item.content_id:
                        continue
                    try:
                        self._process_item(adapter, source, item, cp, errors,
                                           this_run)
                    except AccessBlockedError:
                        # per-item access block stops the whole edge honestly
                        blocked_edges.append(edge)
                        cp.mark_edge_blocked(edge)
                        cp.record_inaccessible(1)
                        cp.save()
                        break
                pages += 1
                cp.set_cursor(edge, page.end_cursor)
                cp.save()
                if not page.has_next:
                    break
                cursor = page.end_cursor
                self._sleep(
                    adapter.polite_delay_seconds
                    + random.uniform(0, adapter.polite_delay_seconds * 0.3)
                )

        if cp.processed_budget() >= source.max_items:
            cp.finish("complete", f"reached max_items={source.max_items}")
        elif blocked_edges and not edge_blocked_previously and cp.counts["extracted"] == 0:
            cp.finish(
                "blocked",
                f"pagination blocked on edges {blocked_edges} before any item was stored",
            )
        elif blocked_edges:
            cp.pause(
                f"pagination blocked on edges {blocked_edges}; "
                f"{cp.counts['extracted']} items stored so far; resumable"
            )
        else:
            cp.finish("complete", "all accessible pages walked")
        cp.save()
        m = self.manifests.write(cp, "extract")
        return self._summary(cp, m)

    # ------------------------------------------------------------ batch

    def extract_many(self, sources: list[Source], *, force: bool = False,
                     stop_on_blocked: bool = False) -> list[RunSummary]:
        summaries: list[RunSummary] = []
        for s in sources:
            try:
                summaries.append(self.extract_source(s, force=force))
            except Exception as e:   # a profile failure never kills the batch
                errors = self._new_error_log(s)
                errors.append(
                    content_url=s.profile_url, error_type=type(e).__name__,
                    message=str(e), retry_count=0, status="failed",
                )
                cp = self._new_checkpoint(s)
                if cp.status == "not_started":
                    cp.finish("blocked", f"unexpected error: {e}")
                else:
                    cp.pause(f"unexpected error: {e}")
                cp.save()
                self.manifests.write(cp, "extract")
                summaries.append(self._summary(cp, None))
                if stop_on_blocked:
                    break
        return summaries

    def _summary(self, cp: Checkpoint, manifest_path) -> RunSummary:
        it = cp.counts
        return RunSummary(
            source_id=cp.source_id,
            status=cp.status,
            stop_reason=cp.data["stop_reason"],
            discovered=it["discovered"],
            extracted=it["extracted"],
            duplicate=it["duplicate"],
            failed=it["failed"],
            inaccessible=it["inaccessible"],
            manifest_path=str(manifest_path) if manifest_path else None,
        )
