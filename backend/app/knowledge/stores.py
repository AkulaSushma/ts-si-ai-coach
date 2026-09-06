"""Atomic file stores for the knowledge pipeline (SPEC-KNW-001 §2).

Layers B, C, E live under data/ (git-ignored runtime products, D-0008):
- processed:  data/processed/<platform>/<source_id>/<content_id>.json
- candidates: data/knowledge/candidates/<candidate_id>.json
- questions:  data/knowledge/questions/<question_id>.json
- concepts:   data/knowledge/concepts/<concept_id>.json

All writes atomic; records immutable once written except where a store method
explicitly appends (concepts add supporting sources, never replace).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent),
                               prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class ProcessedStore:
    def __init__(self, base: Path | None = None):
        self.base = Path(base) if base else ROOT / "data" / "processed"

    def path_for(self, rec) -> Path:
        return self.base / rec.platform / rec.source_id / f"{rec.content_id}.json"

    def has(self, rec) -> bool:
        return self.path_for(rec).is_file()

    def store(self, rec) -> tuple[Path, bool]:
        p = self.path_for(rec)
        if p.is_file():
            return p, False
        payload = {
            "source_id": rec.source_id,
            "platform": rec.platform,
            "content_id": rec.content_id,
            "content_type": rec.content_type,
            "source_url": rec.source_url,
            "published_at": rec.published_at,
            "profile_username": rec.profile_username,
            "test_fixture": rec.is_fixture,
            "text_parts": rec.text_parts,
            "skipped_reason": rec.skipped_reason,
            "processing_hash": rec.processing_hash,
            "hashtags": rec.hashtags,
            "media_counts": rec.media_counts,
            "processed_at": rec.processed_at,
        }
        atomic_write_json(p, payload)
        return p, True


class CandidateStore:
    def __init__(self, base: Path | None = None):
        self.base = Path(base) if base else ROOT / "data" / "knowledge" / "candidates"

    def path_for(self, candidate_id: str) -> Path:
        return self.base / f"{candidate_id}.json"

    def has(self, candidate_id: str) -> bool:
        return self.path_for(candidate_id).is_file()

    def store(self, record: dict) -> tuple[Path, bool]:
        p = self.path_for(record["candidate_id"])
        if p.is_file():
            return p, False
        atomic_write_json(p, record)
        return p, True

    def all_ids(self) -> list[str]:
        if not self.base.is_dir():
            return []
        return sorted(p.stem for p in self.base.glob("*.json"))


class QuestionStore:
    def __init__(self, base: Path | None = None):
        self.base = Path(base) if base else ROOT / "data" / "knowledge" / "questions"

    def path_for(self, question_id: str) -> Path:
        return self.base / f"{question_id}.json"

    def has(self, question_id: str) -> bool:
        return self.path_for(question_id).is_file()

    def store(self, record: dict) -> tuple[Path, bool]:
        p = self.path_for(record["question_id"])
        if p.is_file():
            return p, False
        atomic_write_json(p, record)
        return p, True


class ConceptStore:
    def __init__(self, base: Path | None = None):
        self.base = Path(base) if base else ROOT / "data" / "knowledge" / "concepts"

    def path_for(self, concept_id: str) -> Path:
        return self.base / f"{concept_id}.json"

    def load(self, concept_id: str) -> dict | None:
        p = self.path_for(concept_id)
        if not p.is_file():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def upsert_with_support(self, concept: dict) -> Path:
        """Write concept; if it exists, merge supporting sources append-only.

        Existing supporters are never removed: provenance is only ever added
        (SPEC-KNW-001 §6). The representative text is kept from the first
        sighting; counts recomputed.
        """
        p = self.path_for(concept["concept_id"])
        existing = self.load(concept["concept_id"])
        if existing is not None:
            seen = {(s["source_id"], s["content_id"]) for s in existing["supporting_sources"]}
            for s in concept["supporting_sources"]:
                if (s["source_id"], s["content_id"]) not in seen:
                    existing["supporting_sources"].append(s)
                    seen.add((s["source_id"], s["content_id"]))
            existing["source_count"] = len(existing["supporting_sources"])
            existing["source_diversity"] = _diversity(existing["supporting_sources"])
            existing["updated_at"] = concept.get("created_at")
            atomic_write_json(p, existing)
            return p
        atomic_write_json(p, concept)
        return p


def _diversity(supporting: list[dict]) -> str:
    distinct = len({s["source_id"] for s in supporting})
    if distinct <= 1:
        return "SAME_ACCOUNT"
    if distinct <= 3:
        return "FEW_ACCOUNTS"
    return "MANY_ACCOUNTS"
