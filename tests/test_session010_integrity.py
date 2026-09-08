"""Offline poisoned-record regressions; fixtures are NOT verified exam methods."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from evidence_store import Journal, assess, eligible, revision, fast_method_state
from media_intake import Intake


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.j = Journal(self.root / 'journal')
        (self.root / 'evidence.txt').write_text('SYNTHETIC FIXTURE; not exam-method evidence')
        self.rev = revision({'method': 'fixture', 'version': 1})
        self.args = dict(subject_id='FIXTURE', subject_revision=self.rev,
            dimension='correctness', result='PASS', procedure='fixture gate exercise',
            assessor='fixture_runner', author='fixture_author', approach='DETERMINISTIC',
            evidence_root=self.root, evidence_paths=['evidence.txt'], limitations=[],
            checks=[{'kind': kind, 'procedure': str(i), 'observed': i, 'expected': i, 'passed': True}
                    for i, kind in enumerate(['valid_case', 'valid_case', 'boundary_case'])])

    def permitted(self, dims=('correctness',), rev=None):
        return eligible(self.j, 'FIXTURE', rev or self.rev, dims, self.root)

    def test_absent_evidence_denies(self):
        self.assertFalse(self.permitted())

    def test_complete_pass_supports_only_checked_dimension(self):
        assess(self.j, **self.args)
        self.assertTrue(self.permitted())
        self.assertFalse(self.permitted(('speed',)))
        self.assertFalse(self.permitted(('correctness', 'applicability')))

    def test_fast_state_requires_all_three_dimensions(self):
        assess(self.j, **self.args)
        self.assertEqual(fast_method_state(self.j, 'FIXTURE', self.rev, self.root), 'UNVERIFIED_FAST_METHOD')
        for dimension in ('applicability', 'speed'):
            assess(self.j, **dict(self.args, dimension=dimension))
        self.assertEqual(fast_method_state(self.j, 'FIXTURE', self.rev, self.root), 'VERIFIED_FAST_METHOD')
        assess(self.j, **dict(self.args, dimension='speed', result='FAIL'))
        self.assertEqual(fast_method_state(self.j, 'FIXTURE', self.rev, self.root), 'UNVERIFIED_FAST_METHOD')

    def test_fail_and_inconclusive_never_promote(self):
        for result in ('FAIL', 'INCONCLUSIVE'):
            with self.subTest(result=result):
                args = dict(self.args, result=result)
                assess(self.j, **args)
                self.assertFalse(self.permitted())

    def test_failure_then_pass_keeps_history_and_blocks(self):
        first = assess(self.j, **dict(self.args, result='FAIL'))
        raw = (self.j.root / (first['id'] + '.json')).read_bytes()
        assess(self.j, **self.args)
        self.assertEqual(len(self.j.records('assessment')), 2)
        self.assertEqual(raw, (self.j.root / (first['id'] + '.json')).read_bytes())
        self.assertFalse(self.permitted())

    def test_wrong_subject_revision_and_dimension(self):
        assess(self.j, **self.args)
        self.assertFalse(self.permitted(rev=revision({'version': 2})))
        self.assertFalse(eligible(self.j, 'OTHER', self.rev, ['correctness'], self.root))
        self.assertFalse(self.permitted(()))
        self.assertFalse(self.permitted(('unknown',)))

    def test_incomplete_poisoned_assessments(self):
        poisons = [dict(evidence_paths=[]), dict(checks=[]), dict(assessor=''),
                   dict(limitations=['unresolved']), dict(approach='SELF_REVIEW'),
                   dict(checks=[self.args['checks'][0]]), dict(procedure='')]
        for i, poison in enumerate(poisons):
            with self.subTest(poison=poison):
                j = Journal(self.root / str(i))
                assess(j, **dict(self.args, **poison))
                self.assertFalse(eligible(j, 'FIXTURE', self.rev, ['correctness'], self.root))

    def test_claimed_pass_with_actual_mismatch_denies(self):
        args = copy.deepcopy(self.args)
        args['checks'][0]['observed'] = 999
        assess(self.j, **args)
        self.assertFalse(self.permitted())

    def test_boolean_string_is_not_pass(self):
        args = copy.deepcopy(self.args)
        args['checks'][0]['passed'] = 'true'
        assess(self.j, **args)
        self.assertFalse(self.permitted())

    def test_evidence_tamper_and_removal_deny(self):
        assess(self.j, **self.args)
        (self.root / 'evidence.txt').write_text('changed')
        self.assertFalse(self.permitted())
        (self.root / 'evidence.txt').unlink()
        self.assertFalse(self.permitted())

    def test_record_corruption_denies(self):
        row = assess(self.j, **self.args)
        (self.j.root / (row['id'] + '.json')).write_text('{')
        self.assertFalse(self.permitted())

    def test_self_review_for_recognition_denies(self):
        assess(self.j, **dict(self.args, dimension='recognition', approach='INDEPENDENT_MODEL', assessor='fixture_author'))
        self.assertFalse(self.permitted(('recognition',)))

    def test_legacy_entrypoint_no_mutation(self):
        data = self.root / 'pyq' / 'intelligence'
        data.mkdir(parents=True)
        for name in ('methods', 'questions', 'verifications'):
            (data / (name + '.json')).write_text('[{"test_fixture":true}]')
        before = {p.name: p.read_bytes() for p in data.iterdir()}
        run = subprocess.run([sys.executable, str(ROOT / 'outputs' / 'verify_fast_methods.py')], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn('BLOCKED', run.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in data.iterdir()})

    def test_interrupted_append_not_committed(self):
        with patch('evidence_store.os.link', side_effect=OSError('simulated interruption')):
            with self.assertRaises(OSError):
                self.j.append('attempt', {'fixture': True})
        self.assertEqual(self.j.records(), [])
        self.assertEqual(len(list(self.j.root.glob('*.pending'))), 1)
        self.j.append('attempt', {'retry': True})
        self.assertEqual(len(self.j.records()), 1)


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'raw'
        self.source.mkdir()
        (self.source / 'a.jpg').write_bytes(b'SYNTHETIC NOT REAL JPEG')
        self.intake = Intake(self.source, self.root / 'state')
        self.asset = self.intake.register('a.jpg', 'FIXTURE')

    def probe_fixture(self):
        return self.intake.journal.append('attempt', {'asset_id': self.asset['id'], 'result': 'PASS',
            'metadata': {'streams': [{'codec_type': 'video', 'width': 100, 'height': 100}]},
            'test_fixture': True})

    def span_fixture(self):
        return self.intake.span(self.asset, self.probe_fixture(),
            {'kind': 'image_region', 'xyxy': [0, 0, 100, 100]}, 'fixture text', 'en',
            {'processor': 'fixture', 'version': '1', 'method': 'HUMAN_TRANSCRIPTION'})

    def test_duplicate_bytes_preserve_occurrences_and_resume(self):
        (self.source / 'b.jpg').write_bytes((self.source / 'a.jpg').read_bytes())
        other = self.intake.register('b.jpg', 'FIXTURE')
        self.assertEqual(other['id'], self.asset['id'])
        self.intake.register('a.jpg', 'FIXTURE')
        self.assertEqual(len(self.intake.journal.records('asset')), 1)
        self.assertEqual(len(self.intake.journal.records('occurrence')), 2)

    def test_changed_bytes_create_revision(self):
        (self.source / 'a.jpg').write_bytes(b'changed fixture')
        other = self.intake.register('a.jpg', 'FIXTURE')
        self.assertNotEqual(other['id'], self.asset['id'])
        with self.assertRaises(ValueError):
            self.intake.probe(self.asset, 'a.jpg')

    def test_failed_probe_is_retained(self):
        for _ in range(2):
            result = self.intake.probe(self.asset, 'a.jpg', executable='missing-executable-fixture')
            self.assertEqual(result['payload']['result'], 'FAIL')
        self.assertEqual(len(self.intake.journal.records('attempt')), 2)

    def test_path_escape_and_raw_state_rejected(self):
        with self.assertRaises(ValueError):
            self.intake.register('../escape.jpg', 'FIXTURE')
        with self.assertRaises(ValueError):
            Intake(self.source, self.source / 'state')

    def test_region_bounds_and_model_provenance(self):
        probe = self.probe_fixture()
        with self.assertRaises(ValueError):
            self.intake.span(self.asset, probe, {'kind': 'image_region', 'xyxy': [0, 0, 101, 100]}, 'x', 'en', {'processor':'fixture', 'version':'1','method':'HUMAN_TRANSCRIPTION'})
        with self.assertRaises(ValueError):
            self.intake.span(self.asset, probe, {'kind': 'image_region', 'xyxy': [0, 0, 100, 100]}, 'x', 'en', {'processor':'fixture', 'version':'1','method':'MODEL_VISUAL'})

    def test_candidates_preserve_origin_and_never_verify(self):
        span = self.span_fixture()
        source = self.intake.candidate(span, origin='SOURCE_DERIVED', text='fixture text', uncertainty='fixture')
        model = self.intake.candidate(span, origin='MODEL_DERIVED', text='inference', uncertainty='not evaluated')
        self.assertEqual(source['payload']['provenance_tier'], 'T3_EXPERT')
        self.assertEqual(model['payload']['provenance_tier'], 'T4_AI')
        self.assertEqual(source['payload']['verification_status'], 'UNVERIFIED')
        with self.assertRaises(ValueError):
            self.intake.candidate(span, origin='SOURCE_DERIVED', text='invented quote', uncertainty='x')
        again = self.intake.candidate(span, origin='SOURCE_DERIVED', text='fixture text', uncertainty='fixture')
        self.assertEqual(source['id'], again['id'])


if __name__ == '__main__':
    unittest.main()
