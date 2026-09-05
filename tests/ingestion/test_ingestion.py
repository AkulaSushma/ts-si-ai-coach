"""L1 ingestion tests: registry, URL validation, limits, dedup, checkpoint/
resume, failure recovery, raw persistence, new-source registration.

These use the FakeAdapter (no network) so they are deterministic and instant.
The live single-source test is a separate, manual step by instruction.
Standard library unittest only (D-0006). Run from the project folder:

    python -m unittest discover -s tests -v
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.ingestion.adapters.base import (  # noqa: E402
    AccessBlockedError, MediaRef,
)
from app.ingestion.registry import (  # noqa: E402
    RegistryError, add_source, load_registry, next_source_id,
)
from app.ingestion.runner import IngestionRunner  # noqa: E402
from app.ingestion.storage import (  # noqa: E402
    Checkpoint, ErrorLog, ManifestWriter, NormalizedStore, RawStore,
)
from app.ingestion.taxonomy import MAX_ITEMS_HARD_CAP  # noqa: E402
from app.ingestion.cli import main as cli_main  # noqa: E402

from ._fake_adapter import FakeAdapter, TmpDirs, make_item  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def make_source(source_id="IG900", platform="instagram", username="testuser",
                max_items=299, enabled=True):
    from app.ingestion.registry import Source

    return Source(source_id=source_id, platform=platform, username=username,
                  profile_url=f"https://www.instagram.com/{username}/",
                  enabled=enabled, max_items=max_items)


def make_runner(dirs, **kwargs) -> IngestionRunner:
    return IngestionRunner(
        raw_store=RawStore(base=dirs["raw"]),
        normalized_store=NormalizedStore(base=dirs["normalized"]),
        manifest_writer=ManifestWriter(directory=dirs["manifests"]),
        checkpoint_dir=dirs["checkpoints"],
        error_dir=dirs["errors"],
        sleep=lambda s: None,
    )


class TestRegistryLoading(unittest.TestCase):
    def test_real_registry_loads_32_unique_sources(self):
        sources, defaults = load_registry()
        self.assertEqual(len(sources), 32)
        self.assertEqual(len({s.source_id for s in sources}), 32)
        self.assertEqual(len({s.username.lower() for s in sources}), 32)
        self.assertEqual(defaults["max_items"], 299)
        self.assertTrue(all(s.max_items <= 299 for s in sources))

    def test_sudheergenzacademy_stored_once(self):
        sources, _ = load_registry()
        hits = [s for s in sources if s.username == "sudheergenzacademy"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].source_id, "IG021")

    def test_every_profile_url_matches_its_username(self):
        for s in load_registry()[0]:
            self.assertEqual(
                s.profile_url, f"https://www.instagram.com/{s.username}/"
            )

    def test_dotted_username_allowed(self):
        sources, _ = load_registry()
        dotted = [s for s in sources if "." in s.username]
        self.assertTrue(dotted, "registry contains dotted usernames")

    def test_max_items_above_cap_rejected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "registry.json"
            p.write_text(json.dumps({
                "defaults": {"max_items": 299},
                "sources": [{
                    "source_id": "IG001", "platform": "instagram",
                    "username": "a", "profile_url": "https://www.instagram.com/a/",
                    "enabled": True, "max_items": 300,
                }],
            }), encoding="utf-8")
            with self.assertRaises(RegistryError):
                load_registry(p)

    def test_duplicate_username_rejected(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "registry.json"
            p.write_text(json.dumps({
                "sources": [
                    {"source_id": "IG001", "platform": "instagram",
                     "username": "same", "profile_url": "https://www.instagram.com/same/"},
                    {"source_id": "IG002", "platform": "instagram",
                     "username": "same", "profile_url": "https://www.instagram.com/same/"},
                ],
            }), encoding="utf-8")
            with self.assertRaises(RegistryError):
                load_registry(p)


class TestURLValidation(unittest.TestCase):
    """Acceptance criterion 2: URL validation."""

    def _check(self, url):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            p.write_text(json.dumps({
                "sources": [{"source_id": "IG001", "platform": "instagram",
                             "profile_url": url}],
            }), encoding="utf-8")
            return load_registry(p)[0][0]

    def test_canonical_profile_url_accepted(self):
        s = self._check("https://www.instagram.com/example/")
        self.assertEqual(s.username, "example")

    def test_underscored_and_dotted_accepted(self):
        s = self._check("https://www.instagram.com/times_of_india_g.k/")
        self.assertEqual(s.username, "times_of_india_g.k")

    def test_post_url_rejected(self):
        with self.assertRaises(RegistryError):
            self._check("https://www.instagram.com/p/Cabcdef123/")

    def test_reel_url_rejected(self):
        with self.assertRaises(RegistryError):
            self._check("https://www.instagram.com/reel/Cabcdef123/")

    def test_non_instagram_rejected(self):
        with self.assertRaises(RegistryError):
            self._check("https://example.com/profile/")

    def test_explore_url_rejected(self):
        with self.assertRaises(RegistryError):
            self._check("https://www.instagram.com/explore/tags/physics/")

    def test_query_string_tolerated_and_canonicalized(self):
        s = self._check("https://www.instagram.com/example/?hl=en")
        self.assertEqual(s.profile_url, "https://www.instagram.com/example/")

    def test_31_char_username_rejected(self):
        with self.assertRaises(RegistryError):
            self._check("https://www.instagram.com/" + "a" * 31 + "/")


class TestExtractionLimit(unittest.TestCase):
    """Acceptance criterion 3: the 299-item cap, never 299+299."""

    def _pages(self, n, per_page=50):
        out = []
        made = 0
        while made < n:
            chunk = [make_item(made + i) for i in range(min(per_page, n - made))]
            out.append(chunk)
            made += len(chunk)
        return out

    def test_cap_enforced_at_max_items(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(timeline_pages=self._pages(350))
            summary = runner.extract_source(make_source(max_items=299), adapter=adapter)
            self.assertEqual(summary.extracted, 299)
            self.assertEqual(summary.status, "complete")
            self.assertIn("max_items", summary.stop_reason)

    def test_combined_edges_count_against_one_budget(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(
                timeline_pages=self._pages(200),
                reels_pages=self._pages(200),
            )
            summary = runner.extract_source(make_source(max_items=299), adapter=adapter)
            self.assertEqual(summary.extracted + summary.duplicate, 299)
            self.assertLessEqual(summary.extracted, 299)

    def test_smaller_per_source_cap_respected(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(timeline_pages=self._pages(350))
            summary = runner.extract_source(make_source(max_items=25), adapter=adapter)
            self.assertEqual(summary.extracted, 25)


class TestDeduplication(unittest.TestCase):
    """Acceptance criteria 4, 5: no double storage across edges or runs."""

    def test_same_content_id_in_two_edges_stored_once(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            shared = [make_item(0), make_item(1)]
            adapter = FakeAdapter(
                timeline_pages=[shared],
                reels_pages=[[make_item(0), make_item(1), make_item(2)]],
            )
            summary = runner.extract_source(make_source(), adapter=adapter)
            self.assertEqual(summary.extracted, 3)
            self.assertEqual(summary.duplicate, 2)
            stored = list((dirs["raw"] / "instagram" / "IG900").glob("*.json"))
            self.assertEqual(len([p for p in stored if p.name != "_profile.json"]), 3)

    def test_rerun_of_completed_source_stores_nothing_new(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(timeline_pages=[[make_item(i) for i in range(3)]])
            first = runner.extract_source(make_source(), adapter=adapter)
            self.assertEqual(first.extracted, 3)
            files_before = {
                p.name: p.stat().st_mtime_ns
                for p in (dirs["raw"] / "instagram" / "IG900").glob("*.json")
            }
            # A fresh adapter proves the rerun makes zero network requests:
            # its request_count stays 0 because the completed checkpoint is
            # skipped before any fetch happens.
            adapter2 = FakeAdapter(timeline_pages=[[make_item(i) for i in range(3)]])
            second = runner.extract_source(make_source(), adapter=adapter2)
            self.assertEqual(adapter2.request_count, 0)
            self.assertEqual(second.status, "complete")
            # Counts are cumulative checkpoint totals, not this-run deltas.
            self.assertEqual(second.extracted, 3)
            self.assertEqual(second.discovered, 3)
            files_after = {
                p.name: p.stat().st_mtime_ns
                for p in (dirs["raw"] / "instagram" / "IG900").glob("*.json")
            }
            self.assertEqual(files_before, files_after)


class TestCheckpointResume(unittest.TestCase):
    """Acceptance criteria 6, 10: interruption, resume, accounting."""

    def test_interrupted_run_resumes_without_refetching(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            # 6 pages x 10 UNIQUE items = 60 unique items.
            pages = [
                [make_item(page * 10 + i) for i in range(10)]
                for page in range(6)
            ]

            # First run: fetching page 2 of the timeline explodes.
            adapter = FakeAdapter(
                timeline_pages=pages, fail_pages={("timeline", 2)}
            )
            first = runner.extract_source(make_source(), adapter=adapter)
            self.assertEqual(first.status, "partial")
            self.assertEqual(first.extracted, 20)   # pages 0 and 1 stored

            # Second run with a healthy adapter resumes from cursor 2.
            adapter2 = FakeAdapter(timeline_pages=pages)
            second = runner.extract_source(make_source(), adapter=adapter2)
            self.assertEqual(second.status, "complete")
            # Cumulative checkpoint counts: 20 resumed + 40 new = 60.
            self.assertEqual(second.extracted, 60)
            self.assertEqual(second.discovered, 60)
            # Pages 0 and 1 were NOT re-fetched: the run made 5 requests =
            # 1 profile fetch + pages 2..5 (an uninterrupted run would need 7).
            self.assertEqual(adapter2.request_count, 5)

            # Final accounting equals an uninterrupted run of the same source.
            with TmpDirs() as dirs2:
                runner2 = make_runner(dirs2)
                uninterrupted = runner2.extract_source(
                    make_source(), adapter=FakeAdapter(timeline_pages=pages)
                )
            self.assertEqual(uninterrupted.extracted, 60)
            self.assertEqual(uninterrupted.discovered, 60)

    def test_checkpoint_written_after_every_page(self):
        with TmpDirs() as dirs:
            cp = Checkpoint("IG901", "instagram", 299,
                            directory=dirs["checkpoints"])
            cp.start()
            cp.record_extracted("x1")
            cp.save()
            disk = json.loads(
                (dirs["checkpoints"] / "IG901.json").read_text(encoding="utf-8")
            )
            self.assertEqual(disk["items"]["extracted"], 1)
            self.assertEqual(disk["status"], "in_progress")

    def test_accounting_identity_holds_in_manifest(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(
                timeline_pages=[[make_item(i) for i in range(5)]],
                reels_pages=[[make_item(3), make_item(9)]],
                fail_items={"item0002"},
            )
            summary = runner.extract_source(make_source(), adapter=adapter)
            manifests = list(Path(dirs["manifests"]).glob("IG900-*.json"))
            self.assertEqual(len(manifests), 1)
            m = json.loads(manifests[0].read_text(encoding="utf-8"))
            a = m["accounting"]
            self.assertEqual(
                a["discovered"], a["processed"] + a["duplicate"] + a["failed"]
            )
            self.assertTrue(m["identity_holds"])
            self.assertEqual(summary.failed, 1)


class TestFailureRecovery(unittest.TestCase):
    """Acceptance criterion 7: item and profile failures are isolated."""

    def test_failing_item_does_not_stop_profile(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(
                timeline_pages=[[make_item(i) for i in range(5)]],
                fail_items={"item0001", "item0003"},
            )
            summary = runner.extract_source(make_source(), adapter=adapter)
            self.assertEqual(summary.extracted, 3)
            self.assertEqual(summary.failed, 2)
            self.assertEqual(summary.status, "complete")

    def test_error_log_records_required_fields(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(
                timeline_pages=[[make_item(i) for i in range(3)]],
                fail_items={"item0000"},
            )
            runner.extract_source(make_source(), adapter=adapter)
            err_path = dirs["errors"] / "IG900.jsonl"
            self.assertTrue(err_path.is_file())
            entry = json.loads(err_path.read_text(encoding="utf-8").splitlines()[0])
            for key in ("source_id", "content_url", "error_type", "timestamp",
                        "retry_count", "status"):
                self.assertIn(key, entry)
            self.assertEqual(entry["retry_count"], adapter.max_retries)

    def test_failing_profile_does_not_stop_batch(self):
        with TmpDirs() as dirs:
            runner = IngestionRunner(
                raw_store=RawStore(base=dirs["raw"]),
                normalized_store=NormalizedStore(base=dirs["normalized"]),
                manifest_writer=ManifestWriter(directory=dirs["manifests"]),
                checkpoint_dir=dirs["checkpoints"],
                error_dir=dirs["errors"],
                sleep=lambda s: None,
            )

            class ExplodingAdapter(FakeAdapter):
                def fetch_profile(self, username):
                    if username == "dead":
                        raise RuntimeError("adapter exploded unexpectedly")
                    return super().fetch_profile(username)

            healthy_pages = [[make_item(i) for i in range(2)]]
            runner.adapter_factory = lambda src: ExplodingAdapter(
                timeline_pages=healthy_pages
            )
            summaries = runner.extract_many(
                [make_source("IG901", username="ok1"),
                 make_source("IG902", username="dead"),
                 make_source("IG903", username="ok2")],
            )
            # All three sources were attempted and reported: the unexpected
            # profile-level error on IG902 did not terminate the batch.
            self.assertEqual(len(summaries), 3)
            by_id = {s.source_id: s for s in summaries}
            # An unexpected crash mid-profile is resumable, so "partial" —
            # not "blocked", which is reserved for platform access refusal.
            self.assertEqual(by_id["IG902"].status, "partial")
            self.assertIn("unexpected error", by_id["IG902"].stop_reason)
            # The healthy sources after it were still processed.
            self.assertTrue(
                (dirs["checkpoints"] / "IG903.json").is_file()
            )
            cp3 = json.loads(
                (dirs["checkpoints"] / "IG903.json").read_text(encoding="utf-8")
            )
            self.assertEqual(cp3["status"], "complete")
            self.assertEqual(cp3["items"]["extracted"], 2)

    def test_blocked_profile_recorded_honestly(self):
        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(block_profile=True)
            summary = runner.extract_source(make_source(), adapter=adapter)
            self.assertEqual(summary.status, "blocked")
            self.assertEqual(summary.extracted, 0)
            self.assertIn("access", summary.stop_reason)

    def test_private_profile_recorded_honestly(self):
        from app.ingestion.adapters.base import ProfileSnapshot

        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            adapter = FakeAdapter(
                profile=ProfileSnapshot(
                    platform="fakegram", username="priv", user_id="u",
                    is_private=True, declared_counts={}, edges=[],
                )
            )
            summary = runner.extract_source(make_source(username="priv"), adapter=adapter)
            self.assertEqual(summary.status, "blocked")
            self.assertIn("private", summary.stop_reason)


class TestRawPersistence(unittest.TestCase):
    """Acceptance criteria 1, 8: raw schema, null honesty, slide order."""

    def _run_and_read(self, dirs, kind="carousel", slides=3):
        items = []
        for i in range(2):
            m = make_item(i, kind=kind)
            m.media = [
                MediaRef(index=j, url=f"https://cdn.example/{i}-{j}.jpg",
                         accessibility_caption=f"slide {j} alt")
                for j in range(slides)
            ]
            items.append(m)

        runner = make_runner(dirs)
        adapter = FakeAdapter(timeline_pages=[items])
        runner.extract_source(make_source(), adapter=adapter)
        records = sorted(
            (dirs["raw"] / "instagram" / "IG900").glob("item*.json")
        )
        return [json.loads(p.read_text(encoding="utf-8")) for p in records]

    def test_raw_record_schema(self):
        with TmpDirs() as dirs:
            recs = self._run_and_read(dirs)
            for r in recs:
                for key in (
                    "source_id", "platform", "profile_username", "content_id",
                    "content_url", "content_type", "published_at", "caption",
                    "hashtags", "media", "slides", "text", "engagement",
                    "platform_data", "extraction",
                ):
                    self.assertIn(key, r)
                self.assertEqual(r["extraction"]["status"], "raw")
                self.assertIsNotNone(r["extraction"]["extracted_at"])

    def test_unavailable_fields_are_null_not_invented(self):
        with TmpDirs() as dirs:
            recs = self._run_and_read(dirs)
            for r in recs:
                self.assertIsNone(r["text"]["ocr_text"])
                self.assertIsNone(r["text"]["transcript"])
                self.assertIsNone(r["text"]["on_screen_text"])
                self.assertIsNone(r["media"]["video"])

    def test_slide_order_preserved(self):
        with TmpDirs() as dirs:
            recs = self._run_and_read(dirs, slides=4)
            slides = recs[0]["slides"]
            self.assertEqual([s["index"] for s in slides], [0, 1, 2, 3])
            self.assertEqual(
                [s["image_url"] for s in slides],
                [f"https://cdn.example/0-{j}.jpg" for j in range(4)],
            )

    def test_platform_data_preserved_verbatim(self):
        with TmpDirs() as dirs:
            recs = self._run_and_read(dirs)
            self.assertEqual(recs[0]["platform_data"]["fake"], True)
            self.assertEqual(recs[0]["platform_data"]["pk"], "item0000")

    def test_normalized_record_has_provenance_and_ai_scaffold(self):
        with TmpDirs() as dirs:
            self._run_and_read(dirs)
            norm_files = sorted((dirs["normalized"] / "instagram" / "IG900").glob("*.json"))
            self.assertEqual(len(norm_files), 2)
            n = json.loads(norm_files[0].read_text(encoding="utf-8"))
            prov = n["provenance"]
            for key in ("source_id", "profile_username", "content_id",
                        "original_url", "content_type", "published_at",
                        "extracted_at", "provenance_tier"):
                self.assertIn(key, prov)
            self.assertEqual(prov["provenance_tier"], "T3_EXPERT")
            ai = n["ai_processing"]
            self.assertEqual(ai["status"], "not_processed")
            for key in ("subject", "knowledge_type", "si_relevance",
                        "constable_relevance", "telangana_relevance",
                        "pyq_similarity", "revision_priority", "confidence",
                        "verification_status", "processed_at"):
                self.assertIsNone(ai[key], f"ai_processing.{key} must start null")
            self.assertIn("content_hash", n["hashes"])
            self.assertIn("url_hash", n["hashes"])


class TestNewSourceRegistration(unittest.TestCase):
    """Acceptance criterion 9: a new URL ingests with no code change."""

    def test_add_then_extract_without_code_change(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp, TmpDirs() as dirs:
            reg_path = Path(tmp) / "registry.json"
            reg_path.write_text(json.dumps({
                "version": 1,
                "defaults": {"max_items": 299},
                "sources": [],
            }), encoding="utf-8")

            src = add_source("https://www.instagram.com/brand_new_profile/",
                             path=reg_path)
            self.assertEqual(src.source_id, "IG001")
            self.assertEqual(src.username, "brand_new_profile")

            # The registry on disk now includes it, loadable by plain load.
            sources, _ = load_registry(reg_path)
            self.assertEqual(sources[0].username, "brand_new_profile")
            self.assertEqual(sources[0].profile_url,
                             "https://www.instagram.com/brand_new_profile/")

            # And it extracts through the same runner with zero code change.
            runner = make_runner(dirs)
            adapter = FakeAdapter(
                timeline_pages=[[make_item(i) for i in range(2)]]
            )
            summary = runner.extract_source(sources[0], adapter=adapter)
            self.assertEqual(summary.extracted, 2)
            self.assertTrue(
                (dirs["raw"] / "instagram" / "IG001" / "item0000.json").is_file()
            )

    def test_add_rejects_duplicate_username(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "registry.json"
            reg_path.write_text(json.dumps({
                "sources": [{
                    "source_id": "IG001", "platform": "instagram",
                    "username": "dup", "profile_url": "https://www.instagram.com/dup/",
                }],
            }), encoding="utf-8")
            with self.assertRaises(RegistryError):
                add_source("https://www.instagram.com/dup/", path=reg_path)

    def test_next_source_id_increments(self):
        s1 = make_source("IG001", username="a")
        s2 = make_source("IG002", username="b")
        self.assertEqual(next_source_id([s1, s2]), "IG003")


    def test_embedded_profile_page_is_consumed(self):
        """HTML-fallback path: the profile response's own embedded first page
        must be dispositioned like a fetched page (cap, dedup, checkpoint)."""
        from app.ingestion.adapters.base import EdgePage, ProfileSnapshot

        with TmpDirs() as dirs:
            runner = make_runner(dirs)
            embedded_items = [make_item(i) for i in range(4)]
            adapter = FakeAdapter(
                profile=ProfileSnapshot(
                    platform="fakegram", username="embed", user_id="u1",
                    is_private=False,
                    declared_counts={"timeline": 4},
                    edges=["timeline"],
                    raw={},
                    embedded_pages={
                        "timeline": EdgePage(
                            edge="timeline", items=embedded_items,
                            has_next=False, end_cursor=None,
                        )
                    },
                )
            )
            summary = runner.extract_source(make_source(username="embed"),
                                            adapter=adapter)
            self.assertEqual(summary.extracted, 4)
            self.assertEqual(summary.status, "complete")
            stored = [p for p in (dirs["raw"] / "instagram" / "IG900").glob("item*.json")]
            self.assertEqual(len(stored), 4)


class TestInstagramURLParsing(unittest.TestCase):
    """The Instagram adapter's own parsing rules, without network."""

    def test_content_type_mapping(self):
        from app.ingestion.adapters.instagram import _TYPE_MAP

        self.assertEqual(_TYPE_MAP["GraphSidecar"], "carousel")
        self.assertEqual(_TYPE_MAP["XDTGraphImage"], "post")
        self.assertEqual(_TYPE_MAP["GraphVideo"], "reel")

    def test_unknown_typename_is_unclassified_not_guessed(self):
        from app.ingestion.adapters.instagram import _TYPE_MAP

        self.assertIsNone(_TYPE_MAP.get("GraphSomeFutureType"))

    def test_fake_adapter_platform_is_not_instagram_for_tests(self):
        # Guard: tests must never silently hit the real network adapter.
        self.assertEqual(FakeAdapter.platform, "fakegram")


class TestCLI(unittest.TestCase):
    def test_status_reports_registry_without_network(self):
        with self.subTest("cmd=status"):
            rc = cli_main(["status", "IG001"])
            self.assertEqual(rc, 0)

    def test_unknown_source_id_errors(self):
        rc = cli_main(["status", "IG999"])
        self.assertEqual(rc, 2)

    def test_extract_unknown_source_errors(self):
        rc = cli_main(["extract", "--source", "IG999"])
        self.assertEqual(rc, 2)

    def test_direct_url_validation_in_cli(self):
        with TmpDirs() as dirs:
            # A post URL (not a profile URL) must be rejected before any fetch.
            rc = cli_main(["extract", "--url", "https://www.instagram.com/p/Cabc123/"])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
