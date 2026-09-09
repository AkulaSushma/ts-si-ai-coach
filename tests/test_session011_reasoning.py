"""Tests for independent reasoning verification and fail-closed promotion (SPEC-INT-011).

These tests exercise the deterministic recomputation module and the promotion
gate. They do not verify any expert claim; they verify that the pipeline treats
correctness, applicability and speed as independent and refuses to promote on
incomplete or failed evidence.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from evidence_store import Journal, assess, eligible, fast_method_state, revision  # noqa: E402
import reasoning_verify  # noqa: E402

METHOD = {'method_id': 'MET-TEST-0001', 'rule': 'digit product times six'}


class ReasoningVerifyTest(unittest.TestCase):
    def test_recomputes_observed_pairs(self):
        results = reasoning_verify.check_analogy([(86, 288), (36, 108)], 6)
        self.assertTrue(all(r['matches'] for r in results))
        self.assertEqual(results[0]['stages']['digit_product'], 48)
        self.assertEqual(results[1]['computed_output'], 108)

    def test_rejects_a_wrong_rule_statement(self):
        # Multiplying by the factor twice does not reproduce the observed pair.
        doubled = reasoning_verify.digit_product_scaled(86, 6)['result'] * 6
        self.assertNotEqual(doubled, 288)

    def test_zero_digit_is_a_real_applicability_boundary(self):
        boundary = reasoning_verify.failure_boundary(40, 6)
        self.assertTrue(boundary['degenerate'])
        self.assertEqual(boundary['result'], 0)
        self.assertFalse(reasoning_verify.failure_boundary(36, 6)['degenerate'])

    def test_single_pair_does_not_determine_a_unique_rule(self):
        matches = reasoning_verify.alternative_rule_count((48, 288))
        self.assertGreaterEqual(len(matches), 2)

    def test_input_validation(self):
        for bad in (-1, 1.5, True, '86', None):
            with self.assertRaises(ValueError):
                reasoning_verify.digits(bad)


class PromotionGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence = self.root / 'evidence'
        self.journal = Journal(self.root / 'journal')
        self.revision = revision(METHOD)
        self.addCleanup(self.tmp.cleanup)

    def evidence_file(self, name='report.json'):
        reasoning_verify.write_report(self.evidence / name, {'ok': True})
        return name

    def correctness_checks(self, ok=True):
        return [
            {'kind': 'valid_case', 'procedure': '86', 'observed': 288, 'expected': 288, 'passed': ok},
            {'kind': 'valid_case', 'procedure': '36', 'observed': 108, 'expected': 108, 'passed': ok},
            {'kind': 'boundary_case', 'procedure': 'zero digit', 'observed': True,
             'expected': True, 'passed': ok},
        ]

    def record(self, dimension, result, approach='DETERMINISTIC', checks=None, limitations=None):
        return assess(self.journal, subject_id=METHOD['method_id'],
                      subject_revision=self.revision, dimension=dimension, result=result,
                      procedure='recomputation', assessor='reasoning_verify.py',
                      author='media candidate', approach=approach,
                      evidence_root=self.evidence, evidence_paths=[self.evidence_file()],
                      checks=checks if checks is not None else self.correctness_checks(),
                      limitations=[] if limitations is None else limitations)

    def test_correctness_alone_never_makes_a_fast_method(self):
        self.record('correctness', 'PASS')
        self.assertTrue(eligible(self.journal, METHOD['method_id'], self.revision,
                                 ('correctness',), self.evidence))
        self.assertEqual(fast_method_state(self.journal, METHOD['method_id'], self.revision,
                                           self.evidence), 'UNVERIFIED_FAST_METHOD')

    def test_failed_correctness_is_retained_and_blocks(self):
        self.record('correctness', 'FAIL', checks=self.correctness_checks(ok=False))
        stored = [r['payload'] for r in self.journal.records('assessment')]
        self.assertEqual([s['result'] for s in stored], ['FAIL'])
        self.assertFalse(eligible(self.journal, METHOD['method_id'], self.revision,
                                  ('correctness',), self.evidence))

    def test_a_later_pass_cannot_erase_an_earlier_failure(self):
        self.record('correctness', 'FAIL', checks=self.correctness_checks(ok=False))
        self.record('correctness', 'PASS')
        self.assertEqual(len(self.journal.records('assessment')), 2)
        self.assertFalse(eligible(self.journal, METHOD['method_id'], self.revision,
                                  ('correctness',), self.evidence))

    def test_a_corrected_rule_statement_is_a_new_subject_revision(self):
        self.record('correctness', 'FAIL', checks=self.correctness_checks(ok=False))
        corrected = revision(dict(METHOD, rule='digit product times six, corrected'))
        self.assertNotEqual(corrected, self.revision)
        assess(self.journal, subject_id=METHOD['method_id'], subject_revision=corrected,
               dimension='correctness', result='PASS', procedure='recomputation',
               assessor='reasoning_verify.py', author='media candidate',
               approach='DETERMINISTIC', evidence_root=self.evidence,
               evidence_paths=[self.evidence_file()], checks=self.correctness_checks(),
               limitations=[])
        self.assertTrue(eligible(self.journal, METHOD['method_id'], corrected,
                                 ('correctness',), self.evidence))
        self.assertFalse(eligible(self.journal, METHOD['method_id'], self.revision,
                                  ('correctness',), self.evidence))

    def test_speed_and_applicability_must_be_separately_evidenced(self):
        self.record('correctness', 'PASS')
        self.record('applicability', 'PASS', approach='SOURCE_DOCUMENT',
                    checks=[{'kind': 'valid_case', 'procedure': 'family coverage',
                             'observed': 3, 'expected': 3, 'passed': True}])
        self.assertEqual(fast_method_state(self.journal, METHOD['method_id'], self.revision,
                                           self.evidence), 'UNVERIFIED_FAST_METHOD')
        self.record('speed', 'PASS', approach='DETERMINISTIC',
                    checks=[{'kind': 'valid_case', 'procedure': 'timed steps',
                             'observed': 2, 'expected': 2, 'passed': True}])
        self.assertEqual(fast_method_state(self.journal, METHOD['method_id'], self.revision,
                                           self.evidence), 'VERIFIED_FAST_METHOD')

    def test_limitations_block_promotion(self):
        self.record('correctness', 'PASS', limitations=['only two cases checked'])
        self.assertFalse(eligible(self.journal, METHOD['method_id'], self.revision,
                                  ('correctness',), self.evidence))


if __name__ == '__main__':
    unittest.main(verbosity=2)
