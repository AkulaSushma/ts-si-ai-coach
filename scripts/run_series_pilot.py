"""Bounded real-media intelligence pilot (SPEC-INT-012).

Processes ONE real committed image end to end and builds the first nodes of the
exam-solving knowledge graph:

  Git blob identity -> ffprobe metadata -> located image region ->
  source-derived observation (verbatim visible table) ->
  model-derived hypothesis -> deterministic independent derivation ->
  fail-closed derived status -> learning projection

The asset shows a handwritten code table with NO stated rule and NO worked
steps. That is the interesting case: the rule must be derived, and if the
declared search space contains no rule reproducing every observed pair, the
honest outcome is FAIL. Nothing about the publisher, account, upload date,
spoken audio or PYQ relationship is asserted, because none was observed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_store import assess, revision  # noqa: E402
import series_derive  # noqa: E402
from knowledge_graph import Graph, learning_view, node_status  # noqa: E402
from video_intake import VideoIntake  # noqa: E402

RELATIVE = 'Screenshot_2026-09-01-19-51-42-53_1c337646f29875672b5a61192b9010f9.jpg'
GIT_BLOB = 'b1705377c83a99ace5c92f63a57eb626e11c4835'
COLLECTION = 'SI-Constable-media-b8facd4'

# Read from the actual decoded image. Layout order preserved, nothing added.
OBSERVED_TEXT = (
    'Code\n'
    '1 - 1\n'
    '2 - 5\n'
    '3 - 13\n'
    '4 - 27\n'
    '5 - 48\n'
    '6 - 78\n'
    '7 - 118\n'
    '8 - 170'
)

# Digit pairs as read. This is the extraction, not an interpretation.
OBSERVED_PAIRS = [(1, 1), (2, 5), (3, 13), (4, 27), (5, 48), (6, 78), (7, 118), (8, 170)]

SOURCE_UNCERTAINTY = (
    'Verbatim visible handwriting from one screenshot of a video frame, read '
    'visually without OCR. The image shows only the mapping; no rule, no worked '
    'steps and no question stem are visible. A horizontal rule is drawn under '
    '6 - 78, which may separate given terms from terms to be found, but the '
    'meaning of that line was not stated on screen. The digits 48 and 27 are '
    'handwritten and could in principle be misread.'
)

MODEL_HYPOTHESIS = (
    'A coaching code table of this shape is normally taught as a single '
    'generating rule in n. Candidate hypothesis: the values follow a low-degree '
    'polynomial in n, or a step rule a(n) = a(n-1) + f(n). This is a model '
    'hypothesis about the teaching intent, not an observed claim.'
)

MODEL_UNCERTAINTY = (
    'The rule is not visible in the asset. The spoken explanation that very '
    'likely accompanied this frame has not been processed, so the rule taught by '
    'the source is unknown. No speed, recognition or retention evidence exists '
    'and no PYQ has been linked.'
)

CONCEPT = {
    'concept_id': 'CON-MEDIA-0002',
    'name': 'Number-code table with a single generating rule',
    'domain': 'reasoning_coding_number_series',
    'statement': 'A code table maps consecutive integers to values produced by one rule in n.',
}

HYPOTHESIS_SUBJECT = {
    'method_id': 'MET-MEDIA-0002',
    'name': 'Generating rule for the observed code table',
    'domain': 'reasoning_coding_number_series',
    'rule': 'a low-degree polynomial in n, or a(n) = a(n-1) + f(n) with f polynomial',
    'observed_pairs': [list(p) for p in OBSERVED_PAIRS],
    'provenance_tier': 'T4_AI',
}

AUDIO_BLOCKED_REASON = (
    'No ASR engine is available and the source video for this frame has not been '
    'processed; the rule stated aloud is unknown.'
)

REGION = [260, 110, 780, 1180]


def build_checks(derivation):
    """Deterministic per-pair checks, or one explicit failure check."""
    if derivation['matching_rules']:
        expression = derivation['matching_rules'][0]['expression']
        checks = []
        last = len(OBSERVED_PAIRS) - 1
        for index, pair in enumerate(OBSERVED_PAIRS):
            n, value = pair
            checks.append({
                'kind': 'boundary_case' if index == last else 'valid_case',
                'procedure': 'reproduce observed value at n=' + str(n) + ' using ' + expression,
                'observed': value,
                'expected': value,
                'passed': True,
            })
        limitations = [] if derivation['unique'] else [
            'More than one rule in the declared space reproduces the observed pairs.'
        ]
        return checks, 'PASS', limitations

    checks = [{
        'kind': 'valid_case',
        'procedure': 'exhaustive search of the declared closed-form and step-rule space',
        'observed': 0,
        'expected': 1,
        'passed': False,
    }]
    limitations = [
        'No rule in the declared finite space reproduces all eight observed pairs.',
        'The spoken rule was not available and one handwritten digit may be misread.',
    ]
    return checks, 'FAIL', limitations


def build_graph(graph, asset, span):
    """Create the pilot nodes and only the edges the evidence supports."""
    graph.add_node(node_id=asset['id'], node_kind='asset', origin='SOURCE_DERIVED',
                   subject={'relative_path': RELATIVE, 'git_blob_sha1': GIT_BLOB,
                            'sha256': asset['payload']['sha256'],
                            'bytes': asset['payload']['bytes'],
                            'collection_id': COLLECTION})
    graph.add_node(node_id=span['id'], node_kind='evidence_span', origin='SOURCE_DERIVED',
                   subject={'location': {'kind': 'image_region', 'xyxy': REGION},
                            'asset_sha256': asset['payload']['sha256']},
                   language='en', text=OBSERVED_TEXT)
    graph.add_edge(edge_kind='locates', source_id=span['id'], target_id=asset['id'])

    graph.add_node(node_id='OBS-MEDIA-0002', node_kind='observation', origin='SOURCE_DERIVED',
                   subject={'observed_pairs': [list(p) for p in OBSERVED_PAIRS],
                            'visible_text': OBSERVED_TEXT},
                   language='en', text=OBSERVED_TEXT, uncertainty=SOURCE_UNCERTAINTY)
    graph.add_edge(edge_kind='derived_from', source_id='OBS-MEDIA-0002', target_id=span['id'])

    graph.add_node(node_id=CONCEPT['concept_id'], node_kind='concept', origin='MODEL_DERIVED',
                   subject=CONCEPT, language='en', text=CONCEPT['statement'],
                   uncertainty='Concept framing is model-supplied; the asset does not name it.')
    graph.add_edge(edge_kind='derived_from', source_id=CONCEPT['concept_id'], target_id=span['id'])

    graph.add_node(node_id=HYPOTHESIS_SUBJECT['method_id'], node_kind='method',
                   origin='MODEL_DERIVED', subject=HYPOTHESIS_SUBJECT,
                   language='en', text=MODEL_HYPOTHESIS, uncertainty=MODEL_UNCERTAINTY)
    graph.add_edge(edge_kind='derived_from',
                   source_id=HYPOTHESIS_SUBJECT['method_id'], target_id=span['id'])
    graph.add_edge(edge_kind='uses_concept',
                   source_id=HYPOTHESIS_SUBJECT['method_id'], target_id=CONCEPT['concept_id'])

    # Audio intelligence is genuinely unavailable, so the gap is recorded as a
    # BLOCKED node instead of being silently omitted from the graph.
    graph.add_node(node_id='OBS-MEDIA-0002-AUDIO', node_kind='observation',
                   origin='SOURCE_DERIVED',
                   subject={'asset_sha256': asset['payload']['sha256'],
                            'expected_content': 'spoken rule explanation for the code table'},
                   blocked_reason=AUDIO_BLOCKED_REASON)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--state-root', required=True)
    parser.add_argument('--evidence-root', required=True)
    parser.add_argument('--graph-root', required=True)
    args = parser.parse_args()

    intake = VideoIntake(args.source_root, args.state_root)
    asset = intake.register_committed(RELATIVE, COLLECTION, GIT_BLOB)
    probe = intake.probe(asset, RELATIVE)
    if probe['payload']['result'] != 'PASS':
        print(json.dumps({'status': 'BLOCKED', 'probe': probe['payload']}, indent=1))
        return 1
    stream = next(s for s in probe['payload']['metadata']['streams']
                  if s.get('codec_type') == 'video')
    width, height = int(stream['width']), int(stream['height'])

    span = intake.span(
        asset, probe,
        {'kind': 'image_region', 'xyxy': REGION,
         'note': 'handwritten code table; approximate visual bound, not OCR output'},
        OBSERVED_TEXT, 'en',
        {'processor': 'Notion AI', 'version': 'session012-visual-1', 'method': 'MODEL_VISUAL',
         'model': 'Notion AI', 'prompt_version': 'read-visible-handwriting-v1'})
    source_candidate = intake.candidate(span, origin='SOURCE_DERIVED', text=OBSERVED_TEXT,
                                        uncertainty=SOURCE_UNCERTAINTY)
    model_candidate = intake.candidate(span, origin='MODEL_DERIVED', text=MODEL_HYPOTHESIS,
                                       uncertainty=MODEL_UNCERTAINTY)

    derivation = series_derive.derive(OBSERVED_PAIRS)
    evidence_relative = 'session012/series_MET-MEDIA-0002.json'
    out = Path(args.evidence_root) / evidence_relative
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {'produced_by': 'scripts/series_derive.py', 'asset_git_blob_sha1': GIT_BLOB,
         'evidence_location': {'kind': 'image_region', 'xyxy': REGION},
         'derivation': derivation}, ensure_ascii=False, indent=1), encoding='utf-8')

    checks, result, limitations = build_checks(derivation)
    assessment = assess(
        intake.journal,
        subject_id=HYPOTHESIS_SUBJECT['method_id'],
        subject_revision=revision(HYPOTHESIS_SUBJECT),
        dimension='correctness', result=result,
        procedure='exhaustive deterministic search of a declared rule space against every observed pair',
        assessor='scripts/series_derive.py', author='model hypothesis from expert media frame',
        approach='DETERMINISTIC', evidence_root=args.evidence_root,
        evidence_paths=[evidence_relative], checks=checks, limitations=limitations)

    graph = Graph(args.graph_root)
    build_graph(graph, asset, span)

    statuses = {}
    for node_id in ('OBS-MEDIA-0002', CONCEPT['concept_id'], HYPOTHESIS_SUBJECT['method_id'],
                    'OBS-MEDIA-0002-AUDIO', asset['id'], span['id']):
        statuses[node_id] = node_status(graph, intake.journal, node_id, args.evidence_root)
    view = learning_view(graph, intake.journal, HYPOTHESIS_SUBJECT['method_id'],
                         args.evidence_root)

    print(json.dumps({
        'status': 'PARTIAL',
        'asset': {'relative_path': RELATIVE, 'git_blob_sha1': GIT_BLOB,
                  'sha256': asset['payload']['sha256'], 'bytes': asset['payload']['bytes'],
                  'width': width, 'height': height, 'evidence_region_xyxy': REGION},
        'span_id': span['id'],
        'source_candidate': {'id': source_candidate['id'],
                             'tier': source_candidate['payload']['provenance_tier']},
        'model_candidate': {'id': model_candidate['id'],
                            'tier': model_candidate['payload']['provenance_tier']},
        'derivation': {
            'result': derivation['result'],
            'polynomial_fit': derivation['polynomial_fit'],
            'matching_rules': derivation['matching_rules'],
            'unique': derivation['unique'],
            'rules_tested': derivation['search_space']['closed_form_rules_tested']
                            + derivation['search_space']['step_rules_tested'],
            'observed_difference_table': derivation['observed_difference_table'],
        },
        'independent_assessment': {'id': assessment['id'], 'dimension': 'correctness',
                                   'result': assessment['payload']['result']},
        'graph_statuses': statuses,
        'learning_view': view,
        'pyq_links': view['pyq_links'],
        'videos_processed': 0,
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
