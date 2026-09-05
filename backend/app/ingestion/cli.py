"""Command line interface for the ingestion subsystem (SPEC-ING-001 §4.10).

Run from the project folder:

    python scripts/ingest.py extract                    # all enabled sources
    python scripts/ingest.py extract --source IG001     # one registered source
    python scripts/ingest.py extract --url https://www.instagram.com/example/
    python scripts/ingest.py resume [--source IG001]    # resume interrupted
    python scripts/ingest.py status [IG001]              # registry + checkpoints
    python scripts/ingest.py add --url https://www.instagram.com/example/

Every command is safe to run twice. `status` makes no network requests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from .registry import Source, add_source, load_registry
from .runner import IngestionRunner

ROOT = Path(__file__).resolve().parents[3]


def _print_summary(s) -> None:
    print(
        f"  {s.source_id}: status={s.status} discovered={s.discovered} "
        f"extracted={s.extracted} duplicate={s.duplicate} failed={s.failed} "
        f"inaccessible={s.inaccessible}"
    )
    if s.stop_reason:
        print(f"    stop_reason: {s.stop_reason}")
    if s.manifest_path:
        print(f"    manifest: {s.manifest_path}")


def _ad_hoc_source(url: str, max_items: int) -> Source:
    """Build an unregistered Source for direct-URL extraction.

    The source_id is derived from the URL hash so checkpoints/raw files from
    a direct-URL run are stable across repeated invocations, and never collide
    with registered IG### ids.
    """
    from .registry import _parse_profile_url

    username = _parse_profile_url("instagram", url, "direct-url")
    digest = hashlib.sha256(username.lower().encode()).hexdigest()[:8].upper()
    return Source(
        source_id=f"IGURL{digest}",
        platform="instagram",
        username=username,
        profile_url=f"https://www.instagram.com/{username}/",
        enabled=True,
        max_items=max_items,
    )


def cmd_extract(args) -> int:
    runner = IngestionRunner()
    sources, _ = load_registry()

    if args.url:
        try:
            src = _ad_hoc_source(args.url, args.max_items or 299)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"Direct-URL extraction (unregistered): {src.username}")
        summary = runner.extract_source(src, force=args.force)
        _print_summary(summary)
        # blocked is a legitimate, recorded outcome, but not success
        return 0 if summary.status in ("complete", "partial") else 1

    if args.source:
        match = [s for s in sources if s.source_id == args.source]
        if not match:
            print(f"error: source '{args.source}' is not in the registry", file=sys.stderr)
            return 2
        if not match[0].enabled and not args.force:
            print(f"skipped: {args.source} is disabled (use --force to extract anyway)")
            return 0
        summary = runner.extract_source(match[0], force=args.force)
        _print_summary(summary)
        return 0 if summary.status in ("complete", "partial", "blocked") else 1

    enabled = [s for s in sources if s.enabled]
    print(f"Extracting {len(enabled)} enabled source(s) of {len(sources)} registered")
    summaries = runner.extract_many(enabled, force=args.force)
    for s in summaries:
        _print_summary(s)
    ok = sum(1 for s in summaries if s.status == "complete")
    print(f"batch: {ok}/{len(summaries)} complete")
    return 0


def cmd_resume(args) -> int:
    runner = IngestionRunner()
    sources, _ = load_registry()
    targets = [s for s in sources if s.enabled]
    if args.source:
        match = [s for s in sources if s.source_id == args.source]
        if not match:
            print(f"error: source '{args.source}' is not in the registry", file=sys.stderr)
            return 2
        targets = match

    resumed = 0
    for s in targets:
        cp_path = ROOT / "data" / "ingestion" / "checkpoints" / f"{s.source_id}.json"
        if not cp_path.is_file():
            continue
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        if cp.get("status") in ("partial", "in_progress", "blocked"):
            print(f"resuming {s.source_id} ({cp.get('status')}, "
                  f"{cp['items']['extracted']} items so far)")
            _print_summary(runner.extract_source(s))
            resumed += 1
    if resumed == 0:
        print("nothing to resume: no partial/in-progress/blocked sources")
    return 0


def cmd_status(args) -> int:
    sources, defaults = load_registry()
    cp_dir = ROOT / "data" / "ingestion" / "checkpoints"
    ids = [args.source] if args.source else [s.source_id for s in sources]
    if args.source and args.source not in {s.source_id for s in sources}:
        print(f"error: source '{args.source}' is not in the registry", file=sys.stderr)
        return 2

    print(f"registry: {len(sources)} sources, defaults={defaults}")
    for sid in ids:
        src = next((s for s in sources if s.source_id == sid), None)
        cp_path = cp_dir / f"{sid}.json"
        if not cp_path.is_file():
            print(f"  {sid} [{src.platform if src else '?'}] "
                  f"username={src.username if src else '?'} "
                  f"enabled={src.enabled if src else '?'} "
                  f"max_items={src.max_items if src else '?'} "
                  f"checkpoint=none")
            continue
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
        it = cp["items"]
        print(
            f"  {sid} [{cp['platform']}] username={src.username} "
            f"status={cp['status']} discovered={it['discovered']} "
            f"extracted={it['extracted']} duplicate={it['duplicate']} "
            f"failed={it['failed']} inaccessible={it['inaccessible']} "
            f"max_items={cp['max_items']}"
        )
        if cp.get("stop_reason"):
            print(f"    stop_reason: {cp['stop_reason']}")
    return 0


def cmd_add(args) -> int:
    try:
        src = add_source(args.url, max_items=args.max_items,
                         notes=args.notes)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(
        f"registered {src.source_id}: {src.username} "
        f"(max_items={src.max_items}, enabled={src.enabled}). "
        f"It will be included in the next 'extract' run — no code change needed."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ingest.py",
        description="Multi-platform source ingestion (Instagram first)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("extract", help="extract one or all enabled sources")
    ex.add_argument("--source", help="source_id from the registry, e.g. IG001")
    ex.add_argument("--url", help="direct Instagram profile URL (unregistered)")
    ex.add_argument("--max-items", type=int, default=None,
                    help="cap for direct-URL extraction (default 299)")
    ex.add_argument("--force", action="store_true",
                    help="re-extract even if the checkpoint says complete")
    ex.set_defaults(func=cmd_extract)

    rs = sub.add_parser("resume", help="resume interrupted extractions")
    rs.add_argument("--source", help="limit resume to one source_id")
    rs.set_defaults(func=cmd_resume)

    st = sub.add_parser("status", help="show registry and checkpoint state")
    st.add_argument("source", nargs="?", help="optional source_id")
    st.set_defaults(func=cmd_status)

    ad = sub.add_parser("add", help="register a new Instagram profile URL")
    ad.add_argument("--url", required=True, help="Instagram profile URL")
    ad.add_argument("--max-items", type=int, default=None)
    ad.add_argument("--notes", default=None)
    ad.set_defaults(func=cmd_add)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
