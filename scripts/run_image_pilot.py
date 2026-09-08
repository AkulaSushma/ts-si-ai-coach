"""Reproducible bounded pilot on the repository's exact real JPEG.
No OCR or independent factual verification is claimed: extracted text below was
visually read from the actual source by Notion AI and is explicitly so attributed.
Run with --source-root pointing at the original collection and --state-root at a
separate runtime directory. Never mutates the original media.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_store import file_digest
from media_intake import Intake


def run(source_root, state_root):
    name = 'IMG_20260906_192918.jpg'
    before = file_digest(Path(source_root) / name)
    if before != '6a6af245d2e4e37d5e039a11182bf0fd6ec5358db6f4a1cf7cd22f5c8d2ab8bf':
        raise ValueError('Pilot requires the exact inspected image, not a substitute')
    intake = Intake(source_root, state_root)
    asset = intake.register(name, 'SI-Constable-media-ce938a9')
    probe = intake.probe(asset, name)
    if probe['payload']['result'] != 'PASS':
        raise ValueError('Actual image metadata probe failed')
    span = intake.span(asset, probe, {'kind': 'image_region', 'xyxy': [0, 0, 928, 994]},
        'LADAKH', 'en', {'processor': 'Notion AI', 'version': 'session010-visual-1',
            'method': 'MODEL_VISUAL', 'model': 'Notion AI', 'prompt_version': 'inspect-visible-label-v1'})
    source = intake.candidate(span, origin='SOURCE_DERIVED', text='LADAKH',
        uncertainty='Visible label only; publisher, original URL and factual map accuracy unverified.')
    interpretation = intake.candidate(span, origin='MODEL_DERIVED',
        text='The image combines spatial location, colour, arrows and short letter labels. A future retrieval exercise could hide labels and ask the learner to reconstruct their locations, after the underlying geography is independently checked. This is a proposed learning representation, not a source quotation or demonstrated retention benefit.',
        uncertainty='Analyst proposal; no measured recognition/retention benefit and no PYQ connection established.')
    assert file_digest(Path(source_root) / name) == before
    return {'status': 'PARTIAL', 'asset': asset, 'probe': probe, 'span': span,
        'source_candidate': source, 'model_candidate': interpretation,
        'verified_knowledge_created': 0, 'videos_processed': 0,
        'source_ledger_integration': 'BLOCKED_PENDING_REPOSITORY_REGISTRATION'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--state-root', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source_root, args.state_root), ensure_ascii=False, indent=2))
