"""Deterministic, documented exam-relevance scoring (SPEC-KNW-001 §7).

Every number this module produces comes from a rule in
docs/relevance_scale.md, never from a model or an assumption. The full scale
document is committed next to the code and is the authority for these rules.

Rules summary (see docs/relevance_scale.md for the full statement):
- si_relevance / constable_relevance: 1 iff the candidate's subject maps to a
  verified official syllabus node for that exam's paper list (the mapping
  table is data: config/subject_syllabus_map.json, citing OFF-SYL node ids).
  The SI and Constable recruitments share the notification's syllabus for SI
  (Civil) 2026; the Constable-specific notification (DOC-OFF-004) is NOT yet
  retrieved, so constable_relevance currently derives from the SI syllabus
  and is flagged provisional in the scale doc — never silently assumed.
- telangana_relevance: 1 iff subject is Telangana-specific, else 0.
- pyq_similarity: null until a PYQ database exists (no denominator, no
  number). Never a guess.
- revision_priority: integer 0-5 from four additive rules, capped at 5.
- confidence: copied from the extraction model, labelled
  model_self_reported; never interpreted as accuracy.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAP_PATH = ROOT / "config" / "subject_syllabus_map.json"

from .taxonomy import KNOWLEDGE_TYPES, TELANGANA_SUBJECTS  # noqa: E402


def _load_map() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def _subject_on_syllabus(subject: str, exam: str, mapping: dict) -> bool:
    entry = mapping.get("subjects", {}).get(subject)
    if not entry:
        return False
    return bool(entry.get("papers_by_exam", {}).get(exam))


def telangana_relevance(subject: str) -> int:
    return 1 if subject in TELANGANA_SUBJECTS else 0


def revision_priority(subject: str, knowledge_type: str,
                      published_at: str | None, now_iso: str | None = None) -> int:
    """0-5, additive then capped. Rules in docs/relevance_scale.md §4."""
    from datetime import datetime, timezone

    pts = 0
    mapping = _load_map()
    # R1: subject on the verified syllabus (either exam) -> +2
    on_syllabus = (
        _subject_on_syllabus(subject, "si", mapping)
        or _subject_on_syllabus(subject, "constable", mapping)
    )
    if on_syllabus:
        pts += 2
    # R2: Telangana-specific -> +1
    if telangana_relevance(subject):
        pts += 1
    # R3: high-recall knowledge types -> +1
    if knowledge_type in ("FACT", "DATE", "LAW", "ARTICLE", "AMENDMENT"):
        pts += 1
    # R4: CURRENT_AFFAIRS within 12 months of 'now' -> +1 (else 0 for this rule)
    if knowledge_type == "CURRENT_AFFAIRS" and published_at:
        try:
            then = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            then = None
        ref = None
        if now_iso:
            try:
                ref = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
            except ValueError:
                ref = None
        if ref is None:
            ref = datetime.now(timezone.utc)
        if then is not None and abs((ref - then).days) <= 365:
            pts += 1
    return min(pts, 5)


def exam_relevance_scores(subject: str, knowledge_type: str,
                          published_at: str | None = None) -> dict:
    """The full scores block for a candidate (SPEC-KNW-001 §7)."""
    mapping = _load_map()
    return {
        "si_relevance": 1 if _subject_on_syllabus(subject, "si", mapping) else 0,
        "constable_relevance": (
            1 if _subject_on_syllabus(subject, "constable", mapping) else 0
        ),
        "constable_relevance_basis": (
            "PROVISIONAL — derived from the SI (Civil) 2026 syllabus because the "
            "Constable notification (DOC-OFF-004) is not yet retrieved (B-09). "
            "Recomputed when it is."
        ),
        "telangana_relevance": telangana_relevance(subject),
        "pyq_similarity": None,   # no PYQ database exists; never a guess
        "pyq_similarity_basis": "null until a PYQ set exists (B-02): no denominator, no number",
        "revision_priority": revision_priority(subject, knowledge_type, published_at),
        "scoring_method": "docs/relevance_scale.md v1, deterministic rules only",
    }
