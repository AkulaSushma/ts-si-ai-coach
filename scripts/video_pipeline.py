"""SPEC-INT-013: resumable, fail-closed video intelligence pipeline.

Extends VideoIntake (SPEC-INT-011) and writes into the SPEC-INT-012 knowledge
graph. The pipeline turns one real video into located evidence, never into
unsupported teaching claims.

Stage chain, each stage independently recorded and resumable:

  identity -> probe -> audio_extract -> scene_sample -> frames -> ocr -> asr

Design rules enforced by code, not by convention:

1. Every stage result is keyed by (asset sha256, stage, engine version, params).
   Re-running an unchanged asset reuses the prior PASS record and verifies the
   artifact digest instead of producing a duplicate.
2. A missing capability (no ASR engine, no OCR engine, no Telugu model) yields a
   BLOCKED attempt naming the capability. BLOCKED never becomes a span, so it can
   never become a candidate, and never a verified claim.
3. Recognised text is stored verbatim in its source language. Normalisation and
   translation live in separate optional fields tagged MODEL_INTERPRETED, so the
   original evidence can always be recovered.
4. Low-confidence or ambiguous ASR output is retained with its confidence and is
   marked uncertain. It is never silently repaired.
5. Nothing here creates a concept, method, shortcut or PYQ relationship. Those
   require separate, evidence-gated calls into knowledge_graph.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path

try:
    from .evidence_store import file_digest, revision, safe_file
    from .video_intake import VideoIntake, git_blob_sha1, media_class
except ImportError:  # direct execution
    from evidence_store import file_digest, revision, safe_file
    from video_intake import VideoIntake, git_blob_sha1, media_class

# Languages the project expects in this collection. 'und' means undetermined and
# is used when no engine could establish the language; it is not a guess.
EXPECTED_LANGUAGES = ('te', 'en', 'mixed', 'und')

# Scene detection threshold. Higher means fewer, stronger cuts. Teaching videos
# in this collection are screen/handwriting recordings where a cut usually marks
# a new board state, which is exactly where on-screen text changes.
SCENE_THRESHOLD = 0.30
MAX_SAMPLED_FRAMES = 24


class CapabilityUnavailable(Exception):
    """Raised by an adapter that cannot run. Always becomes a BLOCKED attempt."""


class AsrAdapter:
    """Interface for speech recognition. Implementations must not invent text.

    transcribe() returns a list of segments:
        {'start': float, 'end': float, 'text': str, 'language': str,
         'confidence': float or None}
    text must be verbatim recognised output in the spoken language. An adapter
    that cannot handle the requested language must raise CapabilityUnavailable
    rather than transcribing it as some other language.
    """

    name = 'abstract-asr'
    version = '0'
    languages = ()

    def available(self):
        return False

    def transcribe(self, audio_path, language_hint=None):
        raise CapabilityUnavailable('No speech recognition engine is configured')


class OcrAdapter:
    """Interface for on-screen text recognition.

    recognize() returns a list of regions:
        {'xyxy': [x0, y0, x1, y1], 'text': str, 'language': str,
         'confidence': float or None}
    """

    name = 'abstract-ocr'
    version = '0'
    languages = ()

    def available(self):
        return False

    def recognize(self, image_path, language_hint=None):
        raise CapabilityUnavailable('No OCR engine is configured')


class TesseractOcrAdapter(OcrAdapter):
    """Real OCR when tesseract plus the requested language pack is installed.

    Availability is checked against the actual installed language list, so a
    Telugu request on an English-only install is BLOCKED rather than mis-read.
    """

    name = 'tesseract'

    LANG_CODES = {'te': 'tel', 'en': 'eng', 'mixed': 'tel+eng'}

    def __init__(self, executable='tesseract'):
        self.executable = executable

    def _installed(self):
        if shutil.which(self.executable) is None:
            return set()
        try:
            out = subprocess.run([self.executable, '--list-langs'], capture_output=True,
                                 text=True, timeout=30, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            return set()
        return {line.strip() for line in out.splitlines()[1:] if line.strip()}

    @property
    def version(self):
        if shutil.which(self.executable) is None:
            return '0'
        try:
            out = subprocess.run([self.executable, '--version'], capture_output=True,
                                 text=True, timeout=30, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            return '0'
        return out.splitlines()[0].strip()

    @property
    def languages(self):
        installed = self._installed()
        found = []
        for code, pack in self.LANG_CODES.items():
            if all(part in installed for part in pack.split('+')):
                found.append(code)
        return tuple(found)

    def available(self, language_hint=None):
        langs = self.languages
        if not langs:
            return False
        if language_hint in (None, 'und'):
            return True
        return language_hint in langs

    def recognize(self, image_path, language_hint=None):
        if not self.available(language_hint):
            raise CapabilityUnavailable(
                'tesseract is missing or lacks a language pack for '
                + str(language_hint))
        pack = self.LANG_CODES.get(language_hint or 'en', 'eng')
        completed = subprocess.run(
            [self.executable, str(image_path), 'stdout', '-l', pack, 'tsv'],
            capture_output=True, text=True, timeout=300, check=True)
        regions = []
        for line in completed.stdout.splitlines()[1:]:
            parts = line.split('\t')
            if len(parts) < 12 or not parts[11].strip():
                continue
            left, top, width, height = (int(parts[6]), int(parts[7]),
                                        int(parts[8]), int(parts[9]))
            try:
                confidence = float(parts[10])
            except ValueError:
                confidence = None
            regions.append({
                'xyxy': [left, top, left + width, top + height],
                'text': parts[11],
                'language': language_hint or 'und',
                'confidence': None if confidence is None or confidence < 0
                              else confidence / 100.0,
            })
        return regions


class AdapterRegistry:
    """Fail-closed adapter lookup. Absence is reported, never substituted."""

    def __init__(self):
        self._asr = []
        self._ocr = []

    def register_asr(self, adapter):
        self._asr.append(adapter)
        return adapter

    def register_ocr(self, adapter):
        self._ocr.append(adapter)
        return adapter

    @staticmethod
    def _usable(adapter, language_hint):
        try:
            ok = adapter.available(language_hint)
        except TypeError:
            ok = adapter.available()
        return bool(ok)

    def asr(self, language_hint=None):
        for adapter in self._asr:
            if self._usable(adapter, language_hint):
                return adapter
        return None

    def ocr(self, language_hint=None):
        for adapter in self._ocr:
            if self._usable(adapter, language_hint):
                return adapter
        return None


def default_registry():
    registry = AdapterRegistry()
    registry.register_ocr(TesseractOcrAdapter())
    return registry


class VideoPipeline(VideoIntake):
    """Resumable, fail-closed extraction of located evidence from one video."""

    def __init__(self, source_root, state_root, artifact_root, registry=None):
        super().__init__(source_root, state_root)
        artifacts = Path(artifact_root).resolve()
        if artifacts.is_relative_to(self.source) or self.source.is_relative_to(artifacts):
            raise ValueError('Artifacts must not be written into the raw source root')
        self.artifacts = artifacts
        self.registry = registry if registry is not None else default_registry()

    # ---------------------------------------------------------------- helpers
    def _tool_version(self, executable):
        if shutil.which(executable) is None:
            return None
        try:
            out = subprocess.run([executable, '-version'], capture_output=True,
                                 text=True, timeout=20, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        return out.splitlines()[0].strip()

    def _reuse(self, key):
        """Return a prior PASS attempt for this job key whose artifact still matches."""
        for record in self.journal.records('attempt'):
            payload = record['payload']
            if payload.get('job_key') != key or payload.get('result') != 'PASS':
                continue
            name = payload.get('artifact_name')
            if name is None:
                return record
            existing = self.artifacts / name
            if existing.exists() and file_digest(existing) == payload.get('artifact_sha256'):
                return record
        return None

    def _blocked(self, asset, stage, reason, **extra):
        payload = {'asset_id': asset['id'], 'job_key': None, 'stage': stage,
                   'processor_version': None, 'engine': None, 'result': 'BLOCKED',
                   'reason': reason, 'output': None}
        payload.update(extra)
        return self.journal.append('attempt', payload)

    def _verify_unchanged(self, asset, relative):
        path = safe_file(self.source, relative)
        if file_digest(path) != asset['payload']['sha256']:
            raise ValueError('Source changed; register a new revision')
        return path

    # ----------------------------------------------------------------- stages
    def extract_audio(self, asset, probe, relative, *, executable='ffmpeg',
                      processor_version='ffmpeg-audio-v1'):
        """Extract a normalised 16 kHz mono WAV suitable for any ASR engine."""
        if probe['payload']['asset_id'] != asset['id']:
            raise ValueError('Probe does not belong to this asset')
        if not self.audio_streams(probe):
            return self._blocked(asset, 'audio_extract',
                                 'The probed asset contains no audio stream')
        version = self._tool_version(executable)
        if version is None:
            return self._blocked(asset, 'audio_extract',
                                 str(executable) + ' is not installed')
        path = self._verify_unchanged(asset, relative)
        key = revision({'asset': asset['payload']['sha256'], 'stage': 'audio_extract',
                        'processor': processor_version, 'engine': version,
                        'arguments': 'pcm_s16le 16000 mono'})
        reused = self._reuse(key)
        if reused is not None:
            return reused
        self.artifacts.mkdir(parents=True, exist_ok=True)
        name = asset['payload']['sha256'][:12] + '-audio16k.wav'
        target = self.artifacts / name
        try:
            completed = subprocess.run(
                [executable, '-y', '-i', str(path), '-vn', '-ac', '1', '-ar', '16000',
                 '-acodec', 'pcm_s16le', str(target)],
                capture_output=True, text=True, timeout=1800, check=True)
            if not target.exists() or target.stat().st_size == 0:
                raise ValueError('No audio was produced')
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'audio_extract',
                'processor_version': processor_version, 'engine': version,
                'result': 'PASS', 'artifact_name': name,
                'artifact_sha256': file_digest(target),
                'artifact_bytes': target.stat().st_size,
                'stderr': completed.stderr[-2000:]})
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'audio_extract',
                'processor_version': processor_version, 'engine': version,
                'result': 'FAIL', 'error': str(exc)})

    def scene_timestamps(self, asset, probe, relative, *, executable='ffmpeg',
                         processor_version='ffmpeg-scene-v1',
                         threshold=SCENE_THRESHOLD, limit=MAX_SAMPLED_FRAMES):
        """Detect scene changes. These are where the board state usually changes.

        Falls back to the SPEC-INT-011 fixed fractions when detection finds
        nothing, and records which policy produced the timestamps so a later
        reader can tell a detected cut from a blind sample.
        """
        version = self._tool_version(executable)
        if version is None:
            return self._blocked(asset, 'scene_sample',
                                 str(executable) + ' is not installed')
        path = self._verify_unchanged(asset, relative)
        duration = self.duration_seconds(probe)
        key = revision({'asset': asset['payload']['sha256'], 'stage': 'scene_sample',
                        'processor': processor_version, 'engine': version,
                        'threshold': threshold, 'limit': limit})
        reused = self._reuse(key)
        if reused is not None:
            return reused
        try:
            completed = subprocess.run(
                [executable, '-i', str(path), '-filter:v',
                 'select=gt(scene\\,' + str(threshold) + '),showinfo',
                 '-f', 'null', '-'],
                capture_output=True, text=True, timeout=1800, check=True)
            times = []
            for match in re.finditer(r'pts_time:([0-9.]+)', completed.stderr):
                value = round(float(match.group(1)), 3)
                if 0.0 <= value <= duration and value not in times:
                    times.append(value)
            policy = 'scene_change'
            if not times:
                times = self.planned_frames(probe)
                policy = 'fixed_fraction_fallback'
            if len(times) > limit:
                step = len(times) / float(limit)
                times = [times[int(i * step)] for i in range(limit)]
                policy = policy + '_downsampled'
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'scene_sample',
                'processor_version': processor_version, 'engine': version,
                'result': 'PASS', 'policy': policy, 'threshold': threshold,
                'timestamps': times, 'duration_seconds': duration})
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'scene_sample',
                'processor_version': processor_version, 'engine': version,
                'result': 'FAIL', 'error': str(exc)})

    def recognize_frame(self, asset, relative, frame_attempt, *, language_hint=None,
                        processor_version='ocr-v1'):
        """Run OCR over one extracted frame, or record a BLOCKED capability gap."""
        payload = frame_attempt['payload']
        if payload.get('stage') != 'frame' or payload.get('result') != 'PASS':
            raise ValueError('OCR requires a successful frame attempt')
        adapter = self.registry.ocr(language_hint)
        if adapter is None:
            return self._blocked(
                asset, 'ocr',
                'No OCR engine available for language ' + str(language_hint or 'und'),
                at_seconds=payload['at_seconds'])
        image = self.artifacts / payload['artifact_name']
        if not image.exists() or file_digest(image) != payload['artifact_sha256']:
            raise ValueError('Frame artifact is missing or altered')
        key = revision({'asset': asset['payload']['sha256'], 'stage': 'ocr',
                        'processor': processor_version,
                        'engine': adapter.name + ':' + str(adapter.version),
                        'frame': payload['artifact_sha256'],
                        'language_hint': language_hint})
        reused = self._reuse(key)
        if reused is not None:
            return reused
        try:
            regions = adapter.recognize(image, language_hint)
        except CapabilityUnavailable as exc:
            return self._blocked(asset, 'ocr', str(exc),
                                 at_seconds=payload['at_seconds'])
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'ocr',
                'processor_version': processor_version,
                'engine': adapter.name + ':' + str(adapter.version),
                'result': 'FAIL', 'at_seconds': payload['at_seconds'],
                'error': str(exc)})
        return self.journal.append('attempt', {
            'asset_id': asset['id'], 'job_key': key, 'stage': 'ocr',
            'processor_version': processor_version,
            'engine': adapter.name + ':' + str(adapter.version),
            'result': 'PASS', 'at_seconds': payload['at_seconds'],
            'frame_sha256': payload['artifact_sha256'],
            'language_hint': language_hint,
            'regions': regions, 'region_count': len(regions)})

    def transcribe(self, asset, audio_attempt, *, language_hint=None,
                   processor_version='asr-v1'):
        """Run ASR over extracted audio, or record a BLOCKED capability gap."""
        payload = audio_attempt['payload']
        if payload.get('stage') != 'audio_extract' or payload.get('result') != 'PASS':
            return self._blocked(
                asset, 'asr',
                'Audio extraction did not succeed, so no speech is available')
        adapter = self.registry.asr(language_hint)
        if adapter is None:
            return self._blocked(
                asset, 'asr',
                'No speech recognition engine available for language '
                + str(language_hint or 'und'))
        audio = self.artifacts / payload['artifact_name']
        if not audio.exists() or file_digest(audio) != payload['artifact_sha256']:
            raise ValueError('Audio artifact is missing or altered')
        key = revision({'asset': asset['payload']['sha256'], 'stage': 'asr',
                        'processor': processor_version,
                        'engine': adapter.name + ':' + str(adapter.version),
                        'audio': payload['artifact_sha256'],
                        'language_hint': language_hint})
        reused = self._reuse(key)
        if reused is not None:
            return reused
        try:
            segments = adapter.transcribe(audio, language_hint)
        except CapabilityUnavailable as exc:
            return self._blocked(asset, 'asr', str(exc))
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            return self.journal.append('attempt', {
                'asset_id': asset['id'], 'job_key': key, 'stage': 'asr',
                'processor_version': processor_version,
                'engine': adapter.name + ':' + str(adapter.version),
                'result': 'FAIL', 'error': str(exc)})
        for segment in segments:
            if segment.get('language') not in EXPECTED_LANGUAGES:
                raise ValueError('ASR returned an unexpected language label')
            if not isinstance(segment.get('text'), str) or not segment['text'].strip():
                raise ValueError('ASR returned an empty segment')
            if not math.isfinite(float(segment['start'])) or \
                    float(segment['end']) < float(segment['start']):
                raise ValueError('ASR returned an invalid interval')
        return self.journal.append('attempt', {
            'asset_id': asset['id'], 'job_key': key, 'stage': 'asr',
            'processor_version': processor_version,
            'engine': adapter.name + ':' + str(adapter.version),
            'result': 'PASS', 'language_hint': language_hint,
            'segments': segments, 'segment_count': len(segments)})

    # ------------------------------------------------------------- span build
    def frame_span(self, asset, probe, location, original_text, language, extraction):
        """Span located at a pixel region of a timestamped video frame.

        media_intake.span deliberately supports only whole-image regions and
        whole-video intervals. On-screen teaching text needs both a timestamp and
        a region, so this adds that one location kind without altering the
        existing validated behaviour of media_intake.
        """
        payload_probe = probe['payload']
        if probe not in self.journal.records('attempt') or \
                asset not in self.journal.records('asset'):
            raise ValueError('Unregistered evidence inputs')
        if payload_probe['result'] != 'PASS' or payload_probe['asset_id'] != asset['id']:
            raise ValueError('A matching successful probe is required')
        if asset['payload']['format_hint'] not in {'.mp4', '.mkv', '.mov', '.webm'}:
            raise ValueError('A frame region requires a video asset')
        if location.get('kind') != 'video_frame_region':
            raise ValueError('Unsupported evidence location')
        if not isinstance(original_text, str) or not original_text.strip() or \
                language not in {'en', 'te', 'mixed', 'und'}:
            raise ValueError('Original text and language required')
        if not all(isinstance(extraction.get(k), str) and extraction[k].strip()
                   for k in ('processor', 'version', 'method')):
            raise ValueError('Extraction provenance required')
        if extraction['method'] not in {'HUMAN_TRANSCRIPTION', 'MODEL_VISUAL', 'OCR', 'ASR'}:
            raise ValueError('Unknown extraction method')
        streams = payload_probe['metadata']['streams']
        video = next(s for s in streams if s.get('codec_type') == 'video')
        duration = float(payload_probe['metadata']['format']['duration'])
        at = location.get('at_seconds')
        if type(at) not in (int, float) or not math.isfinite(at) or not 0 <= at <= duration:
            raise ValueError('Frame timestamp outside probed duration')
        box = location.get('xyxy')
        if not isinstance(box, list) or len(box) != 4 or \
                any(type(v) not in (int, float) or not math.isfinite(v) for v in box):
            raise ValueError('Invalid region')
        x1, y1, x2, y2 = box
        if not (0 <= x1 < x2 <= video['width'] and 0 <= y1 < y2 <= video['height']):
            raise ValueError('Region outside frame')
        payload = {'asset_id': asset['id'], 'asset_sha256': asset['payload']['sha256'],
                   'probe_id': probe['id'], 'location': location,
                   'original_text': original_text, 'language': language,
                   'extraction': extraction, 'fidelity_status': 'UNVERIFIED'}
        for record in self.journal.records('span'):
            if record['payload'] == payload:
                return record
        return self.journal.append('span', payload)

    def spans_from_ocr(self, asset, probe, ocr_attempt, *, min_confidence=0.55):
        """Turn recognised on-screen text into located, source-derived spans.

        Each span keeps the exact recognised characters, the frame timestamp and
        the pixel region. Low-confidence text is still preserved but is marked so
        no downstream reader can treat it as clean evidence.
        """
        payload = ocr_attempt['payload']
        if payload.get('stage') != 'ocr' or payload.get('result') != 'PASS':
            return []
        created = []
        for region in payload['regions']:
            confidence = region.get('confidence')
            uncertain = confidence is None or confidence < min_confidence
            location = {'kind': 'video_frame_region',
                        'at_seconds': payload['at_seconds'],
                        'xyxy': region['xyxy'],
                        'frame_sha256': payload['frame_sha256']}
            extraction = {'processor': payload['engine'], 'version': payload['processor_version'],
                          'method': 'OCR', 'confidence': confidence,
                          'low_confidence': uncertain}
            created.append(self.frame_span(asset, probe, location, region['text'],
                                           region.get('language') or 'und', extraction))
        return created

    def spans_from_asr(self, asset, probe, asr_attempt, *, min_confidence=0.55):
        """Turn recognised speech into located, source-derived spans.

        The transcript text is stored verbatim in the spoken language. No
        translation is produced here; a translation would be a separate
        MODEL_INTERPRETED candidate carrying its own uncertainty.
        """
        payload = asr_attempt['payload']
        if payload.get('stage') != 'asr' or payload.get('result') != 'PASS':
            return []
        created = []
        for segment in payload['segments']:
            confidence = segment.get('confidence')
            uncertain = confidence is None or confidence < min_confidence
            location = {'kind': 'video_interval',
                        'start_seconds': float(segment['start']),
                        'end_seconds': float(segment['end'])}
            extraction = {'processor': payload['engine'], 'version': payload['processor_version'],
                          'method': 'ASR', 'confidence': confidence,
                          'low_confidence': uncertain}
            created.append(self.span(asset, probe, location, segment['text'],
                                     segment['language'], extraction))
        return created

    # ------------------------------------------------------------ orchestration
    def run(self, relative, collection, git_blob, *, language_hint=None,
            max_frames=MAX_SAMPLED_FRAMES):
        """Execute the whole stage chain for one video and return a stage report.

        The return value is a plain dict of stage outcomes. It never contains a
        teaching claim, a concept, a method or a PYQ relationship: those are the
        responsibility of a separate, evidence-gated intelligence step.
        """
        if media_class(relative) != 'VIDEO':
            raise ValueError('This pipeline is bounded to video assets')
        report = {'relative_path': str(Path(relative)), 'collection': collection,
                  'stages': {}, 'spans': [], 'capability_gaps': []}
        asset = self.register_committed(relative, collection, git_blob)
        report['asset'] = {'sha256': asset['payload']['sha256'],
                           'bytes': asset['payload']['bytes'],
                           'git_blob_sha1': git_blob.lower(),
                           'format_hint': asset['payload']['format_hint']}
        report['stages']['identity'] = 'PASS'

        probe = self.probe(asset, relative)
        report['stages']['probe'] = probe['payload']['result']
        if probe['payload']['result'] != 'PASS':
            report['status'] = 'BLOCKED'
            report['probe_error'] = probe['payload'].get('error')
            return report
        metadata = probe['payload']['metadata']
        video_streams = [s for s in metadata['streams'] if s.get('codec_type') == 'video']
        report['metadata'] = {
            'duration_seconds': float(metadata['format']['duration']),
            'format_name': metadata['format'].get('format_name'),
            'video_streams': [{'codec': s.get('codec_name'), 'width': s.get('width'),
                               'height': s.get('height'),
                               'avg_frame_rate': s.get('avg_frame_rate')}
                              for s in video_streams],
            'audio_streams': [{'codec': s.get('codec_name'),
                               'sample_rate': s.get('sample_rate'),
                               'channels': s.get('channels'),
                               'language_tag': (s.get('tags') or {}).get('language')}
                              for s in self.audio_streams(probe)],
        }

        audio = self.extract_audio(asset, probe, relative)
        report['stages']['audio_extract'] = audio['payload']['result']
        if audio['payload']['result'] != 'PASS':
            report['capability_gaps'].append(
                {'stage': 'audio_extract',
                 'reason': audio['payload'].get('reason') or audio['payload'].get('error')})

        scenes = self.scene_timestamps(asset, probe, relative, limit=max_frames)
        report['stages']['scene_sample'] = scenes['payload']['result']
        timestamps = []
        if scenes['payload']['result'] == 'PASS':
            timestamps = scenes['payload']['timestamps']
            report['sampling_policy'] = scenes['payload']['policy']
        else:
            report['capability_gaps'].append(
                {'stage': 'scene_sample',
                 'reason': scenes['payload'].get('reason') or scenes['payload'].get('error')})
        report['sampled_timestamps'] = timestamps

        frames = []
        for at in timestamps:
            frames.append(self.frame(asset, probe, relative, at, self.artifacts))
        passed = [f for f in frames if f['payload']['result'] == 'PASS']
        report['stages']['frames'] = 'PASS' if passed else 'FAILED'
        report['frames'] = [{'at_seconds': f['payload']['at_seconds'],
                             'artifact_sha256': f['payload'].get('artifact_sha256'),
                             'result': f['payload']['result']} for f in frames]

        ocr_results = []
        for frame_attempt in passed:
            ocr_results.append(self.recognize_frame(asset, relative, frame_attempt,
                                                    language_hint=language_hint))
        ocr_pass = [r for r in ocr_results if r['payload']['result'] == 'PASS']
        if not ocr_results:
            report['stages']['ocr'] = 'INCOMPLETE'
        elif ocr_pass:
            report['stages']['ocr'] = 'PASS'
        else:
            report['stages']['ocr'] = ocr_results[0]['payload']['result']
            report['capability_gaps'].append(
                {'stage': 'ocr', 'reason': ocr_results[0]['payload'].get('reason')
                 or ocr_results[0]['payload'].get('error')})

        asr = self.transcribe(asset, audio, language_hint=language_hint)
        report['stages']['asr'] = asr['payload']['result']
        if asr['payload']['result'] != 'PASS':
            report['capability_gaps'].append(
                {'stage': 'asr', 'reason': asr['payload'].get('reason')
                 or asr['payload'].get('error')})

        spans = []
        for record in ocr_pass:
            spans.extend(self.spans_from_ocr(asset, probe, record))
        spans.extend(self.spans_from_asr(asset, probe, asr))
        report['spans'] = [{'span_id': s['id'], 'language': s['payload']['language'],
                            'location': s['payload']['location'],
                            'method': s['payload']['extraction']['method'],
                            'low_confidence': s['payload']['extraction'].get('low_confidence'),
                            'original_text': s['payload']['original_text']}
                           for s in spans]
        report['span_count'] = len(spans)
        report['status'] = 'PARTIAL' if spans else 'BLOCKED'
        report['note'] = ('Located source evidence only. No concept, method, shortcut, '
                          'translation, publisher attribution or PYQ relationship is '
                          'asserted by this pipeline.')
        return report


def stage_summary(report):
    """Seven-label view of one pipeline run, for reports and tests."""
    stages = report.get('stages', {})
    mapping = {'PASS': 'SUPPORTED', 'FAIL': 'FAILED', 'FAILED': 'FAILED',
               'BLOCKED': 'BLOCKED', 'INCOMPLETE': 'INCOMPLETE'}
    return {name: mapping.get(value, 'UNVERIFIED') for name, value in stages.items()}
