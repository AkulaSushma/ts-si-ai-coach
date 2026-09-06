"""CLI for the knowledge pipeline (SPEC-KNW-001 §10).

    python scripts/process_knowledge.py process --fixture      # offline, deterministic
    python scripts/process_knowledge.py process --source IG001 # real raw records (needs key)
    python scripts/process_knowledge.py process --platform instagram
    python scripts/process_knowledge.py status

--fixture runs the committed fixture dataset with a recording fake client —
it is the offline "first GLM test" and makes zero network calls.
Live processing requires GLM_API_KEY and reports honestly when absent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "raw_records"


def _load_raw_records(where: Path) -> list[dict]:
    out = []
    for p in sorted(where.rglob("*.json")):
        if p.name in ("manifest.json", "model_script.json"):
            continue
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def _fixture_client():
    """Deterministic scripted client over the fixture dataset. Responses are
    keyed by content_id; a missing script entry raises so a fixture change
    can never silently produce fake 'model' output."""
    from app.knowledge.client import GlmClient

    script_path = FIXTURE_DIR / "model_script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))

    class ScriptedClient(GlmClient):
        def __init__(self):
            # deliberately bypass GlmClient.__init__: no routing read needed,
            # no key required, and extract() is fully overridden.
            self.prompt_version = script["prompt_version"]
            self.model = "scripted-fixture-client (no network)"
            self._script = script["responses"]

        def extract(self, processed):
            from app.knowledge.extraction_schema import validate_extraction
            try:
                payload = self._script[processed.content_id]
            except KeyError:
                raise RuntimeError(
                    f"fixture script has no response for {processed.content_id!r} — "
                    "a scripted response must be added; the fixture never "
                    "fabricates generic output"
                ) from None
            return validate_extraction(payload)

    return ScriptedClient()


def cmd_process(args) -> int:
    from app.knowledge.pipeline import KnowledgePipeline
    from app.knowledge.stores import (
        CandidateStore, ConceptStore, ProcessedStore, QuestionStore,
    )
    from app.knowledge.verify_queue import VerificationQueue

    base = Path(args.data_dir) if args.data_dir else None

    if args.fixture:
        raws = _load_raw_records(FIXTURE_DIR)
        client = _fixture_client()
    else:
        if not any((ROOT / "data" / "raw").glob(f"{args.platform or '*'}/**/*.json")):
            print(f"no raw records under data/raw/{args.platform or '<any>'}/ — "
                  "nothing to process (Instagram acquisition is BLOCKED, B-08)")
            return 0
        where = (ROOT / "data" / "raw" / args.platform) if args.platform else (ROOT / "data" / "raw")
        raws = []
        for p in sorted(where.rglob("*.json")):
            if p.name == "_profile.json":
                continue
            raw = json.loads(p.read_text(encoding="utf-8"))
            if args.source and raw.get("source_id") != args.source:
                continue
            raws.append(raw)
        try:
            from app.knowledge.client import GlmClient
            client = GlmClient()
        except Exception as e:
            print(f"error initializing live GLM client: {e}", file=sys.stderr)
            return 2

    pipeline = KnowledgePipeline(
        client=client,
        processed_store=ProcessedStore(),
        candidate_store=CandidateStore(),
        question_store=QuestionStore(),
        concept_store=ConceptStore(),
        verify_queue=VerificationQueue(),
        checkpoint_path=(
            ROOT / "data" / "knowledge" / (
                "fixture_checkpoint.json" if args.fixture else "checkpoint.json"
            )
        ),
    )
    summary = pipeline.process_batch(raws, resume=not args.force, force=args.force)
    print(
        f"items: {summary.total} | processed: {summary.processed} | "
        f"no_text: {summary.skipped_no_text} | not_relevant: {summary.not_relevant} | "
        f"duplicate_text: {summary.duplicate_text} | failed: {summary.failed}"
    )
    print(
        f"candidates written: {summary.candidates_written} | "
        f"questions written: {summary.questions_written}"
    )
    if summary.failures:
        for f in summary.failures[:5]:
            print(f"  FAILED {f['content_id']} (retries={f['retries']}): {f['error'][:120]}")
    print("NOTE: all output is CANDIDATE knowledge, UNVERIFIED. Instagram "
          "content was NOT processed." if args.fixture else "")
    return 0


def cmd_status(args) -> int:
    kn = ROOT / "data" / "knowledge"
    for name in ("candidates", "questions", "concepts"):
        d = kn / name
        n = len(list(d.glob("*.json"))) if d.is_dir() else 0
        print(f"{name}: {n}")
    q = kn / "verification_queue.jsonl"
    if q.is_file():
        lines = [json.loads(x) for x in q.read_text(encoding="utf-8").splitlines() if x.strip()]
        statuses: dict = {}
        for ln in lines:
            statuses[ln.get("queue_status")] = statuses.get(ln.get("queue_status"), 0) + 1
        print(f"verification queue: {len(lines)} entries, {statuses}")
        if lines:
            print("  (queue only — nothing is VERIFIED by this pipeline)")
    for cp_name in ("fixture_checkpoint.json", "checkpoint.json"):
        cp = kn / cp_name
        if cp.is_file():
            d = json.loads(cp.read_text(encoding="utf-8"))
            print(
                f"{cp_name}: prompt={d.get('prompt_version')} "
                f"processed={len(d.get('processed_content_ids', []))} "
                f"failed={len(d.get('failed', {}))}"
            )
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="process_knowledge.py")
    sub = p.add_subparsers(dest="command", required=True)
    pr = sub.add_parser("process", help="run the knowledge pipeline")
    pr.add_argument("--fixture", action="store_true",
                    help="use the committed offline fixture dataset")
    pr.add_argument("--platform", default=None)
    pr.add_argument("--source", default=None)
    pr.add_argument("--data-dir", default=None, help=argparse.SUPPRESS)
    pr.add_argument("--force", action="store_true",
                    help="reprocess even if checkpointed")
    pr.set_defaults(func=cmd_process)
    st = sub.add_parser("status", help="show pipeline state (no model calls)")
    st.set_defaults(func=cmd_status)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
