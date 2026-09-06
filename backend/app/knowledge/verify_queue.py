"""Verification queue (SPEC-KNW-001 §8) — architecture, not verification.

The queue is the ONLY handoff between candidate knowledge and the future
verification stage. It performs no verification, emits no VERIFIED verdicts,
and resolves the required verifier provider at queue time from
config/model_routing.json so the author/verifier provider separation is
recorded per item, mechanically.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTING_PATH = ROOT / "config" / "model_routing.json"

VERIFICATION_ROLE = "VERIFICATION"
AUTHOR_ROLE = "KNOWLEDGE_EXTRACTION"


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_verifier_provider() -> tuple[str | None, str]:
    """Resolve the verifier provider for KNOWLEDGE_EXTRACTION output.

    Returns (provider_or_None, reason). AUTO_NOT_AUTHOR resolves to any
    candidate provider other than the author's — same runtime rule the
    verification stage will apply, recorded now so the queue line is
    self-describing.
    """
    cfg = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))
    roles = cfg["roles"]
    author_provider = roles[AUTHOR_ROLE]["provider"]
    verifier = roles.get(VERIFICATION_ROLE, {})
    vp = verifier.get("provider")
    if vp == "AUTO_NOT_AUTHOR":
        candidates = [
            c for c in (verifier.get("candidates") or [])
            if c != author_provider
        ]
        if not candidates:
            return None, (
                f"no candidate verifier provider other than the author "
                f"provider {author_provider!r} exists; item cannot be queued "
                f"for independent verification"
            )
        return candidates[0], (
            f"AUTO_NOT_AUTHOR resolved against author provider "
            f"{author_provider!r}"
        )
    if vp == author_provider:
        return None, (
            f"routing assigns the author provider {author_provider!r} to "
            f"VERIFICATION; refusing to queue a self-verification"
        )
    return vp, f"fixed provider {vp!r} differs from author {author_provider!r}"


class VerificationQueue:
    """Append-only JSONL queue. `enqueue` never sets any status except
    UNVERIFIED; `verify` does not exist by design."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else (
            ROOT / "data" / "knowledge" / "verification_queue.jsonl"
        )

    def enqueue(self, candidate: dict, *, concept_id: str | None = None) -> dict:
        provider, reason = resolve_verifier_provider()
        line = {
            "candidate_id": candidate["candidate_id"],
            "concept_id": concept_id,
            "verification_status": "UNVERIFIED",
            "author_role": AUTHOR_ROLE,
            "author_provider": candidate["provenance"].get("extraction_model"),
            "required_verifier_role": VERIFICATION_ROLE,
            "required_verifier_provider": provider,
            "queue_note": reason,
            "queued_at": _utcnow(),
        }
        if provider is None:
            line["queue_status"] = "QUEUED_BLOCKED_NO_INDEPENDENT_VERIFIER"
        else:
            line["queue_status"] = "QUEUED"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
        return line
