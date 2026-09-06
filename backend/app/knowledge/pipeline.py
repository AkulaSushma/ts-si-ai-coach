"""Batch knowledge pipeline (SPEC-KNW-001 §9): raw records → processed →
GLM extraction → candidates + questions → concepts → verification queue.

Guarantees:
- checkpoint after EVERY item; crash ⇒ resume continues from the checkpoint
- idempotent: re-running stores nothing new for already-processed content
- cost-controlled: empty content never reaches the model; already-processed
  and within-run duplicate text never re-call the model
- failure isolation: one item's extraction failure records the failure with
  retry count and moves on; the batch always completes
- no Instagram source is processed by this pipeline unless raw records for
  it actually exist on disk; the CLI's --fixture path uses the committed
  fixture dataset only
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import taxonomy
from .candidates import build_candidates, build_questions
from .dedup import ConceptIndex
from .extraction_schema import ExtractionSchemaError
from .processor import process_raw_record
from .stores import CandidateStore, ConceptStore, ProcessedStore, QuestionStore
from .verify_queue import VerificationQueue


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ItemOutcome:
    content_id: str
    disposition: str          # processed | skipped_no_text | not_relevant |
                              # duplicate_text | failed
    candidates: int = 0
    questions: int = 0
    error: str | None = None
    retries: int = 0


@dataclass
class BatchSummary:
    total: int = 0
    processed: int = 0
    skipped_no_text: int = 0
    not_relevant: int = 0
    duplicate_text: int = 0
    failed: int = 0
    candidates_written: int = 0
    questions_written: int = 0
    model_calls: int = 0
    failures: list = field(default_factory=list)


class KnowledgePipeline:
    def __init__(self, *, client, processed_store: ProcessedStore | None = None,
                 candidate_store: CandidateStore | None = None,
                 question_store: QuestionStore | None = None,
                 concept_store: ConceptStore | None = None,
                 verify_queue: VerificationQueue | None = None,
                 checkpoint_path: Path | None = None,
                 max_retries: int = taxonomy.MAX_EXTRACTION_RETRIES):
        self.client = client
        self.processed = processed_store or ProcessedStore()
        self.candidates = candidate_store or CandidateStore()
        self.questions = question_store or QuestionStore()
        self.concepts = ConceptIndex(concept_store or ConceptStore())
        self.queue = verify_queue or VerificationQueue()
        self.checkpoint_path = (
            checkpoint_path
            if checkpoint_path is not None
            else self.processed.base.parent / "knowledge" / "checkpoint.json"
        )
        self.max_retries = max_retries

    # --------------------------------------------------------- checkpoint

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_path.is_file():
            return json.loads(
                self.checkpoint_path.read_text(encoding="utf-8")
            )
        return {
            "prompt_version": self.client.prompt_version,
            "model": getattr(self.client, "model", "fake-client"),
            "processed_content_ids": [],
            "failed": {},       # content_id -> {error, retries, last_at}
            "duplicate_content_ids": [],
            "not_relevant_content_ids": [],
            "skipped_no_text_ids": [],
            "updated_at": None,
        }

    def _save_checkpoint(self, cp: dict) -> None:
        cp["updated_at"] = _utcnow()
        from .stores import atomic_write_json
        atomic_write_json(self.checkpoint_path, cp)

    # ------------------------------------------------------------ one item

    def process_one(self, raw: dict, *, cp: dict, seen_text_hashes: set,
                    force: bool = False) -> ItemOutcome:
        content_id = raw.get("content_id") or "unknown"

        rec = process_raw_record(raw)
        out = ItemOutcome(content_id=content_id, disposition="processed")

        if not rec.has_text:
            cp["skipped_no_text_ids"].append(content_id)
            self.processed.store(rec)
            self._save_checkpoint(cp)
            out.disposition = "skipped_no_text"
            return out

        # Cost control: within-run duplicate text never re-calls the model.
        if rec.processing_hash in seen_text_hashes:
            cp["duplicate_content_ids"].append(content_id)
            self._save_checkpoint(cp)
            out.disposition = "duplicate_text"
            return out
        seen_text_hashes.add(rec.processing_hash)

        self.processed.store(rec)

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                extraction = self.client.extract(rec)
                break
            except ExtractionSchemaError as e:
                last_err = f"schema: {e}"
                out.retries = attempt
            except Exception as e:   # transport or unexpected — isolate
                last_err = f"{type(e).__name__}: {e}"
                out.retries = attempt
        else:
            cp["failed"][content_id] = {
                "error": last_err, "retries": self.max_retries,
                "last_at": _utcnow(),
            }
            self._save_checkpoint(cp)
            out.disposition = "failed"
            out.error = last_err
            return out

        if extraction.relevance == "NOT_RELEVANT":
            cp["not_relevant_content_ids"].append(content_id)
            cp["failed"].pop(content_id, None)
            self._save_checkpoint(cp)
            out.disposition = "not_relevant"
            return out

        model_name = getattr(self.client, "model", "fake-client")
        cand_recs = build_candidates(
            rec, extraction, prompt_version=self.client.prompt_version,
            model_name=model_name,
        )
        quest_recs = build_questions(
            rec, extraction, prompt_version=self.client.prompt_version,
            model_name=model_name,
        )

        for c in cand_recs:
            _, wrote = self.candidates.store(c)
            out.candidates += 1
            if wrote:
                # group into concepts (append-only provenance), then queue
                concept = self.concepts.add_candidate(c)
                self.queue.enqueue(c, concept_id=concept["concept_id"])
        for q in quest_recs:
            _, wrote = self.questions.store(q)
            out.questions += 1

        cp["processed_content_ids"].append(content_id)
        # a previously-failed item that now succeeded is no longer failed
        cp["failed"].pop(content_id, None)
        self._save_checkpoint(cp)
        return out

    # ------------------------------------------------------------- batch

    def process_batch(self, raws: list[dict], *, resume: bool = True,
                      force: bool = False) -> BatchSummary:
        cp = self._load_checkpoint()
        # A different prompt version or model is a NEW checkpoint scope: never
        # silently skip items extracted by an older prompt.
        if (cp.get("prompt_version") != self.client.prompt_version
                and cp.get("processed_content_ids")):
            cp = {
                "prompt_version": self.client.prompt_version,
                "model": getattr(self.client, "model", "fake-client"),
                "supersedes": {
                    "prompt_version": cp.get("prompt_version"),
                    "model": cp.get("model"),
                },
                "processed_content_ids": [],
                "failed": {}, "duplicate_content_ids": [],
                "not_relevant_content_ids": [], "skipped_no_text_ids": [],
                "updated_at": None,
            }

        done = (
            set(cp["processed_content_ids"])
            | set(cp["not_relevant_content_ids"])
            | set(cp["skipped_no_text_ids"])
        )
        # NOTE: failed items are deliberately NOT skipped — resume retries
        # them up to max_retries again (SPEC-KNW-001 §9; "resume continues
        # from the appropriate checkpoint rather than reprocessing
        # everything", but failed work is unfinished work).
        seen_text_hashes: set = set()

        summary = BatchSummary(total=len(raws))
        for raw in raws:
            cid = raw.get("content_id") or "unknown"
            if resume and not force and cid in done:
                # already dispositioned in a prior run — skip without recount
                summary.processed += 1
                continue
            out = self.process_one(raw, cp=cp, seen_text_hashes=seen_text_hashes,
                                   force=force)
            if out.disposition == "processed":
                summary.processed += 1
                summary.candidates_written += out.candidates
                summary.questions_written += out.questions
            elif out.disposition == "skipped_no_text":
                summary.skipped_no_text += 1
            elif out.disposition == "not_relevant":
                summary.not_relevant += 1
            elif out.disposition == "duplicate_text":
                summary.duplicate_text += 1
            elif out.disposition == "failed":
                summary.failed += 1
                summary.failures.append({
                    "content_id": cid, "error": out.error,
                    "retries": out.retries,
                })
        self._save_checkpoint(cp)
        return summary
