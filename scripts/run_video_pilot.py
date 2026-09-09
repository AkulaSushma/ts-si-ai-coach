"""SPEC-INT-013 runner: bounded, real-asset video intelligence pilot.

Processes exactly one committed video from a real local checkout and prints a
stage report. Identity is checked against the committed Git blob SHA-1 before
anything is derived, so the report can only describe the real committed bytes.

The state and artifact roots must sit outside the media source root so raw media
can never be written to or overwritten. Re-running the same command on the same
unchanged file reuses prior successful stages instead of duplicating work.

This runner never asserts a teaching claim, translation, publisher or PYQ link.
It produces located evidence plus an explicit list of capability gaps. See
specs/features/session013-video-intelligence.md for the invocation example.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .video_pipeline import VideoPipeline, default_registry, stage_summary
except ImportError:  # direct execution
    from video_pipeline import VideoPipeline, default_registry, stage_summary


def build_parser():
    parser = argparse.ArgumentParser(description='Bounded single-video pilot')
    parser.add_argument('--source-root', required=True,
                        help='Local checkout root that contains the real media')
    parser.add_argument('--relative', required=True,
                        help='Path of one video inside --source-root')
    parser.add_argument('--git-blob', required=True,
                        help='Committed Git blob SHA-1 of that exact asset')
    parser.add_argument('--state-root', required=True)
    parser.add_argument('--artifact-root', required=True)
    parser.add_argument('--collection', required=True)
    parser.add_argument('--language-hint', default=None,
                        choices=['te', 'en', 'mixed', 'und'],
                        help='Expected teaching language; omit if unknown')
    parser.add_argument('--max-frames', type=int, default=12,
                        help='Upper bound on sampled frames for this bounded pilot')
    parser.add_argument('--out', default=None, help='Optional JSON report path')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_frames < 1 or args.max_frames > 24:
        parser.error('This bounded pilot allows 1 to 24 sampled frames')
    pipeline = VideoPipeline(args.source_root, args.state_root, args.artifact_root,
                             registry=default_registry())
    try:
        report = pipeline.run(args.relative, args.collection, args.git_blob,
                              language_hint=args.language_hint,
                              max_frames=args.max_frames)
    except (OSError, ValueError) as exc:
        report = {'relative_path': args.relative, 'status': 'BLOCKED',
                  'error': str(exc), 'stages': {}, 'spans': [],
                  'capability_gaps': [{'stage': 'identity', 'reason': str(exc)}]}
    report['stage_status'] = stage_summary(report)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    print(text)
    return 0 if report.get('status') in {'PARTIAL', 'COMPLETE'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
