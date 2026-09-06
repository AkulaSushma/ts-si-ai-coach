"""Deduplication and cross-source corroboration (SPEC-KNW-001 §6).

Deterministic, no model calls. Two candidates express the same concept when
their normalized, stopword-stripped token SETS (plus knowledge_type) match —
order and phrasing are irrelevant, so 'A added B' and 'B was added by A' map
to the same concept. A concept keeps ONE representative text and EVERY
supporting source — provenance is appended, never merged away. Corroboration
explicitly does not verify: a concept with many supporters is still
UNVERIFIED, and says so in writing.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SYNONYMS_PATH = ROOT / "config" / "dedup_synonyms.json"


def _synonyms() -> dict:
    """Curated surface-verb synonym table (config/dedup_synonyms.json).
    Loaded lazily and cached; a missing file means no canonicalization."""
    global _SYN_CACHE
    try:
        return _SYN_CACHE
    except NameError:
        try:
            _SYN_CACHE = json.loads(
                SYNONYMS_PATH.read_text(encoding="utf-8")
            ).get("synonyms", {})
        except FileNotFoundError:
            _SYN_CACHE = {}
        return _SYN_CACHE

# Stopword list for concept keys. Deliberately small and fixed: it exists so
# active-voice and passive-voice phrasings of the same claim collide; a longer
# list would start conflating genuinely different claims (e.g. dropping 'not'
# would merge a fact with its negation — 'not' is NOT a stopword here).
_STOPWORDS = frozenset({
    "a", "an", "the", "of", "in", "on", "by", "to", "was", "were", "is",
    "are", "and", "for", "with", "as", "at", "that", "this", "it", "its",
    "be", "been", "being", "has", "have", "had", "which", "who", "from",
    "into", "under", "during",
})


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace. Exact-sentence
    comparison basis; the concept key below additionally drops stopwords."""
    t = (text or "").lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def concept_key(knowledge_text: str, knowledge_type: str) -> str:
    """Order-, phrasing- and curated-synonym-insensitive concept key over
    content words plus the knowledge type. Documented in the module docstring
    and in config/dedup_synonyms.json; the 42nd-Amendment fixture pair
    (active vs passive voice, different sources) must collide, and is tested
    to. 'not' and other negation words are never dropped or mapped."""
    syn = _synonyms()
    tokens = sorted({
        syn.get(t, t)
        for t in normalize_text(knowledge_text).split()
        if t not in _STOPWORDS
    })
    basis = "\x1f".join([knowledge_type, *tokens])
    return "CC-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _diversity(supporting: list[dict]) -> str:
    distinct = len({s["source_id"] for s in supporting})
    if distinct <= 1:
        return "SAME_ACCOUNT"
    if distinct <= 3:
        return "FEW_ACCOUNTS"
    return "MANY_ACCOUNTS"


class ConceptIndex:
    """In-memory + on-disk concept grouping over a ConceptStore."""

    def __init__(self, store):
        self.store = store

    def add_candidate(self, candidate: dict) -> dict:
        """Group one candidate into its concept. Returns the concept record
        (created or updated). Existing supporters are preserved (append-only).
        """
        key = concept_key(
            candidate["knowledge_text"], candidate["knowledge_type"]
        )
        prov = candidate["provenance"]
        supporter = {
            "candidate_id": candidate["candidate_id"],
            "source_id": prov["source_id"],
            "content_id": prov["content_id"],
            "source_url": prov["source_url"],
            "published_at": prov["published_at"],
            "prompt_version": prov["prompt_version"],
            "first_seen": _utcnow(),
        }

        existing = self.store.load(key)
        if existing is None:
            concept = {
                "concept_id": key,
                "representative_text": candidate["knowledge_text"],
                "representative_candidate_id": candidate["candidate_id"],
                "subject": candidate["subject"],
                "knowledge_type": candidate["knowledge_type"],
                "source_count": 1,
                "supporting_sources": [supporter],
                "source_diversity": "SAME_ACCOUNT",
                "verification_status": "UNVERIFIED",
                "corroboration_is_not_verification": True,
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
            }
            self.store.upsert_with_support(concept)
            return concept

        # append-only merge; representative text never replaced
        self.store.upsert_with_support({
            "concept_id": key,
            "supporting_sources": [supporter],
            "created_at": _utcnow(),
        })
        merged = self.store.load(key)
        return merged
