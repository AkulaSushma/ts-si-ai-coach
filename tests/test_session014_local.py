"""SPEC-INT-014 regression tests: Whisper ASR adapter + local orchestrator.

All speech used here comes from an injected fake model or a locally generated
ffmpeg TEST FIXTURE. Nothing in this file describes the real media collection.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from video_pipeline import (AdapterRegistry, CapabilityUnavailable,  # noqa: E402
                            VideoPipeline)
from video_intake import git_blob_sha1  # noqa: E402
import asr_whisper  # noqa: E402
from asr_whisper import WhisperAsrAdapter, capability_snapshot, local_registry  # noqa: E402
import run_session014_local as orchestrator  # noqa: E402

HAS_FFMPEG = shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None

TELUGU = '\u0c15\u0c4d\u0c30\u0c3f.\u0c2a\u0c42. 322 \u0c1a\u0c02\u0c26\u0c4d\u0c30\u0c17\u0c41\u0c2a\u0c4d\u0c24 \u0c2e\u0c4c\u0c30\u0c4d\u0c2f'


class FakeModel:
    """Mimics the reference whisper API shape. TEST DOUBLE ONLY."""

    def __init__(self, segments, language='te'):
        self.segments = segments
        self.language = language
        self.calls = []

    def transcribe(self, audio_path, language=None, task=None):
        self.calls.append({'audio': audio_path, 'language': language, 'task': task})
        return {'language': self.language, 'segments': self.segments}


def adapter_with(segments, language='te'):
    model = FakeModel(segments, language)
    adapter = WhisperAsrAdapter(model_size='fake', loader=lambda size: model)
    return adapter, model


class WhisperAdapterTests(unittest.TestCase):
    def test_no_backend_is_unavailable_and_refuses(self):
        adapter = WhisperAsrAdapter(backend=None)
        adapter._loader = None
        self.assertFalse(adapter.available('te'))
        self.assertFalse(adapter.available('mixed'))
        self.assertEqual(adapter.version, 'unavailable:' + adapter.model_size)
        with self.assertRaises(CapabilityUnavailable):
            adapter.transcribe('/tmp/x.wav', 'te')

    def test_injected_backend_is_available(self):
        adapter, _ = adapter_with([])
        self.assertEqual(adapter.backend, 'injected')
        self.assertTrue(adapter.available('te'))
        self.assertTrue(adapter.available('mixed'))

    def test_unsupported_language_hint_refuses(self):
        adapter, _ = adapter_with([])
        with self.assertRaises(CapabilityUnavailable):
            adapter.transcribe('/tmp/x.wav', 'hi')

    def test_text_is_preserved_verbatim(self):
        adapter, _ = adapter_with([{'start': 0.0, 'end': 2.0, 'text': ' ' + TELUGU + ' ',
                                    'avg_logprob': -0.1, 'no_speech_prob': 0.01}])
        segments = adapter.transcribe('/tmp/x.wav', 'te')
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]['text'], TELUGU)
        self.assertEqual(segments[0]['language'], 'te')
        self.assertGreater(segments[0]['confidence'], 0.5)

    def test_no_translation_is_produced(self):
        adapter, _ = adapter_with([{'start': 0.0, 'end': 1.0, 'text': TELUGU,
                                    'avg_logprob': -0.2}])
        segments = adapter.transcribe('/tmp/x.wav', 'te')
        self.assertNotIn('translation', segments[0])
        self.assertNotIn('text_en', segments[0])

    def test_detected_language_outside_vocabulary_becomes_und(self):
        adapter, _ = adapter_with([{'start': 0.0, 'end': 1.0, 'text': 'kuch bhi',
                                    'avg_logprob': -0.5}], language='hi')
        segments = adapter.transcribe('/tmp/x.wav', 'mixed')
        self.assertEqual(segments[0]['language'], 'und')
        self.assertEqual(segments[0]['detected_language'], 'hi')

    def test_mixed_hint_lets_engine_autodetect(self):
        adapter, model = adapter_with([{'start': 0.0, 'end': 1.0, 'text': 'Maurya',
                                        'avg_logprob': -0.3}], language='en')
        segments = adapter.transcribe('/tmp/x.wav', 'mixed')
        self.assertIsNone(model.calls[0]['language'])
        self.assertEqual(segments[0]['language'], 'en')

    def test_explicit_language_is_passed_to_engine(self):
        adapter, model = adapter_with([{'start': 0.0, 'end': 1.0, 'text': TELUGU,
                                        'avg_logprob': -0.3}])
        adapter.transcribe('/tmp/x.wav', 'te')
        self.assertEqual(model.calls[0]['language'], 'te')
        self.assertEqual(model.calls[0]['task'], 'transcribe')

    def test_empty_segments_are_not_evidence(self):
        adapter, _ = adapter_with([{'start': 0.0, 'end': 1.0, 'text': '   ',
                                    'avg_logprob': -0.1}])
        self.assertEqual(adapter.transcribe('/tmp/x.wav', 'te'), [])

    def test_low_confidence_is_reported_not_dropped(self):
        adapter, _ = adapter_with([{'start': 0.0, 'end': 1.0, 'text': 'unclear',
                                    'avg_logprob': -3.0, 'no_speech_prob': 0.8}])
        segments = adapter.transcribe('/tmp/x.wav', 'te')
        self.assertEqual(len(segments), 1)
        self.assertLess(segments[0]['confidence'], 0.2)

    def test_confidence_bounds(self):
        self.assertEqual(asr_whisper._confidence(None), 0.0)
        self.assertEqual(asr_whisper._confidence('bad'), 0.0)
        self.assertLessEqual(asr_whisper._confidence(5.0), 1.0)

    def test_local_registry_reports_missing_capabilities(self):
        registry = local_registry(asr=WhisperAsrAdapter(backend=None))
        self.assertIsNone(registry.asr('te'))
        snapshot = capability_snapshot(registry)
        self.assertIn('te', snapshot)
        self.assertIsNone(snapshot['te']['asr'])


@unittest.skipUnless(HAS_FFMPEG, 'ffmpeg and ffprobe are required')
class PipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.source = base / 'source'
        self.source.mkdir()
        self.video = self.source / 'fixture.mp4'
        subprocess.run(
            ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:d=1',
             '-f', 'lavfi', '-i', 'color=c=white:s=320x240:d=1',
             '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
             '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[v]',
             '-map', '[v]', '-map', '2:a', '-pix_fmt', 'yuv420p',
             '-c:a', 'aac', '-shortest', str(self.video)],
            capture_output=True, text=True, timeout=300, check=True)
        self.blob = git_blob_sha1(self.video)
        self.base = base

    def tearDown(self):
        self.tmp.cleanup()

    def pipeline(self, adapter):
        registry = AdapterRegistry()
        registry.register_asr(adapter)
        return VideoPipeline(self.source, self.base / 'state', self.base / 'artifacts',
                             registry=registry)

    def test_whisper_adapter_produces_located_verbatim_spans(self):
        adapter, _ = adapter_with([{'start': 0.0, 'end': 1.5, 'text': TELUGU,
                                    'avg_logprob': -0.1, 'no_speech_prob': 0.01}])
        report = self.pipeline(adapter).run('fixture.mp4', 'fixture', self.blob,
                                            language_hint='mixed', max_frames=4)
        self.assertEqual(report['stages']['asr'], 'PASS')
        spans = [s for s in report['spans'] if s['method'] == 'ASR']
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]['original_text'], TELUGU)
        self.assertEqual(spans[0]['location']['kind'], 'video_interval')
        self.assertEqual(spans[0]['location']['start_seconds'], 0.0)

    def test_missing_backend_keeps_asr_blocked(self):
        report = self.pipeline(WhisperAsrAdapter(backend=None)).run(
            'fixture.mp4', 'fixture', self.blob, language_hint='te', max_frames=4)
        self.assertEqual(report['stages']['asr'], 'BLOCKED')
        self.assertEqual(len([s for s in report['spans'] if s['method'] == 'ASR']), 0)


class OrchestratorTests(unittest.TestCase):
    def test_counts_are_zero_when_no_report(self):
        counts = orchestrator.observation_counts(None)
        self.assertFalse(counts['decoded'])
        self.assertEqual(counts['status'], 'BLOCKED')
        self.assertEqual(counts['source_observations'], 0)
        self.assertEqual(counts['verified_new_knowledge'], 0)

    def test_counts_are_read_from_observed_report(self):
        report = {'stages': {'probe': 'PASS', 'asr': 'PASS', 'ocr': 'BLOCKED'},
                  'spans': [{'method': 'ASR', 'low_confidence': False},
                            {'method': 'ASR', 'low_confidence': True}],
                  'sampled_timestamps': [0.1, 0.5], 'frames': [{}, {}, {}],
                  'status': 'PARTIAL'}
        counts = orchestrator.observation_counts(report)
        self.assertTrue(counts['decoded'])
        self.assertTrue(counts['asr'])
        self.assertFalse(counts['ocr'])
        self.assertEqual(counts['real_timestamps'], 2)
        self.assertEqual(counts['frame_evidence'], 3)
        self.assertEqual(counts['asr_spans'], 2)
        self.assertEqual(counts['low_confidence_spans'], 1)

    def test_interpretation_counts_are_never_invented(self):
        report = {'stages': {'probe': 'PASS', 'asr': 'PASS', 'ocr': 'PASS'},
                  'spans': [{'method': 'ASR'}], 'status': 'PARTIAL'}
        counts = orchestrator.observation_counts(report)
        self.assertEqual(counts['candidate_concepts'], 0)
        self.assertEqual(counts['candidate_methods'], 0)
        self.assertEqual(counts['candidate_pyq_links'], 0)
        self.assertEqual(counts['verified_new_knowledge'], 0)

    def test_resumability_detects_drift(self):
        first = {'asset': {'sha256': 'a'}, 'stages': {'probe': 'PASS'}, 'span_count': 2,
                 'frames': [{}]}
        same = {'asset': {'sha256': 'a'}, 'stages': {'probe': 'PASS'}, 'span_count': 2,
                'frames': [{}]}
        drifted = {'asset': {'sha256': 'b'}, 'stages': {'probe': 'PASS'}, 'span_count': 3,
                   'frames': [{}]}
        self.assertEqual(orchestrator.resumability(first, same)['status'], 'PASS')
        self.assertEqual(orchestrator.resumability(first, drifted)['status'], 'FAILED')
        self.assertEqual(orchestrator.resumability(first, None)['status'], 'BLOCKED')

    def test_missing_asset_is_blocked_not_assumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            identity = orchestrator.asset_identity(tmp)
            self.assertFalse(identity['exists'])
            self.assertEqual(identity['status'], 'BLOCKED')

    def test_identity_mismatch_is_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            relative = 'media/asset.mp4'
            target = Path(tmp) / relative
            target.parent.mkdir(parents=True)
            target.write_bytes(b'not the real video')
            identity = orchestrator.asset_identity(tmp, relative=relative)
            self.assertTrue(identity['exists'])
            self.assertFalse(identity['identity_matches'])
            self.assertFalse(identity['size_matches'])
            self.assertEqual(identity['status'], 'FAILED')
            self.assertEqual(identity['git_blob_sha1'], git_blob_sha1(target))

    def test_identity_match_is_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            relative = 'media/asset.mp4'
            target = Path(tmp) / relative
            target.parent.mkdir(parents=True)
            payload = b'bytes'
            target.write_bytes(payload)
            identity = orchestrator.asset_identity(
                tmp, relative=relative, expected_blob=git_blob_sha1(target),
                expected_size=len(payload))
            self.assertEqual(identity['status'], 'PASS')
            self.assertTrue(identity['size_matches'])

    def test_session013_presence_is_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            present = orchestrator.session013_presence(tmp)
            self.assertEqual(set(present), set(orchestrator.SESSION_013_FILES))
            self.assertFalse(any(v['exists'] for v in present.values()))

    def test_run_cmd_records_missing_executable(self):
        result = orchestrator.run_cmd(['definitely-not-a-real-binary-xyz'])
        self.assertFalse(result['available'])
        self.assertIsNone(result['returncode'])

    def test_summarise_run_verdicts(self):
        ok = orchestrator.summarise_run({'available': True, 'returncode': 0,
                                         'stdout': 'fine', 'stderr': ''}, 'x')
        bad = orchestrator.summarise_run({'available': True, 'returncode': 1,
                                          'stdout': '', 'stderr': 'boom'}, 'x')
        missing = orchestrator.summarise_run({'available': False, 'returncode': None,
                                              'stdout': '', 'stderr': ''}, 'x')
        self.assertEqual(ok['verdict'], 'PASSED')
        self.assertEqual(bad['verdict'], 'FAILED')
        self.assertEqual(missing['verdict'], 'UNAVAILABLE')

    def sample_payload(self):
        return {
            'git': {'head': {'stdout': 'abc123\n'}, 'branch': {'stdout': 'main\n'},
                    'status_short': {'stdout': ''}},
            'session013_files': {'scripts/video_pipeline.py': {'exists': True,
                                                               'size': 1}},
            'asset': {'relative_path': 'x.mp4', 'exists': True, 'size_bytes': 1,
                      'sha256': 'deadbeef', 'git_blob_sha1': 'abc',
                      'identity_matches': True, 'status': 'PASS'},
            'capabilities': {
                'ffmpeg': {'usable': True, 'path': '/usr/bin/ffmpeg', 'version_line': 'v'},
                'ffprobe': {'usable': True, 'path': '/usr/bin/ffprobe', 'version_line': 'v'},
                'tesseract': {'usable': False, 'path': None, 'version_line': None},
                'tesseract_languages': [], 'ocr_telugu': False, 'ocr_english': False,
                'asr': {'backend': None, 'version': 'unavailable:small'},
                'asr_telugu_capable': False,
                'capability_gaps': ['no local Whisper-class ASR backend'],
                'status': 'BLOCKED'},
            'real_video_results': orchestrator.observation_counts(None),
            'resumability': {'status': 'BLOCKED'},
            'tamper_check': {'status': 'BLOCKED', 'original_unchanged': True},
            'tests': {'verdict': 'PASSED'}, 'validator': {'verdict': 'UNAVAILABLE'},
        }

    def test_blockers_are_collected_from_observations(self):
        payload = self.sample_payload()
        blockers = orchestrator.collect_blockers(payload)
        self.assertIn('no local Whisper-class ASR backend', blockers)
        self.assertTrue(any('decoding did not succeed' in b for b in blockers))
        self.assertTrue(any('Speech recognition did not succeed' in b for b in blockers))
        self.assertTrue(any('retention' in b for b in blockers))

    def test_markdown_reports_no_when_nothing_observed(self):
        payload = self.sample_payload()
        payload['blockers'] = orchestrator.collect_blockers(payload)
        payload['session_status'] = 'BLOCKED'
        text = orchestrator.build_markdown(payload)
        self.assertIn('decoded: NO', text)
        self.assertIn('ASR: NO', text)
        self.assertIn('OCR: NO', text)
        self.assertIn('VERIFIED new knowledge: 0', text)
        self.assertIn('Session status: BLOCKED', text)
        self.assertNotIn('COMPLETE', text.split('Session status')[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
