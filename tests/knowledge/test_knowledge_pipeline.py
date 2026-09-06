"""Knowledge-pipeline tests (SPEC-KNW-001 §12, all 18 acceptance criteria).

Deterministic, offline, standard-library unittest only (D-0006). The GLM
client's HTTP path is never exercised; every test uses ScriptedClient.

Run from the project folder:

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.knowledge import taxonomy  # noqa: E402
from app.knowledge.candidates import (  # noqa: E402
    build_candidates, build_questions,
)
from app.knowledge.client import GlmClient, MissingKeyError  # noqa: E402
from app.knowledge.dedup import concept_key  # noqa: E402
from app.knowledge.extraction_schema import (  # noqa: E402
    ExtractionResult, ExtractionSchemaError, validate_extraction,
)
from app.knowledge.pipeline import KnowledgePipeline  # noqa: E402
from app.knowledge.processor import process_raw_record  # noqa: E402
from app.knowledge.prompts import (  # noqa: E402
    CURRENT_PROMPT_VERSION, PROMPT_VERSIONS,
)
from app.knowledge.prompts.knowledge_extraction_v1 import (  # noqa: E402
    build_messages,
)
from app.knowledge.scoring import exam_relevance_scores  # noqa: E402
from app.knowledge.taxonomy import SUBJECTS  # noqa: E402
from app.knowledge.verify_queue import resolve_verifier_provider  # noqa: E402

from ._fixtures import (  # noqa: E402
    AlwaysFailingClient, ExplodingOnceClient, ScriptedClient,
    TmpStores, fixture_raws, fixture_script,
)

ROOT = Path(__file__).resolve().parents[2]


def make_pipeline(stores, client):
    from app.knowledge.dedup import ConceptIndex

    return KnowledgePipeline(
        client=client,
        processed_store=stores["processed"],
        candidate_store=stores["candidates"],
        question_store=stores["questions"],
        concept_store=stores["concepts"],
        verify_queue=stores["queue"],
        checkpoint_path=stores["checkpoint"],
    )


def by_content_id(raws):
    return {r["content_id"]: r for r in raws}


class TestContentProcessing(unittest.TestCase):
    """Criteria 1, 2 — empty content, null fields."""

    def test_all_null_text_skips_with_reason(self):
        rec = process_raw_record(by_content_id(fixture_raws())["FIX0008"])
        self.assertEqual(rec.skipped_reason, "no_text")
        self.assertFalse(rec.has_text)

    def test_null_fields_never_invented(self):
        rec = process_raw_record(by_content_id(fixture_raws())["FIX0008"])
        self.assertEqual(rec.text_parts, [])
        self.assertIsNone(rec.processing_hash)

    def test_ocr_only_record_reads_slides_in_order(self):
        rec = process_raw_record(by_content_id(fixture_raws())["FIX0005"])
        kinds = [(p["kind"], p["text"]) for p in rec.text_parts]
        self.assertEqual(kinds, [
            ("slide_ocr", "Telangana was formed on 2 June 2014."),
            ("slide_ocr", "It is the 29th state of India."),
        ])

    def test_caption_only_record(self):
        rec = process_raw_record(by_content_id(fixture_raws())["FIX0001"])
        self.assertEqual(len(rec.text_parts), 1)
        self.assertEqual(rec.text_parts[0]["kind"], "caption")

    def test_transcript_only_record(self):
        raw = {
            "source_id": "IGT01", "platform": "instagram", "content_id": "T1",
            "content_url": "https://www.instagram.com/p/T1/", "content_type": "reel",
            "published_at": None, "profile_username": "u", "caption": None,
            "hashtags": [], "media": {"images": [], "video": {"url": "x"}},
            "slides": [],
            "text": {"caption_text": None, "ocr_text": None,
                     "transcript": "welcome to today's class on Article 21",
                     "on_screen_text": None},
            "engagement": {"likes": None, "comments": None},
            "platform_data": {}, "extraction": {"status": "raw", "extracted_at": "x"},
        }
        rec = process_raw_record(raw)
        self.assertEqual(rec.text_parts, [
            {"kind": "transcript", "text": "welcome to today's class on Article 21"}
        ])

    def test_processing_hash_stable_for_identical_text(self):
        a = process_raw_record(by_content_id(fixture_raws())["FIX0006"])
        b = process_raw_record(by_content_id(fixture_raws())["FIX0006"])
        self.assertEqual(a.processing_hash, b.processing_hash)


class TestExtractionSchema(unittest.TestCase):
    """Criteria 3, 4, 5, 13 — relevance, enums, malformed output."""

    def test_valid_fixture_payloads_all_parse(self):
        for cid, payload in fixture_script()["responses"].items():
            with self.subTest(cid=cid):
                result = validate_extraction(payload)
                self.assertIsInstance(result, ExtractionResult)

    def test_not_relevant_with_smuggled_items_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction({
                "relevance": "NOT_RELEVANT",
                "items": [{"knowledge_text": "x", "subject": "Arithmetic",
                           "knowledge_type": "FACT", "confidence": 0.5}],
                "questions": [],
            })

    def test_unknown_subject_rejected_with_path(self):
        with self.assertRaises(ExtractionSchemaError) as ctx:
            validate_extraction({
                "relevance": "RELEVANT",
                "items": [{"knowledge_text": "x", "subject": "Astrology",
                           "knowledge_type": "FACT"}],
                "questions": [],
            })
        self.assertIn("$.items[0].subject", str(ctx.exception))

    def test_unknown_knowledge_type_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction({
                "relevance": "RELEVANT",
                "items": [{"knowledge_text": "x", "subject": "Arithmetic",
                           "knowledge_type": "VIBES"}],
                "questions": [],
            })

    def test_confidence_out_of_range_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction({
                "relevance": "RELEVANT",
                "items": [{"knowledge_text": "x", "subject": "Arithmetic",
                           "knowledge_type": "FACT", "confidence": 1.5}],
                "questions": [],
            })

    def test_answer_claimed_but_missing_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction({
                "relevance": "RELEVANT", "items": [],
                "questions": [{"question_text": "q?", "options": {"A": "1"},
                               "answer": None, "subject": "Arithmetic",
                               "question_format": "MCQ",
                               "answer_status": "STATED_BY_SOURCE"}],
            })

    def test_answer_invented_for_not_stated_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction({
                "relevance": "RELEVANT", "items": [],
                "questions": [{"question_text": "q?", "options": {"A": "1"},
                               "answer": "A", "subject": "Arithmetic",
                               "question_format": "MCQ",
                               "answer_status": "NOT_STATED"}],
            })

    def test_answer_not_among_options_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction({
                "relevance": "RELEVANT", "items": [],
                "questions": [{"question_text": "q?", "options": {"A": "1"},
                               "answer": "Z", "subject": "Arithmetic",
                               "question_format": "MCQ",
                               "answer_status": "STATED_BY_SOURCE"}],
            })

    def test_non_object_payload_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction([1, 2, 3])

    def test_empty_knowledge_text_rejected(self):
        with self.assertRaises(ExtractionSchemaError):
            validate_extraction({
                "relevance": "RELEVANT",
                "items": [{"knowledge_text": "   ", "subject": "Arithmetic",
                           "knowledge_type": "FACT"}],
                "questions": [],
            })


class TestAtomicExtraction(unittest.TestCase):
    """Criterion 6 — one post, two atomic candidates, same provenance."""

    def _two(self):
        raws = by_content_id(fixture_raws())
        client = ScriptedClient()
        rec = process_raw_record(raws["FIX0001"])
        extraction = client.extract(rec)
        return build_candidates(
            rec, extraction, prompt_version=client.prompt_version,
            model_name=client.model,
        )

    def test_two_facts_yield_two_candidates(self):
        cands = self._two()
        self.assertEqual(len(cands), 2)
        texts = {c["knowledge_text"] for c in cands}
        self.assertEqual(texts, {
            "The Constitution of India was adopted on 26 November 1949.",
            "The Constitution of India came into force on 26 January 1950.",
        })

    def test_both_candidates_share_identical_provenance(self):
        cands = self._two()
        self.assertEqual(cands[0]["provenance"], cands[1]["provenance"])
        self.assertEqual(cands[0]["provenance"]["source_id"], "IGFIX01")
        self.assertEqual(cands[0]["provenance"]["content_id"], "FIX0001")


class TestQuestionExtraction(unittest.TestCase):
    """Criterion 7 — MCQs with and without answers; nothing invented."""

    def _questions_for(self, cid):
        raws = by_content_id(fixture_raws())
        client = ScriptedClient()
        rec = process_raw_record(raws[cid])
        extraction = client.extract(rec)
        return build_questions(
            rec, extraction, prompt_version=client.prompt_version,
            model_name=client.model,
        )

    def test_mcq_with_stated_answer(self):
        qs = self._questions_for("FIX0002")
        self.assertEqual(len(qs), 1)
        q = qs[0]
        self.assertEqual(q["options"], {"A": "Nehru", "B": "Ambedkar",
                                        "C": "Patel", "D": "Gandhi"})
        self.assertEqual(q["answer"], "B")
        self.assertEqual(q["answer_status"], "STATED_BY_SOURCE")

    def test_question_without_answer_records_null_not_stated(self):
        qs = self._questions_for("FIX0003")
        self.assertEqual(len(qs), 1)
        q = qs[0]
        self.assertIsNone(q["answer"])
        self.assertEqual(q["answer_status"], "NOT_STATED")
        self.assertEqual(q["options"], {})

    def test_no_options_never_fabricated(self):
        # A scripted response with empty options must yield empty options —
        # the schema forbids inventing, and the builder must not either.
        qs = self._questions_for("FIX0003")
        self.assertEqual(qs[0]["options"], {})
        self.assertNotIn("A", qs[0]["options"])


class TestProvenancePreservation(unittest.TestCase):
    """Criterion 8 — every downstream field traces to the raw record."""

    def test_candidate_provenance_field_by_field(self):
        raw = by_content_id(fixture_raws())["FIX0001"]
        client = ScriptedClient()
        rec = process_raw_record(raw)
        extraction = client.extract(rec)
        cands = build_candidates(rec, extraction,
                                 prompt_version=client.prompt_version,
                                 model_name=client.model)
        prov = cands[0]["provenance"]
        self.assertEqual(prov["source_id"], raw["source_id"])
        self.assertEqual(prov["content_id"], raw["content_id"])
        self.assertEqual(prov["source_url"], raw["content_url"])
        self.assertEqual(prov["published_at"], raw["published_at"])
        self.assertEqual(prov["content_type"], raw["content_type"])
        self.assertEqual(prov["prompt_version"], "knowledge-extraction-v1")
        self.assertIsNotNone(prov["extraction_timestamp"])
        self.assertEqual(prov["provenance_tier"], "T3_EXPERT")

    def test_processed_record_preserves_raw_fields(self):
        raw = by_content_id(fixture_raws())["FIX0005"]
        rec = process_raw_record(raw)
        self.assertEqual(rec.source_url, raw["content_url"])
        self.assertEqual(rec.content_type, "carousel")
        self.assertEqual(rec.hashtags, raw["hashtags"])

    def test_fixture_flag_propagates(self):
        raw = by_content_id(fixture_raws())["FIX0001"]
        rec = process_raw_record(raw)
        self.assertTrue(rec.is_fixture)
        client = ScriptedClient()
        extraction = client.extract(rec)
        cands = build_candidates(rec, extraction,
                                 prompt_version=client.prompt_version,
                                 model_name=client.model)
        self.assertTrue(cands[0]["provenance"]["test_fixture"])


class TestRelevanceFiltering(unittest.TestCase):
    """Criterion 3 — NOT_RELEVANT creates nothing; UNCERTAIN still does."""

    def test_not_relevant_yields_no_candidates_or_questions(self):
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            summary = pipe.process_batch(
                [by_content_id(fixture_raws())["FIX0004"]]
            )
            self.assertEqual(summary.not_relevant, 1)
            self.assertEqual(summary.candidates_written, 0)
            self.assertEqual(summary.questions_written, 0)

    def test_uncertain_still_creates_candidates(self):
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            summary = pipe.process_batch(
                [by_content_id(fixture_raws())["FIX0009"]]
            )
            self.assertEqual(summary.candidates_written, 1)
            cands = list(stores["candidates"].base.glob("*.json"))
            c = json.loads(cands[0].read_text(encoding="utf-8"))
            self.assertEqual(c["relevance"], "UNCERTAIN")


class TestDeduplicationAndCorroboration(unittest.TestCase):
    """Criteria 9, 10 — one concept, multiple sources, provenance kept."""

    def test_active_passive_pair_collides(self):
        a = concept_key(
            "Fundamental Duties were added by the 42nd Amendment.", "AMENDMENT")
        b = concept_key(
            "The 42nd Amendment introduced Fundamental Duties.", "AMENDMENT")
        self.assertEqual(a, b)

    def test_different_knowledge_type_does_not_collide(self):
        a = concept_key("Same words here.", "FACT")
        b = concept_key("Same words here.", "DATE")
        self.assertNotEqual(a, b)

    def test_negation_is_not_merged(self):
        # 'not' must never be a stopword or a synonym: a fact and its
        # negation are different concepts.
        a = concept_key("The President is elected.", "FACT")
        b = concept_key("The President is not elected.", "FACT")
        self.assertNotEqual(a, b)

    def test_fixture_pair_becomes_one_concept_two_sources(self):
        raws = by_content_id(fixture_raws())
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch([raws["FIX0006"], raws["FIX0007"]])
            concepts = [json.loads(p.read_text(encoding="utf-8"))
                        for p in stores["concepts"].base.glob("*.json")]
            self.assertEqual(len(concepts), 1)
            c = concepts[0]
            self.assertEqual(c["source_count"], 2)
            self.assertEqual(
                {s["source_id"] for s in c["supporting_sources"]},
                {"IGFIX03", "IGFIX04"},
            )
            self.assertEqual(c["source_diversity"], "FEW_ACCOUNTS")

    def test_corroboration_is_not_verification(self):
        raws = by_content_id(fixture_raws())
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch([raws["FIX0006"], raws["FIX0007"]])
            c = json.loads(
                next(stores["concepts"].base.glob("*.json"))
                .read_text(encoding="utf-8")
            )
            self.assertEqual(c["verification_status"], "UNVERIFIED")
            self.assertTrue(c["corroboration_is_not_verification"])

    def test_rerun_keeps_supporters_append_only(self):
        raws = by_content_id(fixture_raws())
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch([raws["FIX0006"], raws["FIX0007"]])
            pipe.process_batch([raws["FIX0006"], raws["FIX0007"]], force=True)
            c = json.loads(
                next(stores["concepts"].base.glob("*.json"))
                .read_text(encoding="utf-8")
            )
            # same two sources, never duplicated by the rerun
            self.assertEqual(c["source_count"], 2)
            pairs = [(s["source_id"], s["content_id"])
                     for s in c["supporting_sources"]]
            self.assertEqual(sorted(pairs), [("IGFIX03", "FIX0006"),
                                             ("IGFIX04", "FIX0007")])


class TestIdempotencyAndResume(unittest.TestCase):
    """Criteria 11, 12 — no duplicate files; resume skips processed."""

    def test_rerun_creates_no_new_candidate_files(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            s1 = pipe.process_batch(raws)
            before = sorted(p.name for p in stores["candidates"].base.glob("*.json"))
            s2 = pipe.process_batch(raws)
            after = sorted(p.name for p in stores["candidates"].base.glob("*.json"))
            self.assertEqual(before, after)
            # A rerun over fully-dispositioned content writes nothing new:
            # that is what idempotency means here.
            self.assertEqual(s2.candidates_written, 0)
            self.assertEqual(s2.questions_written, 0)

    def test_resume_continues_from_checkpoint(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            # First run: crashes on the first item past FIX0003, after three
            # items were dispositioned.
            class CrashClient(ScriptedClient):
                def extract(self, processed):
                    if processed.content_id in ("FIX0001", "FIX0002", "FIX0003"):
                        return super().extract(processed)
                    raise RuntimeError("simulated crash mid-batch")

            pipe = make_pipeline(stores, CrashClient())
            pipe.process_batch(raws)
            cp = json.loads(stores["checkpoint"].read_text(encoding="utf-8"))
            self.assertEqual(len(cp["processed_content_ids"]), 3)

            healthy = ScriptedClient()
            pipe2 = KnowledgePipeline(
                client=healthy,
                processed_store=stores["processed"],
                candidate_store=stores["candidates"],
                question_store=stores["questions"],
                concept_store=stores["concepts"],
                verify_queue=stores["queue"],
                checkpoint_path=stores["checkpoint"],
            )
            pipe2.process_batch(raws)
            # items 1-3 were NOT re-extracted. Run 2 handles 6 remaining
            # items, of which FIX0008 is empty content (no model call),
            # so exactly 5 model calls must occur.
            self.assertEqual(healthy.calls, 5)
            cp2 = json.loads(stores["checkpoint"].read_text(encoding="utf-8"))
            self.assertEqual(len(cp2["failed"]), 0)  # healthy rerun succeeded

    def test_no_model_call_for_empty_content(self):
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch([by_content_id(fixture_raws())["FIX0008"]])
            self.assertEqual(client.calls, 0)

    def test_within_run_duplicate_text_skips_second_call(self):
        raws = fixture_raws()
        dup = dict(raws[0])
        dup["content_id"] = "FIX0001-DUP"
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch([raws[0], dup])
            # identical caption text: the second is dispositioned as duplicate
            self.assertEqual(client.calls, 1)


class TestModelFailures(unittest.TestCase):
    """Criteria 14, 15, 16 — model failure, retries, batch isolation."""

    def test_permanent_failure_isolated_and_recorded(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = AlwaysFailingClient()
            pipe = make_pipeline(stores, client)
            summary = pipe.process_batch(raws)
            self.assertEqual(summary.failed, len(raws) - 1)  # no-text item skips
            self.assertEqual(summary.processed, 0)
            self.assertEqual(len(summary.failures), len(raws) - 1)
            cp = json.loads(stores["checkpoint"].read_text(encoding="utf-8"))
            for entry in cp["failed"].values():
                self.assertEqual(entry["retries"], taxonomy.MAX_EXTRACTION_RETRIES)

    def test_transient_failure_retried_then_succeeds(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ExplodingOnceClient(fail_first={"FIX0001": 1})
            pipe = make_pipeline(stores, client)
            summary = pipe.process_batch([raws[0]])
            self.assertEqual(summary.failed, 0)
            self.assertEqual(summary.candidates_written, 2)

    def test_one_failing_item_does_not_stop_batch(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            class OneBadItem(ScriptedClient):
                def extract(self, processed):
                    if processed.content_id == "FIX0002":
                        raise RuntimeError("this item explodes")
                    return super().extract(processed)

            pipe = make_pipeline(stores, OneBadItem())
            summary = pipe.process_batch(raws)
            self.assertEqual(summary.failed, 1)
            self.assertGreater(summary.candidates_written, 0)
            # the failed item's OWN question is absent; FIX0003's question,
            # from a healthy item later in the batch, is still written
            self.assertEqual(summary.questions_written, 1)
            written_q = [
                json.loads(p.read_text(encoding="utf-8"))
                for p in stores["questions"].base.glob("*.json")
            ]
            self.assertEqual(
                {q["provenance"]["content_id"] for q in written_q},
                {"FIX0003"},
            )


class TestVerificationSeparation(unittest.TestCase):
    """Criterion 15 — UNVERIFIED only; provider separation; queue shape."""

    def test_candidates_created_unverified(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch(raws)
            for p in stores["candidates"].base.glob("*.json"):
                c = json.loads(p.read_text(encoding="utf-8"))
                self.assertEqual(c["verification_status"], "UNVERIFIED")

    def test_questions_created_unverified(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch(raws)
            for p in stores["questions"].base.glob("*.json"):
                q = json.loads(p.read_text(encoding="utf-8"))
                self.assertEqual(q["verification_status"], "UNVERIFIED")

    def test_verifier_provider_differs_from_author(self):
        provider, reason = resolve_verifier_provider()
        self.assertIsNotNone(provider)
        # author is glm; the resolved verifier must be a different provider
        self.assertNotEqual(provider, "glm")
        self.assertIn("AUTO_NOT_AUTHOR", reason)

    def test_queue_lines_never_verified(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch(raws)
            lines = [
                json.loads(x) for x in
                stores["queue"].path.read_text(encoding="utf-8").splitlines()
                if x.strip()
            ]
            self.assertGreater(len(lines), 0)
            for ln in lines:
                self.assertEqual(ln["verification_status"], "UNVERIFIED")
                self.assertEqual(ln["queue_status"], "QUEUED")
                self.assertIsNotNone(ln["required_verifier_provider"])
                self.assertIsNotNone(ln["concept_id"])

    def test_pipeline_has_no_verify_method(self):
        # The pipeline structurally cannot verify: no method exists for it.
        self.assertFalse(hasattr(KnowledgePipeline, "verify"))
        self.assertFalse(hasattr(KnowledgePipeline, "mark_verified"))


class TestPromptVersions(unittest.TestCase):
    """Criterion 16 — prompt versions change ids and are recorded."""

    def test_current_version_is_registered(self):
        self.assertIn(CURRENT_PROMPT_VERSION, PROMPT_VERSIONS)

    def test_new_prompt_version_changes_candidate_ids(self):
        from app.knowledge.candidates import candidate_id

        a = candidate_id("IGFIX01", "FIX0001", "knowledge-extraction-v1", 0, "x")
        b = candidate_id("IGFIX01", "FIX0001", "knowledge-extraction-v2", 0, "x")
        self.assertNotEqual(a, b)

    def test_checkpoint_records_prompt_version(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch(raws)
            cp = json.loads(stores["checkpoint"].read_text(encoding="utf-8"))
            self.assertEqual(cp["prompt_version"], "knowledge-extraction-v1")

    def test_version_change_resets_checkpoint_scope(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch(raws[:3])
            # a NEW prompt version re-extracts: old processed ids do not apply
            v2client = ScriptedClient(prompt_version="knowledge-extraction-v2")
            pipe2 = make_pipeline(stores, v2client)
            s2 = pipe2.process_batch(raws[:3])
            self.assertEqual(s2.processed, 3)
            self.assertEqual(v2client.calls, 3)

    def test_prompt_includes_atomic_instruction(self):
        msgs = build_messages(process_raw_record(
            by_content_id(fixture_raws())["FIX0001"]
        ))
        system = msgs[0]["content"]
        self.assertIn("EXTRACT, do not summarize", system)
        self.assertIn("ATOMIC", system)
        self.assertIn("NEVER INVENT", system)
        self.assertIn("26 November 1949", system)
        self.assertIn("26 January 1950", system)


class TestScoring(unittest.TestCase):
    """Criterion 9 support — scoring rules deterministic and documented."""

    def test_syllabus_subject_scores_relevant(self):
        s = exam_relevance_scores("Arithmetic", "FORMULA")
        self.assertEqual(s["si_relevance"], 1)

    def test_unmapped_subject_scores_zero(self):
        s = exam_relevance_scores("Indian Constitution", "FACT")
        self.assertEqual(s["si_relevance"], 0)
        self.assertIn("PROVISIONAL", s["constable_relevance_basis"])

    def test_pyq_similarity_is_null_without_denominator(self):
        s = exam_relevance_scores("Arithmetic", "FORMULA")
        self.assertIsNone(s["pyq_similarity"])

    def test_revision_priority_capped(self):
        # Telangana DATE on syllabus: R1(2)+R2(1)+R3(1) = 4
        s = exam_relevance_scores("Telangana History", "DATE")
        self.assertLessEqual(s["revision_priority"], 5)
        self.assertEqual(s["revision_priority"], 4)

    def test_confidence_labelled_model_self_reported(self):
        raws = fixture_raws()
        client = ScriptedClient()
        rec = process_raw_record(raws[0])
        cands = build_candidates(
            rec, client.extract(rec),
            prompt_version=client.prompt_version, model_name=client.model,
        )
        self.assertEqual(cands[0]["confidence_basis"], "model_self_reported")


class TestNoNetworkInTests(unittest.TestCase):
    """Criterion 17 — structural guarantees that tests cannot hit network."""

    def test_fixture_client_is_not_glm_http(self):
        client = ScriptedClient()
        self.assertIn("no network", client.model)

    def test_live_client_requires_key(self):
        # A live GlmClient cannot make a call without GLM_API_KEY: the key
        # lookup raises MissingKeyError rather than sending anything.
        client = GlmClient.__new__(GlmClient)   # no routing read, no call
        client.api_key_env = "GLM_API_KEY"
        import os
        had = os.environ.pop("GLM_API_KEY", None)
        try:
            with self.assertRaises(MissingKeyError):
                client._api_key()
        finally:
            if had is not None:
                os.environ["GLM_API_KEY"] = had

    def test_fixture_records_all_marked_test_fixture(self):
        for raw in fixture_raws():
            with self.subTest(cid=raw["content_id"]):
                self.assertTrue(raw["test_fixture"])
                self.assertTrue(raw["source_id"].startswith("IGFIX"))

    def test_no_real_instagram_raw_records_processed(self):
        # The CLI fixture path only ever reads tests/fixtures; assert the
        # real raw store is untouched by the offline pipeline by checking
        # the reserved id range in every candidate id's provenance.
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            pipe.process_batch(raws)
            for p in stores["candidates"].base.glob("*.json"):
                c = json.loads(p.read_text(encoding="utf-8"))
                self.assertTrue(c["provenance"]["test_fixture"])
                self.assertTrue(
                    c["provenance"]["source_id"].startswith("IGFIX"),
                    f"real source id leaked into fixture run: "
                    f"{c['provenance']['source_id']}"
                )


class TestFixturePipelineEndToEnd(unittest.TestCase):
    """Criterion 18 — the full committed fixture through the full pipeline,
    in a temp store, asserting the exact expected census."""

    def test_full_fixture_census(self):
        raws = fixture_raws()
        with TmpStores() as stores:
            client = ScriptedClient()
            pipe = make_pipeline(stores, client)
            summary = pipe.process_batch(raws)
            self.assertEqual(summary.total, 9)
            self.assertEqual(summary.processed, 7)
            self.assertEqual(summary.skipped_no_text, 1)
            self.assertEqual(summary.not_relevant, 1)
            self.assertEqual(summary.candidates_written, 7)
            self.assertEqual(summary.questions_written, 2)
            concepts = list(stores["concepts"].base.glob("*.json"))
            self.assertEqual(len(concepts), 6)
            c42 = [
                json.loads(p.read_text(encoding="utf-8")) for p in concepts
                if json.loads(p.read_text(encoding="utf-8"))["source_count"] == 2
            ]
            self.assertEqual(len(c42), 1)
            self.assertEqual(c42[0]["verification_status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
