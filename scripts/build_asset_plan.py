"""Build the durable expert-media asset plan from repository ground truth.

The plan records, for every committed asset in the media collection, its exact
committed Git blob identity, byte size, media class and the treatment the
pipeline should apply. It records what is *known* from the repository only:
attribution, publisher, transcript and PYQ relationships are deliberately null
because they have not been observed.

Two authoritative inputs are supported:

--listing   JSON array of {name, size, sha, type} exactly as returned by a
            GitHub repository directory listing of the collection.
--source-root  A local checkout directory; Git blob SHA-1 is recomputed from the
            real bytes, which also proves the checkout matches the commit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .video_intake import git_blob_sha1, media_class
except ImportError:  # direct execution
    from video_intake import git_blob_sha1, media_class

COLLECTION = 'SI & Constable Concepts Videos & photos'

TREATMENT = {
    'VIDEO': {
        'stages': ['identity', 'probe', 'frame_sampling', 'asr', 'ocr_on_frames',
                   'span_extraction', 'candidate_proposal'],
        'evidence_location': 'video_interval',
    },
    'IMAGE': {
        'stages': ['identity', 'probe', 'ocr', 'span_extraction', 'candidate_proposal'],
        'evidence_location': 'image_region',
    },
    'UNSUPPORTED': {'stages': ['identity'], 'evidence_location': None},
}


def entry(name, size, blob):
    kind = media_class(name)
    return {
        'relative_path': f'{COLLECTION}/{name}',
        'file_name': name,
        'collection_id': 'SI-Constable-media-ce938a9',
        'media_class': kind,
        'bytes': size,
        'git_blob_sha1': blob,
        'sha256': None,
        'treatment': TREATMENT[kind],
        'processing_state': 'NOT_STARTED',
        'source_url': None,
        'publisher': None,
        'published_at': None,
        'attribution_status': 'UNKNOWN_NOT_OBSERVED',
        'transcript_status': 'ABSENT',
        'ocr_status': 'ABSENT',
        'pyq_relationships_status': 'NOT_EVALUATED',
    }


def from_listing(path):
    listing = json.loads(Path(path).read_text(encoding='utf-8'))
    return [entry(item['name'], item['size'], item['sha'])
            for item in listing if item.get('type', 'file') == 'file']


def from_checkout(source_root):
    root = Path(source_root).resolve() / COLLECTION
    if not root.is_dir():
        raise ValueError(f'Collection directory not found under {source_root}')
    return [entry(p.name, p.stat().st_size, git_blob_sha1(p))
            for p in sorted(root.iterdir()) if p.is_file()]


def build(assets):
    videos = [a for a in assets if a['media_class'] == 'VIDEO']
    images = [a for a in assets if a['media_class'] == 'IMAGE']
    return {
        'schema': 'expert-media-asset-plan',
        'schema_version': 1,
        'collection': COLLECTION,
        'collection_id': 'SI-Constable-media-ce938a9',
        'observed_from': 'repository directory listing / local checkout bytes',
        'totals': {
            'assets': len(assets),
            'videos': len(videos),
            'images': len(images),
            'unsupported': len(assets) - len(videos) - len(images),
            'bytes': sum(a['bytes'] for a in assets),
        },
        'coverage_statement': 'Inventory is complete for identity and size only. '
                              'Content, attribution and teaching claims are unobserved.',
        'assets': sorted(assets, key=lambda a: a['file_name']),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--listing')
    group.add_argument('--source-root')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assets = from_listing(args.listing) if args.listing else from_checkout(args.source_root)
    plan = build(assets)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # JSON Lines: header first, then one asset per line. Compact, diff-friendly and
    # streamable when the plan grows beyond this collection.
    header = {k: v for k, v in plan.items() if k != 'assets'}
    header['record'] = 'header'
    header['treatment_by_media_class'] = TREATMENT
    header['unobserved_defaults'] = {
        'sha256': None, 'source_url': None, 'publisher': None, 'published_at': None,
        'attribution_status': 'UNKNOWN_NOT_OBSERVED', 'transcript_status': 'ABSENT',
        'ocr_status': 'ABSENT', 'pyq_relationships_status': 'NOT_EVALUATED',
        'processing_state': 'NOT_STARTED',
    }
    keep = ('file_name', 'media_class', 'bytes', 'git_blob_sha1')
    lines = [json.dumps(header, ensure_ascii=False, sort_keys=True)]
    lines += [json.dumps({k: a[k] for k in keep}, ensure_ascii=False, sort_keys=True)
              for a in plan['assets']]
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(plan['totals'], indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
