"""Shared fixtures for knowledge-pipeline tests: temp stores, a scripted
client factory, and the committed fixture dataset. No network, ever."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.knowledge.client import GlmClient  # noqa: E402
from app.knowledge.stores import (  # noqa: E402
    CandidateStore, ConceptStore, ProcessedStore, QuestionStore,
)
from app.knowledge.verify_queue import VerificationQueue  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "raw_records"


class TmpStores:
    """Temp data-root so tests never touch the real data/ tree."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="knw-test-")

    def __enter__(self):
        root = Path(self._tmp.name)
        return {
            "root": root,
            "processed": ProcessedStore(base=root / "processed"),
            "candidates": CandidateStore(base=root / "knowledge" / "candidates"),
            "questions": QuestionStore(base=root / "knowledge" / "questions"),
            "concepts": ConceptStore(base=root / "knowledge" / "concepts"),
            "queue": VerificationQueue(path=root / "knowledge" / "verification_queue.jsonl"),
            "checkpoint": root / "knowledge" / "checkpoint.json",
        }

    def __exit__(self, *exc):
        self._tmp.cleanup()
        return False


def fixture_raws() -> list[dict]:
    out = []
    for p in sorted(FIXTURE_DIR.glob("*.json")):
        if p.name in ("manifest.json", "model_script.json"):
            continue
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def fixture_script() -> dict:
    return json.loads((FIXTURE_DIR / "model_script.json").read_text(encoding="utf-8"))


class ScriptedClient(GlmClient):
    """Deterministic stand-in for the GLM client: same extract() contract,
    zero network. Responses keyed by content_id; an unscripted id raises
    rather than inventing output."""

    def __init__(self, responses: dict | None = None,
                 prompt_version: str | None = None):
        self.prompt_version = prompt_version or "knowledge-extraction-v1"
        self.model = "scripted-test-client (no network)"
        self._responses = (
            responses if responses is not None else fixture_script()["responses"]
        )
        self.calls = 0

    def extract(self, processed):
        self.calls += 1
        from app.knowledge.extraction_schema import validate_extraction
        try:
            payload = self._responses[processed.content_id]
        except KeyError:
            raise RuntimeError(
                f"no scripted response for {processed.content_id!r}"
            ) from None
        return validate_extraction(payload)


class ExplodingOnceClient(ScriptedClient):
    """Fails the first N calls for given content_ids, then succeeds."""

    def __init__(self, fail_first: dict[str, int] | None = None, **kw):
        super().__init__(**kw)
        self.fail_first = fail_first or {}
        self._failed: dict[str, int] = {}

    def extract(self, processed):
        n = self.fail_first.get(processed.content_id, 0)
        if self._failed.get(processed.content_id, 0) < n:
            self._failed[processed.content_id] = (
                self._failed.get(processed.content_id, 0) + 1
            )
            raise RuntimeError(f"transient failure for {processed.content_id}")
        return super().extract(processed)


class AlwaysFailingClient(ScriptedClient):
    """Fails every call — for model-failure and batch-isolation tests."""

    def extract(self, processed):
        self.calls += 1
        raise RuntimeError("model unavailable")
