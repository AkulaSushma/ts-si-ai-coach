"""Acceptance tests for the video-capable evidence path (SPEC-INT-011).

All media used here is a locally generated TEST FIXTURE produced by ffmpeg. It is
not expert material and no fixture result is ever presented as knowledge about
the real collection. The real collection assets are exercised by the pilot
runners, not by these tests.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from build_asset_plan import build, from_listing  # noqa: E402
from video_intake import VideoIntake, git_blob_sha1, media_class  # noqa: E402

FFMPEG = shutil.which('ffmpeg')
FFPROBE = shutil.which('ffprobe')


def make_fixture(path, *, seconds=3, with_audio=True):
    command = [FFMPEG, '-y', '-f', 'lavfi', '-i',
               f'testsrc=size=320x240:rate=10:duration={seconds}']
    if with_audio:
        command += ['-f', 'lavfi', '-i', f'sine=frequency=440:duration={seconds}',
                    '-c:a', 'aac']
    command += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-t', str(seconds), str(path)]
    subprocess.run(command, capture_output=True, check=True, timeout=180)


@unittest.skipIf(not FFMPEG or not FFPROBE, 'ffmpeg/ffprobe unavailable')
class VideoEvidencePathTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.source = root / 'raw'
        self.state = root / 'state'
        self.artifacts = root / 'artifacts'
        self.source.mkdir()
        self.video = self.source / 'fixture.mp4'
        make_fixture(self.video)
        self.intake = VideoIntake(self.source, self.state)
        self.blob = git_blob_sha1(self.video)
        self.addCleanup(self.tmp.cleanup)

    def register(self):
        return self.intake.register_committed('fixture.mp4', 'fixture-collection', self.blob)

    def test_identity_mismatch_is_refused(self):
        with self.assertRaises(ValueError):
            self.intake.register_committed('fixture.mp4', 'fixture-collection', '0' * 40)
        self.assertEqual(self.intake.journal.records('asset'), [])

    def test_identity_must_be_a_blob_sha(self):
        with self.assertRaises(ValueError):
            self.intake.register_committed('fixture.mp4', 'fixture-collection', 'abc')

    def test_registration_records_identity_evidence(self):
        asset = self.register()
        identity = [r['payload'] for r in self.intake.journal.records('attempt')
                    if r['payload']['stage'] == 'identity']
        self.assertEqual(len(identity), 1)
        self.assertEqual(identity[0]['git_blob_sha1'], self.blob)
        self.assertEqual(identity[0]['result'], 'PASS')
        self.assertEqual(len(asset['payload']['sha256']), 64)

    def test_probe_and_frames_are_reproducible_and_hashed(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        self.assertEqual(probe['payload']['result'], 'PASS')
        self.assertGreater(self.intake.duration_seconds(probe), 0)
        planned = self.intake.planned_frames(probe)
        self.assertEqual(len(planned), 3)
        first = self.intake.frame(asset, probe, 'fixture.mp4', planned[0], self.artifacts)
        self.assertEqual(first['payload']['result'], 'PASS')
        self.assertEqual(len(first['payload']['artifact_sha256']), 64)
        artifact = self.artifacts / first['payload']['artifact_name']
        self.assertTrue(artifact.exists())
        again = self.intake.frame(asset, probe, 'fixture.mp4', planned[0], self.artifacts)
        self.assertEqual(again['id'], first['id'])

    def test_frame_timestamp_outside_duration_is_refused(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        duration = self.intake.duration_seconds(probe)
        for bad in (-1, duration + 5, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                self.intake.frame(asset, probe, 'fixture.mp4', bad, self.artifacts)

    def test_frames_cannot_be_written_into_the_raw_source_root(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        with self.assertRaises(ValueError):
            self.intake.frame(asset, probe, 'fixture.mp4', 0.5, self.source / 'frames')

    def test_blocked_extraction_never_becomes_evidence(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        blocked = self.intake.blocked_extraction(asset, probe, 'asr', 'no engine configured')
        self.assertEqual(blocked['payload']['result'], 'BLOCKED')
        self.assertIsNone(blocked['payload']['output'])
        with self.assertRaises(ValueError):
            self.intake.span(asset, blocked,
                             {'kind': 'video_interval', 'start_seconds': 0.0, 'end_seconds': 1.0},
                             'invented transcript', 'en',
                             {'processor': 'x', 'version': '1', 'method': 'ASR'})
        self.assertEqual(self.intake.journal.records('span'), [])
        self.assertEqual(self.intake.journal.records('candidate'), [])

    def test_video_interval_span_and_origin_separation(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        duration = self.intake.duration_seconds(probe)
        span = self.intake.span(
            asset, probe,
            {'kind': 'video_interval', 'start_seconds': 0.0, 'end_seconds': min(1.0, duration)},
            'fixture pattern frame', 'en',
            {'processor': 'fixture', 'version': 'test-1', 'method': 'HUMAN_TRANSCRIPTION'})
        self.assertEqual(span['payload']['fidelity_status'], 'UNVERIFIED')
        self.assertEqual(span['payload']['asset_sha256'], asset['payload']['sha256'])
        source = self.intake.candidate(span, origin='SOURCE_DERIVED',
                                       text='fixture pattern frame',
                                       uncertainty='fixture only')
        model = self.intake.candidate(span, origin='MODEL_DERIVED',
                                      text='an interpretation of the fixture',
                                      uncertainty='model interpretation, unvalidated')
        self.assertEqual(source['payload']['provenance_tier'], 'T3_EXPERT')
        self.assertEqual(model['payload']['provenance_tier'], 'T4_AI')
        for record in (source, model):
            self.assertEqual(record['payload']['verification_status'], 'UNVERIFIED')
            self.assertEqual(record['payload']['pyq_links'], [])
        with self.assertRaises(ValueError):
            self.intake.candidate(span, origin='SOURCE_DERIVED', text='paraphrased wording',
                                  uncertainty='paraphrase must be interpretation')

    def test_interval_outside_duration_is_refused(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        duration = self.intake.duration_seconds(probe)
        with self.assertRaises(ValueError):
            self.intake.span(asset, probe,
                             {'kind': 'video_interval', 'start_seconds': 0.0,
                              'end_seconds': duration + 10},
                             'text', 'en',
                             {'processor': 'fixture', 'version': '1',
                              'method': 'HUMAN_TRANSCRIPTION'})

    def test_image_region_is_refused_for_video_assets(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        with self.assertRaises(ValueError):
            self.intake.span(asset, probe, {'kind': 'image_region', 'xyxy': [0, 0, 10, 10]},
                             'text', 'en',
                             {'processor': 'fixture', 'version': '1',
                              'method': 'HUMAN_TRANSCRIPTION'})

    def test_silent_video_reports_zero_audio_streams(self):
        silent = self.source / 'silent.mp4'
        make_fixture(silent, with_audio=False)
        asset = self.intake.register_committed('silent.mp4', 'fixture-collection',
                                               git_blob_sha1(silent))
        probe = self.intake.probe(asset, 'silent.mp4')
        self.assertEqual(self.intake.audio_streams(probe), [])

    def test_changed_bytes_block_further_derivation(self):
        asset = self.register()
        probe = self.intake.probe(asset, 'fixture.mp4')
        self.video.write_bytes(self.video.read_bytes() + b'tamper')
        with self.assertRaises(ValueError):
            self.intake.frame(asset, probe, 'fixture.mp4', 0.5, self.artifacts)


class AssetPlanTest(unittest.TestCase):
    LISTING = [
        {'name': 'Some Trick.mp4', 'size': 2347758, 'sha': 'a' * 40, 'type': 'file'},
        {'name': 'IMG_1.jpg', 'size': 266527, 'sha': 'b' * 40, 'type': 'file'},
        {'name': 'notes.txt', 'size': 12, 'sha': 'c' * 40, 'type': 'file'},
    ]

    def test_classification_and_treatment(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / 'listing.json'
            listing.write_text(json.dumps(self.LISTING), encoding='utf-8')
            plan = build(from_listing(listing))
        self.assertEqual(plan['totals'],
                         {'assets': 3, 'videos': 1, 'images': 1, 'unsupported': 1,
                          'bytes': 2347758 + 266527 + 12})
        by_class = {a['media_class']: a for a in plan['assets']}
        self.assertIn('frame_sampling', by_class['VIDEO']['treatment']['stages'])
        self.assertEqual(by_class['VIDEO']['treatment']['evidence_location'], 'video_interval')
        self.assertEqual(by_class['IMAGE']['treatment']['evidence_location'], 'image_region')
        self.assertIsNone(by_class['UNSUPPORTED']['treatment']['evidence_location'])

    def test_unobserved_fields_stay_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / 'listing.json'
            listing.write_text(json.dumps(self.LISTING), encoding='utf-8')
            plan = build(from_listing(listing))
        for asset in plan['assets']:
            self.assertIsNone(asset['source_url'])
            self.assertIsNone(asset['publisher'])
            self.assertIsNone(asset['published_at'])
            self.assertEqual(asset['attribution_status'], 'UNKNOWN_NOT_OBSERVED')
            self.assertEqual(asset['transcript_status'], 'ABSENT')
            self.assertEqual(asset['pyq_relationships_status'], 'NOT_EVALUATED')
            self.assertEqual(asset['processing_state'], 'NOT_STARTED')

    def test_media_class_helper(self):
        self.assertEqual(media_class('a/b.MP4'), 'VIDEO')
        self.assertEqual(media_class('a/b.JPG'), 'IMAGE')
        self.assertEqual(media_class('a/b.pdf'), 'UNSUPPORTED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
