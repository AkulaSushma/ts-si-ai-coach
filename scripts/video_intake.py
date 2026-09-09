"""SPEC-INT-011: video-capable evidence path for expert media.

Adds three capabilities on top of media_intake.Intake:

1. Repository-bound asset identity. Git stores a blob SHA-1 for every committed
   asset, so an operator running this on a real checkout can prove that the local
   bytes are exactly the committed bytes before any intelligence is derived.
2. Deterministic frame derivatives. A frame extracted with ffmpeg is itself
   hashed and recorded as an attempt bound to (asset sha256, timestamp, engine,
   processor version), so any later visual claim can cite a reproducible artifact.
3. Fail-closed extraction slots. When no OCR/ASR engine is available the pipeline
   records a BLOCKED attempt. A BLOCKED attempt can never become an evidence span
   and therefore can never become a candidate or verified claim.

No transcript, translation, publisher or PYQ relationship is ever synthesised here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

try:
    from .evidence_store import file_digest, revision, safe_file
    from .media_intake import Intake
except ImportError:  # direct execution
    from evidence_store import file_digest, revision, safe_file
    from media_intake import Intake

VIDEO_SUFFIXES = {'.mp4', '.mkv', '.mov', '.webm'}
IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp'}
# Fractions of duration sampled for frame derivatives. This is a sampling policy,
# not a claim about where teaching content occurs in any asset.
FRAME_FRACTIONS = (0.10, 0.50, 0.90)


def git_blob_sha1(path):
    """Git blob identity of a local file, comparable with committed tree SHAs."""
    raw = Path(path).read_bytes()
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def media_class(relative):
    suffix = Path(relative).suffix.lower()
    if suffix in VIDEO_SUFFIXES:
        return 'VIDEO'
    if suffix in IMAGE_SUFFIXES:
        return 'IMAGE'
    return 'UNSUPPORTED'


class VideoIntake(Intake):
    def register_committed(self, relative, collection_id, expected_git_blob):
        """Register only if local bytes match the committed Git blob identity."""
        if not (isinstance(expected_git_blob, str) and len(expected_git_blob) == 40):
            raise ValueError('A 40-character committed Git blob SHA-1 is required')
        path = safe_file(self.source, relative)
        observed = git_blob_sha1(path)
        if observed != expected_git_blob.lower():
            raise ValueError(
                'Local bytes do not match the committed asset: expected '
                f'{expected_git_blob.lower()} observed {observed}')
        asset = self.register(relative, collection_id)
        self.journal.append('attempt', {
            'asset_id': asset['id'], 'job_key': None, 'stage': 'identity',
            'processor_version': 'git-blob-sha1-v1', 'engine': 'stdlib-sha1',
            'result': 'PASS', 'git_blob_sha1': observed,
            'expected_git_blob_sha1': expected_git_blob.lower(),
        })
        return asset

    def duration_seconds(self, probe):
        payload = probe['payload']
        if payload['result'] != 'PASS':
            raise ValueError('A successful probe is required')
        return float(payload['metadata']['format']['duration'])

    def frame(self, asset, probe, relative, at_seconds, artifact_root,
              *, executable='ffmpeg', processor_version='ffmpeg-frame-v1'):
        """Extract and hash one frame. Reuses an intact prior successful attempt."""
        if asset not in self.journal.records('asset'):
            raise ValueError('Unregistered asset')
        duration = self.duration_seconds(probe)
        if probe['payload']['asset_id'] != asset['id']:
            raise ValueError('Probe does not belong to this asset')
        if type(at_seconds) not in (int, float) or not math.isfinite(at_seconds) \
                or not 0 <= at_seconds <= duration:
            raise ValueError('Frame timestamp outside probed duration')
        if asset['payload']['format_hint'] not in VIDEO_SUFFIXES:
            raise ValueError('Frame extraction requires a video asset')
        path = safe_file(self.source, relative)
        if file_digest(path) != asset['payload']['sha256']:
            raise ValueError('Source changed; register a new revision')
        if shutil.which(executable) is None:
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': None, 'stage': 'frame',
                'processor_version': processor_version, 'engine': None,
                'result': 'BLOCKED', 'reason': f'{executable} unavailable',
                'at_seconds': at_seconds})
        version = subprocess.run([executable, '-version'], capture_output=True, text=True,
                                 timeout=20, check=True).stdout.splitlines()[0]
        key = revision({'asset': asset['payload']['sha256'], 'stage': 'frame',
                        'processor': processor_version, 'engine': version,
                        'at_seconds': round(float(at_seconds), 3)})
        artifacts = Path(artifact_root).resolve()
        if artifacts.is_relative_to(self.source) or self.source.is_relative_to(artifacts):
            raise ValueError('Frame artifacts must not be written into the raw source root')
        for record in self.journal.records('attempt'):
            payload = record['payload']
            if payload.get('job_key') == key and payload['result'] == 'PASS':
                existing = artifacts / payload['artifact_name']
                if existing.exists() and file_digest(existing) == payload['artifact_sha256']:
                    return record
        artifacts.mkdir(parents=True, exist_ok=True)
        name = f"{asset['payload']['sha256'][:12]}-{int(round(float(at_seconds) * 1000)):09d}.png"
        target = artifacts / name
        try:
            completed = subprocess.run(
                [executable, '-y', '-ss', f'{float(at_seconds):.3f}', '-i', str(path),
                 '-frames:v', '1', '-f', 'image2', str(target)],
                capture_output=True, text=True, timeout=180, check=True)
            if not target.exists() or target.stat().st_size == 0:
                raise ValueError('No frame was produced')
            if file_digest(path) != asset['payload']['sha256']:
                raise ValueError('Source changed during extraction')
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'frame',
                'processor_version': processor_version, 'engine': version, 'result': 'PASS',
                'at_seconds': float(at_seconds), 'artifact_name': name,
                'artifact_sha256': file_digest(target), 'artifact_bytes': target.stat().st_size,
                'stderr': completed.stderr[-2000:]})
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'frame',
                'processor_version': processor_version, 'engine': version, 'result': 'FAIL',
                'at_seconds': float(at_seconds), 'error': str(exc)})

    def blocked_extraction(self, asset, probe, stage, reason):
        """Record an unavailable extraction capability without inventing output."""
        if stage not in {'asr', 'ocr'}:
            raise ValueError('Unknown extraction stage')
        if not reason:
            raise ValueError('An explicit blocking reason is required')
        if probe['payload']['asset_id'] != asset['id']:
            raise ValueError('Probe does not belong to this asset')
        return self.journal.append('attempt', {
            'asset_id': asset['id'], 'job_key': None, 'stage': stage,
            'processor_version': None, 'engine': None, 'result': 'BLOCKED',
            'reason': reason, 'output': None})

    def audio_streams(self, probe):
        return [s for s in probe['payload']['metadata']['streams']
                if s.get('codec_type') == 'audio']

    def planned_frames(self, probe):
        duration = self.duration_seconds(probe)
        return [round(duration * f, 3) for f in FRAME_FRACTIONS]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True,
                        help='Local checkout directory holding the real committed media')
    parser.add_argument('--state-root', required=True)
    parser.add_argument('--artifact-root', required=True)
    parser.add_argument('--collection', required=True)
    parser.add_argument('--relative', required=True, help='One asset path inside --source-root')
    parser.add_argument('--git-blob', required=True, help='Committed Git blob SHA-1 of that asset')
    args = parser.parse_args()
    if media_class(args.relative) != 'VIDEO':
        parser.error('This runner is bounded to a single video asset')
    intake = VideoIntake(args.source_root, args.state_root)
    result = {'relative_path': args.relative, 'status': 'PARTIAL',
              'verified_knowledge_created': 0, 'spans_created': 0}
    try:
        asset = intake.register_committed(args.relative, args.collection, args.git_blob)
        probe = intake.probe(asset, args.relative)
        if probe['payload']['result'] != 'PASS':
            result['status'] = 'BLOCKED'
            result['probe'] = probe['payload']
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1
        frames = [intake.frame(asset, probe, args.relative, at, args.artifact_root)['payload']
                  for at in intake.planned_frames(probe)]
        blocked = [intake.blocked_extraction(asset, probe, 'asr',
                       'No licensed speech-recognition engine is configured in this repository')['payload'],
                   intake.blocked_extraction(asset, probe, 'ocr',
                       'No OCR engine is installed; frame derivatives are retained for later OCR')['payload']]
        result.update({
            'asset_sha256': asset['payload']['sha256'],
            'bytes': asset['payload']['bytes'],
            'duration_seconds': intake.duration_seconds(probe),
            'audio_streams': len(intake.audio_streams(probe)),
            'frames': frames,
            'blocked_extractions': blocked,
            'note': 'Frames and metadata only. No transcript, OCR text, publisher '
                    'attribution or PYQ relationship is asserted by this runner.',
        })
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result['status'] = 'BLOCKED'
        result['error'] = str(exc)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
