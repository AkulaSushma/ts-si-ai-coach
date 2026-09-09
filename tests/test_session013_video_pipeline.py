"""SPEC-INT-013 regression tests for the video intelligence pipeline.

The video used here is generated locally by ffmpeg and is a TEST FIXTURE. No
assertion in this file describes the real committed media collection.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from video_pipeline import (  # noqa: E402
    AdapterRegistry, AsrAdapter, CapabilityUnavailable, OcrAdapter,
    VideoPipeline, stage_summary)
from video_intake import git_blob_sha1  # noqa: E402

HAS_FFMPEG = shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None


class StubAsr(AsrAdapter):
    name = 'stub-asr'
    version = '1'
    languages = ('te', 'en', 'mixed')

    def __init__(self, segments=None, language='te'):
        self.language = language
        self.calls = 0
        self.segments = segments

    def available(self, language_hint=None):
        return language_hint in (None, 'und') or language_hint in self.languages

    def transcribe(self, audio_path, language_hint=None):
        self.calls += 1
        if self.segments is not None:
            return self.segments
        return [{'start': 0.0, 'end': 1.0,
                 'text': 'ఇది పరీక్ష', 'language': self.language,
                 'confidence': 0.91},
                {'start': 1.0, 'end': 1.6, 'text': 'unclear word',
                 'language': self.language, 'confidence': 0.21}]


class TeluguOnlyAsr(AsrAdapter):
    name = 'te-only-asr'
    version = '1'
    languages = ('te',)

    def available(self, language_hint=None):
        return language_hint == 'te'

    def transcribe(self, audio_path, language_hint=None):
        raise CapabilityUnavailable('Telugu-only engine cannot handle ' + str(language_hint))


class StubOcr(OcrAdapter):
    name = 'stub-ocr'
    version = '1'
    languages = ('en',)

    def __init__(self):
        self.calls = 0

    def available(self, language_hint=None):
        return True

    def recognize(self, image_path, language_hint=None):
        self.calls += 1
        return [{'xyxy': [10, 10, 120, 40], 'text': 'MAURYA',
                 'language': 'en', 'confidence': 0.88},
                {'xyxy': [10, 50, 120, 80], 'text': 'CHANDRAGUPTA',
                 'language': 'en', 'confidence': 0.30}]


def make_fixture(directory):
    """Generate a tiny two-scene video with a tone. TEST FIXTURE ONLY."""
    target = Path(directory) / 'fixture.mp4'
    subprocess.run(
        ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:d=1',
         '-f', 'lavfi', '-i', 'color=c=white:s=320x240:d=1',
         '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
         '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[v]',
         '-map', '[v]', '-map', '2:a', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-shortest', str(target)],
        capture_output=True, text=True, timeout=300, check=True)
    return target


@unittest.skipUnless(HAS_FFMPEG, 'ffmpeg and ffprobe are required')
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.source = base / 'source'
        self.source.mkdir()
        self.video = make_fixture(self.source)
        self.blob = git_blob_sha1(self.video)
        self.pipeline = VideoPipeline(self.source, base / 'state', base / 'artifacts',
                                      registry=AdapterRegistry())

    def tearDown(self):
        self.tmp.cleanup()

    def run_default(self, registry=None, language_hint=None, max_frames=6):
        if registry is not None:
            self.pipeline.registry = registry
        return self.pipeline.run('fixture.mp4', 'fixture-collection', self.blob,
                                 language_hint=language_hint, max_frames=max_frames)

    def test_identity_mismatch_refuses(self):
        with self.assertRaises(ValueError):
            self.pipeline.run('fixture.mp4', 'fixture-collection', '0' * 40)

    def test_decode_probe_and_audio_succeed(self):
        report = self.run_default()
        self.assertEqual(report['stages']['probe'], 'PASS')
        self.assertEqual(report['stages']['audio_extract'], 'PASS')
        self.assertEqual(report['metadata']['video_streams'][0]['width'], 320)
        self.assertEqual(len(report['metadata']['audio_streams']), 1)

    def test_missing_engines_block_and_create_no_spans(self):
        report = self.run_default()
        self.assertEqual(report['stages']['asr'], 'BLOCKED')
        self.assertEqual(report['span_count'], 0)
        self.assertEqual(report['status'], 'BLOCKED')
        gaps = {gap['stage'] for gap in report['capability_gaps']}
        self.assertIn('asr', gaps)
        self.assertEqual(stage_summary(report)['asr'], 'BLOCKED')

    def test_ocr_and_asr_spans_are_located_and_verbatim(self):
        registry = AdapterRegistry()
        registry.register_ocr(StubOcr())
        registry.register_asr(StubAsr())
        report = self.run_default(registry=registry)
        self.assertEqual(report['stages']['ocr'], 'PASS')
        self.assertEqual(report['stages']['asr'], 'PASS')
        frame_spans = [s for s in report['spans'] if s['method'] == 'OCR']
        asr_spans = [s for s in report['spans'] if s['method'] == 'ASR']
        self.assertTrue(frame_spans)
        self.assertTrue(asr_spans)
        self.assertIn('MAURYA', [s['original_text'] for s in frame_spans])
        self.assertEqual(frame_spans[0]['location']['kind'], 'video_frame_region')
        self.assertIn('at_seconds', frame_spans[0]['location'])
        self.assertEqual(asr_spans[0]['location']['kind'], 'video_interval')
        self.assertEqual(asr_spans[0]['original_text'], 'ఇది పరీక్ష')
        self.assertEqual(asr_spans[0]['language'], 'te')

    def test_low_confidence_is_marked_not_repaired(self):
        registry = AdapterRegistry()
        registry.register_ocr(StubOcr())
        registry.register_asr(StubAsr())
        report = self.run_default(registry=registry)
        low = [s for s in report['spans'] if s['low_confidence']]
        texts = [s['original_text'] for s in low]
        self.assertIn('unclear word', texts)
        self.assertIn('CHANDRAGUPTA', texts)

    def test_language_capability_gap_is_blocked_not_substituted(self):
        registry = AdapterRegistry()
        registry.register_asr(TeluguOnlyAsr())
        report = self.run_default(registry=registry, language_hint='en')
        self.assertEqual(report['stages']['asr'], 'BLOCKED')
        self.assertEqual(report['span_count'], 0)

    def test_adapter_raising_capability_unavailable_is_blocked(self):
        registry = AdapterRegistry()
        registry.register_asr(TeluguOnlyAsr())
        report = self.run_default(registry=registry, language_hint='te')
        self.assertEqual(report['stages']['asr'], 'BLOCKED')

    def test_rerun_reuses_work_and_does_not_duplicate(self):
        registry = AdapterRegistry()
        ocr = StubOcr()
        asr = StubAsr()
        registry.register_ocr(ocr)
        registry.register_asr(asr)
        first = self.run_default(registry=registry)

        def stage_counts():
            counts = {}
            for record in self.pipeline.journal.records('attempt'):
                stage = record['payload']['stage']
                counts[stage] = counts.get(stage, 0) + 1
            return counts

        assets_before = len(self.pipeline.journal.records('asset'))
        counts_before = stage_counts()
        spans_before = len(self.pipeline.journal.records('span'))
        second = self.run_default(registry=registry)
        counts_after = stage_counts()
        self.assertEqual(assets_before, len(self.pipeline.journal.records('asset')))
        self.assertEqual(spans_before, len(self.pipeline.journal.records('span')))
        # Every processing stage is reused. Only the identity check is re-recorded,
        # because each run genuinely re-verifies the bytes against the committed blob.
        for stage in ('probe', 'audio_extract', 'scene_sample', 'frame', 'ocr', 'asr'):
            self.assertEqual(counts_before.get(stage, 0), counts_after.get(stage, 0), stage)
        self.assertEqual(counts_after['identity'], counts_before['identity'] + 1)
        self.assertEqual(first['span_count'], second['span_count'])
        self.assertEqual(ocr.calls, len(first['frames']))
        self.assertEqual(asr.calls, 1)

    def test_changed_source_refuses_reuse(self):
        self.run_default()
        self.video.write_bytes(self.video.read_bytes() + b'tamper')
        with self.assertRaises(ValueError):
            self.pipeline.run('fixture.mp4', 'fixture-collection', self.blob)

    def test_state_root_inside_source_refused(self):
        with self.assertRaises(ValueError):
            VideoPipeline(self.source, self.source / 'state', self.source / 'art')

    def test_artifacts_inside_source_refused(self):
        base = Path(self.tmp.name)
        with self.assertRaises(ValueError):
            VideoPipeline(self.source, base / 'state2', self.source / 'art')

    def test_asr_invalid_interval_is_rejected(self):
        registry = AdapterRegistry()
        registry.register_asr(StubAsr(segments=[{'start': 5.0, 'end': 1.0,
                                                 'text': 'bad', 'language': 'en',
                                                 'confidence': 0.9}]))
        with self.assertRaises(ValueError):
            self.run_default(registry=registry)

    def test_asr_unexpected_language_is_rejected(self):
        registry = AdapterRegistry()
        registry.register_asr(StubAsr(segments=[{'start': 0.0, 'end': 1.0,
                                                 'text': 'x', 'language': 'hi',
                                                 'confidence': 0.9}]))
        with self.assertRaises(ValueError):
            self.run_default(registry=registry)

    def test_asr_span_interval_must_be_inside_duration(self):
        registry = AdapterRegistry()
        registry.register_asr(StubAsr(segments=[{'start': 0.0, 'end': 9999.0,
                                                 'text': 'too long', 'language': 'en',
                                                 'confidence': 0.9}]))
        with self.assertRaises(ValueError):
            self.run_default(registry=registry)

    def test_frame_region_outside_frame_is_rejected(self):
        report = self.run_default()
        asset = self.pipeline.journal.records('asset')[0]
        probe = [r for r in self.pipeline.journal.records('attempt')
                 if r['payload']['stage'] == 'probe'][0]
        location = {'kind': 'video_frame_region', 'at_seconds': 0.5,
                    'xyxy': [0, 0, 9999, 9999], 'frame_sha256': 'x'}
        extraction = {'processor': 'stub', 'version': '1', 'method': 'OCR'}
        with self.assertRaises(ValueError):
            self.pipeline.frame_span(asset, probe, location, 'text', 'en', extraction)
        self.assertEqual(report['stages']['probe'], 'PASS')

    def test_sampling_policy_is_recorded(self):
        report = self.run_default()
        self.assertIn(report['sampling_policy'],
                      {'scene_change', 'fixed_fraction_fallback',
                       'scene_change_downsampled', 'fixed_fraction_fallback_downsampled'})
        self.assertTrue(report['sampled_timestamps'])


class RegistryTests(unittest.TestCase):
    def test_empty_registry_returns_none(self):
        registry = AdapterRegistry()
        self.assertIsNone(registry.asr('te'))
        self.assertIsNone(registry.ocr('te'))

    def test_base_adapters_are_unavailable_by_default(self):
        self.assertFalse(AsrAdapter().available())
        self.assertFalse(OcrAdapter().available())
        with self.assertRaises(CapabilityUnavailable):
            AsrAdapter().transcribe('x')
        with self.assertRaises(CapabilityUnavailable):
            OcrAdapter().recognize('x')

    def test_first_usable_adapter_wins(self):
        registry = AdapterRegistry()
        registry.register_asr(TeluguOnlyAsr())
        registry.register_asr(StubAsr())
        self.assertIsInstance(registry.asr('en'), StubAsr)
        self.assertIsInstance(registry.asr('te'), TeluguOnlyAsr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
