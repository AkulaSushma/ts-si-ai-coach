"""SPEC-INT-010: bounded local intake, no downloads or trusted knowledge writes.

Single-process pilot implementation. Journal scans are linear; a transactional
indexed scheduler for bulk/concurrent workers is deliberately not claimed here.
ffprobe is optional and missing/failed probes remain auditable attempts.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import subprocess
try:
    from .evidence_store import Journal, file_digest, revision, safe_file
except ImportError:
    from evidence_store import Journal, file_digest, revision, safe_file


class Intake:
    def __init__(self, source_root, state_root):
        self.source = Path(source_root).resolve()
        state = Path(state_root).resolve()
        if state.is_relative_to(self.source) or self.source.is_relative_to(state):
            raise ValueError('State and raw source roots must be disjoint')
        self.journal = Journal(state)

    def register(self, relative, collection_id):
        if not collection_id:
            raise ValueError('Collection identity required')
        path = safe_file(self.source, relative)
        sha = file_digest(path)
        assets = [r for r in self.journal.records('asset') if r['payload']['sha256'] == sha]
        if assets:
            asset = assets[0]
        else:
            asset = self.journal.append('asset', {'sha256': sha, 'bytes': path.stat().st_size,
                'format_hint': path.suffix.lower(), 'near_duplicate_assessment': None})
        occurrence = {'asset_id': asset['id'], 'collection_id': collection_id,
            'relative_path': str(Path(relative)), 'source_url': None, 'publisher': None,
            'published_at': None, 'acquisition_route': 'USER_SUPPLIED_LOCAL_FILE'}
        if not any(r['payload'] == occurrence for r in self.journal.records('occurrence')):
            self.journal.append('occurrence', occurrence)
        return asset

    def probe(self, asset, relative, *, executable='ffprobe', processor_version='ffprobe-v1'):
        path = safe_file(self.source, relative)
        if file_digest(path) != asset['payload']['sha256']:
            raise ValueError('Source changed; register a new revision')
        try:
            version = subprocess.run([executable, '-version'], capture_output=True,
                text=True, timeout=10, check=True).stdout.splitlines()[0]
            key = revision({'asset': asset['payload']['sha256'], 'processor': processor_version,
                            'engine': version, 'arguments': 'show_format,show_streams,json'})
            for r in self.journal.records('attempt'):
                if r['payload'].get('job_key') == key and r['payload']['result'] == 'PASS':
                    return r
            completed = subprocess.run([executable, '-v', 'error', '-show_format',
                '-show_streams', '-of', 'json', str(path)], capture_output=True,
                text=True, timeout=60, check=True)
            metadata = json.loads(completed.stdout)
            if not metadata.get('streams') or file_digest(path) != asset['payload']['sha256']:
                raise ValueError('No media streams or source changed during probe')
            return self.journal.append('attempt', {'asset_id': asset['id'], 'job_key': key,
                'stage': 'probe', 'processor_version': processor_version, 'engine': version,
                'result': 'PASS', 'metadata': metadata, 'stderr': completed.stderr})
        except (OSError, subprocess.SubprocessError, ValueError, IndexError) as exc:
            return self.journal.append('attempt', {'asset_id': asset['id'], 'job_key': None,
                'stage': 'probe', 'processor_version': processor_version, 'engine': None,
                'result': 'FAIL', 'error': str(exc)})

    def span(self, asset, probe, location, original_text, language, extraction):
        p = probe['payload']
        if probe not in self.journal.records('attempt') or asset not in self.journal.records('asset'):
            raise ValueError('Unregistered evidence inputs')
        if p['result'] != 'PASS' or p['asset_id'] != asset['id']:
            raise ValueError('A matching successful probe is required')
        if not isinstance(original_text, str) or not original_text.strip() or language not in {'en', 'te', 'mixed', 'und'}:
            raise ValueError('Original text and language required')
        if not all(isinstance(extraction.get(k), str) and extraction[k].strip()
                   for k in ('processor', 'version', 'method')):
            raise ValueError('Extraction provenance required')
        if extraction['method'] not in {'HUMAN_TRANSCRIPTION', 'MODEL_VISUAL', 'OCR', 'ASR'}:
            raise ValueError('Unknown extraction method')
        if extraction['method'] == 'MODEL_VISUAL' and not all(extraction.get(k) for k in ('model', 'prompt_version')):
            raise ValueError('Model/prompt provenance required')
        streams = p['metadata']['streams']
        if location.get('kind') == 'image_region':
            if asset['payload']['format_hint'] not in {'.jpg', '.jpeg', '.png', '.webp'}:
                raise ValueError('Video regions require frame timestamps; not supported by image spans')
            video = next(s for s in streams if s.get('codec_type') == 'video')
            box = location['xyxy']
            if len(box) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in box):
                raise ValueError('Invalid region')
            x1, y1, x2, y2 = box
            if not (0 <= x1 < x2 <= video['width'] and 0 <= y1 < y2 <= video['height']):
                raise ValueError('Region outside image')
        elif location.get('kind') == 'video_interval':
            if asset['payload']['format_hint'] not in {'.mp4', '.mkv', '.mov', '.webm'}:
                raise ValueError('A video interval requires a video asset')
            a, b = location['start_seconds'], location['end_seconds']
            duration = float(p['metadata']['format']['duration'])
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in (a, b)) or not (0 <= a < b <= duration):
                raise ValueError('Invalid time interval')
        else:
            raise ValueError('Unsupported evidence location')
        payload = {'asset_id': asset['id'], 'asset_sha256': asset['payload']['sha256'],
            'probe_id': probe['id'], 'location': location, 'original_text': original_text,
            'language': language, 'extraction': extraction, 'fidelity_status': 'UNVERIFIED'}
        for r in self.journal.records('span'):
            if r['payload'] == payload:
                return r
        return self.journal.append('span', payload)

    def candidate(self, span, *, origin, text, uncertainty, text_te=None):
        if span not in self.journal.records('span'):
            raise ValueError('Unknown or changed evidence span')
        if origin not in {'SOURCE_DERIVED', 'MODEL_DERIVED'} or not text or not uncertainty:
            raise ValueError('Explicit origin, text and uncertainty required')
        if origin == 'SOURCE_DERIVED' and text != span['payload']['original_text']:
            raise ValueError('Source claim must preserve extracted wording; paraphrase is interpretation')
        payload = {'span_id': span['id'], 'origin': origin,
            'provenance_tier': 'T3_EXPERT' if origin == 'SOURCE_DERIVED' else 'T4_AI',
            'text': text, 'text_te': text_te, 'uncertainty': uncertainty, 'uncertainty_te': None,
            'verification_status': 'UNVERIFIED', 'confidence': None,
            'pyq_links': [], 'relationships_status': 'NOT_EVALUATED'}
        for r in self.journal.records('candidate'):
            if r['payload'] == payload:
                return r
        return self.journal.append('candidate', payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--state-root', required=True)
    parser.add_argument('--collection', required=True)
    parser.add_argument('--file', action='append', required=True)
    args = parser.parse_args()
    if len(args.file) > 3:
        parser.error('Pilot is limited to three explicitly selected files')
    intake = Intake(args.source_root, args.state_root)
    results = []
    for relative in args.file:
        try:
            asset = intake.register(relative, args.collection)
            results.append(intake.probe(asset, relative))
        except (OSError, ValueError) as exc:
            results.append({'relative_path': relative, 'result': 'FAIL', 'error': str(exc)})
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r.get('payload', {}).get('result') == 'PASS' for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
