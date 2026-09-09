"""SPEC-INT-012 tests: knowledge graph fail-closed status and rule derivation.

These tests target the failure modes that damaged this project before:
silent promotion, unsupported exam relationships, and rewritten history.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import series_derive  # noqa: E402
from evidence_store import Journal, assess, revision  # noqa: E402
from knowledge_graph import Graph, learning_view, node_status  # noqa: E402

SUBJECT = {'method_id': 'MET-TEST-0001', 'rule': 'a(n) = 2*n + 1'}


def passing_checks():
    return [
        {'kind': 'valid_case', 'procedure': 'n=1', 'observed': 3, 'expected': 3, 'passed': True},
        {'kind': 'valid_case', 'procedure': 'n=2', 'observed': 5, 'expected': 5, 'passed': True},
        {'kind': 'boundary_case', 'procedure': 'n=0', 'observed': 1, 'expected': 1, 'passed': True},
    ]


class GraphStructureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.graph = Graph(base / 'graph')
        self.journal = Journal(base / 'journal')
        self.evidence = base / 'evidence'
        self.evidence.mkdir()
        (self.evidence / 'proof.json').write_text('{"ok": true}', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def add_method(self, node_id='MET-TEST-0001', origin='MODEL_DERIVED', subject=None):
        return self.graph.add_node(node_id=node_id, node_kind='method', origin=origin,
                                   subject=subject or SUBJECT)

    def test_unknown_kind_and_origin_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.add_node(node_id='X', node_kind='not_a_kind',
                                origin='MODEL_DERIVED', subject={'a': 1})
        with self.assertRaises(ValueError):
            self.graph.add_node(node_id='X', node_kind='concept',
                                origin='TRUST_ME', subject={'a': 1})

    def test_nodes_are_append_only(self):
        self.add_method()
        with self.assertRaises(ValueError):
            self.add_method()

    def test_edges_require_existing_nodes(self):
        self.add_method()
        with self.assertRaises(ValueError):
            self.graph.add_edge(edge_kind='uses_concept', source_id='MET-TEST-0001',
                                target_id='CON-MISSING')

    def test_pyq_edge_refused_without_evidence(self):
        self.add_method()
        self.graph.add_node(node_id='Q-PYQ-010001', node_kind='pyq_question',
                            origin='OFFICIAL_DOCUMENT', subject={'pyq_id': 'Q-PYQ-010001'})
        with self.assertRaises(ValueError):
            self.graph.add_edge(edge_kind='solves', source_id='MET-TEST-0001',
                                target_id='Q-PYQ-010001',
                                known_pyq_ids=['Q-PYQ-010001'])

    def test_pyq_edge_refused_for_unknown_question_id(self):
        self.add_method()
        self.graph.add_node(node_id='Q-FAKE', node_kind='pyq_question',
                            origin='MODEL_DERIVED', subject={'pyq_id': 'Q-FAKE'})
        with self.assertRaises(ValueError):
            self.graph.add_edge(edge_kind='solves', source_id='MET-TEST-0001',
                                target_id='Q-FAKE', evidence_root=self.evidence,
                                evidence_paths=['proof.json'], justification='because',
                                known_pyq_ids=['Q-PYQ-010001'])

    def test_pyq_edge_accepted_with_evidence_and_known_id(self):
        self.add_method()
        self.graph.add_node(node_id='Q-PYQ-010001', node_kind='pyq_question',
                            origin='OFFICIAL_DOCUMENT', subject={'pyq_id': 'Q-PYQ-010001'})
        edge = self.graph.add_edge(edge_kind='solves', source_id='MET-TEST-0001',
                                   target_id='Q-PYQ-010001', evidence_root=self.evidence,
                                   evidence_paths=['proof.json'],
                                   justification='the recomputed rule reproduces the answer',
                                   known_pyq_ids=['Q-PYQ-010001'])
        self.assertEqual(len(edge['payload']['evidence']), 1)

    def test_corrupt_record_detected(self):
        self.add_method()
        target = next(p for p in Path(self.graph.root).iterdir() if p.suffix == '.json')
        item = json.loads(target.read_text())
        item['record']['payload']['origin'] = 'OFFICIAL_DOCUMENT'
        target.write_text(json.dumps(item), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.graph.nodes()


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.graph = Graph(base / 'graph')
        self.journal = Journal(base / 'journal')
        self.evidence = base / 'evidence'
        self.evidence.mkdir()
        (self.evidence / 'proof.json').write_text('{"ok": true}', encoding='utf-8')
        self.graph.add_node(node_id='MET-TEST-0001', node_kind='method',
                            origin='MODEL_DERIVED', subject=SUBJECT)

    def tearDown(self):
        self.tmp.cleanup()

    def status(self):
        return node_status(self.graph, self.journal, 'MET-TEST-0001', self.evidence)

    def record(self, dimension, result, **kwargs):
        params = dict(
            subject_id='MET-TEST-0001', subject_revision=revision(SUBJECT),
            dimension=dimension, result=result,
            procedure='independent recomputation', assessor='tests',
            author='model', approach='DETERMINISTIC', evidence_root=self.evidence,
            evidence_paths=['proof.json'], checks=passing_checks(), limitations=[])
        params.update(kwargs)
        return assess(self.journal, **params)

    def test_model_node_without_evidence_is_candidate(self):
        self.assertEqual(self.status(), 'CANDIDATE')

    def test_fail_dominates_even_after_a_pass(self):
        self.record('correctness', 'PASS')
        self.record('applicability', 'PASS', approach='INDEPENDENT_MODEL', assessor='reviewer')
        self.assertEqual(self.status(), 'VERIFIED')
        self.record('speed', 'FAIL', checks=[
            {'kind': 'valid_case', 'procedure': 'timing', 'observed': 1,
             'expected': 2, 'passed': False}])
        self.assertEqual(self.status(), 'FAILED')

    def test_inconclusive_reads_as_unverified(self):
        self.record('correctness', 'INCONCLUSIVE')
        self.assertEqual(self.status(), 'UNVERIFIED')

    def test_limitations_block_verified(self):
        self.record('correctness', 'PASS', limitations=['one handwritten digit may be misread'])
        self.record('applicability', 'PASS', approach='INDEPENDENT_MODEL', assessor='reviewer')
        self.assertNotEqual(self.status(), 'VERIFIED')

    def test_new_revision_drops_back_from_verified(self):
        self.record('correctness', 'PASS')
        self.record('applicability', 'PASS', approach='INDEPENDENT_MODEL', assessor='reviewer')
        self.assertEqual(self.status(), 'VERIFIED')
        changed = dict(SUBJECT, rule='a(n) = 2*n + 2')
        self.graph.add_node(node_id='MET-TEST-0002', node_kind='method',
                            origin='MODEL_DERIVED', subject=changed)
        self.assertEqual(
            node_status(self.graph, self.journal, 'MET-TEST-0002', self.evidence),
            'CANDIDATE')

    def test_blocked_node_never_reads_as_anything_else(self):
        self.graph.add_node(node_id='OBS-AUDIO', node_kind='observation',
                            origin='SOURCE_DERIVED', subject={'expected': 'audio'},
                            blocked_reason='no ASR engine available')
        self.assertEqual(
            node_status(self.graph, self.journal, 'OBS-AUDIO', self.evidence), 'BLOCKED')

    def test_source_derived_with_located_evidence_is_supported_not_verified(self):
        self.graph.add_node(node_id='ASSET-1', node_kind='asset', origin='SOURCE_DERIVED',
                            subject={'sha256': 'a' * 64})
        self.graph.add_node(node_id='OBS-1', node_kind='observation', origin='SOURCE_DERIVED',
                            subject={'text': 'visible table'}, text='visible table')
        self.graph.add_edge(edge_kind='derived_from', source_id='OBS-1', target_id='ASSET-1')
        self.assertEqual(
            node_status(self.graph, self.journal, 'OBS-1', self.evidence), 'SUPPORTED')

    def test_learning_view_exposes_status_and_no_reliability_claim(self):
        view = learning_view(self.graph, self.journal, 'MET-TEST-0001', self.evidence)
        self.assertEqual(view['status'], 'CANDIDATE')
        self.assertEqual(view['pyq_links'], [])
        self.assertNotIn('reliable', json.dumps(view))


class SeriesDerivationTests(unittest.TestCase):
    def test_linear_rule_is_found(self):
        pairs = [(1, 3), (2, 5), (3, 7), (4, 9), (5, 11)]
        result = series_derive.derive(pairs)
        self.assertEqual(result['result'], 'PASS')
        self.assertTrue(any('2*n**1' in m['expression'] or '2*n' in m['expression']
                            for m in result['matching_rules']))

    def test_quadratic_rule_is_found(self):
        pairs = [(n, n * n + 1) for n in range(1, 7)]
        result = series_derive.derive(pairs)
        self.assertEqual(result['result'], 'PASS')
        self.assertTrue(result['polynomial_fit']['fits'])

    def test_step_rule_is_found(self):
        values, current = [], 5
        for n in range(1, 8):
            current = current + 3 * n if n > 1 else current
            values.append((n, current))
        result = series_derive.derive(values)
        self.assertEqual(result['result'], 'PASS')

    def test_observed_code_table_does_not_fit_the_declared_space(self):
        pairs = [(1, 1), (2, 5), (3, 13), (4, 27), (5, 48), (6, 78), (7, 118), (8, 170)]
        result = series_derive.derive(pairs)
        self.assertEqual(result['result'], 'FAIL')
        self.assertEqual(result['matching_rules'], [])
        self.assertFalse(result['polynomial_fit']['fits'])
        self.assertEqual(result['observed_difference_table'][0],
                         [4, 8, 14, 21, 30, 40, 52])

    def test_too_few_pairs_refused(self):
        with self.assertRaises(ValueError):
            series_derive.derive([(1, 1), (2, 5), (3, 13)])

    def test_checks_fail_when_rule_does_not_reproduce_values(self):
        pairs = [(1, 1), (2, 5), (3, 13), (4, 27)]
        checks = series_derive.deterministic_checks(pairs, lambda n: 2 * n)
        self.assertTrue(any(c['passed'] is False for c in checks))


if __name__ == '__main__':
    unittest.main()
