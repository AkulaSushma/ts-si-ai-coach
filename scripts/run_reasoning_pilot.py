"""Bounded real-media reasoning pilot (SPEC-INT-011).

Processes ONE real committed image from the expert media collection end to end:

  identity (Git blob) -> ffprobe metadata -> located evidence span ->
  source-derived candidate -> model-derived interpretation ->
  independent deterministic correctness assessment -> fail-closed fast state

The visible text recorded here was read from the actual decoded image. Nothing
about the publisher, account, upload date, spoken audio or PYQ relationship is
asserted, because none of that was observed. The independent correctness check
is recomputed by scripts/reasoning_verify.py, not taken from the image.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_store import assess, eligible, fast_method_state, revision  # noqa: E402
import reasoning_verify  # noqa: E402
from video_intake import VideoIntake  # noqa: E402

RELATIVE = 'Screenshot_2026-09-01-19-57-10-82_1c337646f29875672b5a61192b9010f9.jpg'
GIT_BLOB = '5b4835709335954246a0bf603da4b7eb4b3c394b'
COLLECTION = 'SI-Constable-media-b8facd4'

# Transcribed by reading the actual decoded image. Layout order preserved.
OBSERVED_TEXT = (
    'Reasoning Trick\n'
    '86 : 288 :: 36 : ? 108\n'
    '(a) 95\n'
    '(b) 108\n'
    '(c) 172\n'
    '(d) 102\n'
    '8x6=48\n'
    '48x6 = 288\n'
    '3x6=18\n'
    '18x6 = 108'
)

MODEL_INTERPRETATION = (
    'The worked lines suggest the rule: multiply the two digits of the term '
    'together, then multiply that digit product by 6. Recognition cue: a number '
    'analogy of the form AB : X :: CD : ? where X is a multiple of the digit '
    'product. The rule is not uniquely determined by a single shown pair, so it '
    'must be treated as a candidate pattern rather than an established analogy law.'
)

MODEL_UNCERTAINTY = (
    'No speed measurement, recognition-reliability evidence or retention evidence '
    'exists. No PYQ has been linked. The publisher, account and upload date were '
    'not observed. Option (b) being circled in the image is a source statement, '
    'not independent confirmation.'
)

SOURCE_UNCERTAINTY = (
    'Verbatim visible text from one screenshot of a video frame. Handwriting was '
    'read visually without OCR; surrounding spoken explanation was not available.'
)

METHOD = {
    'method_id': 'MET-MEDIA-0001',
    'name': 'Digit-product twice-scaled analogy rule',
    'domain': 'reasoning_number_analogy',
    'rule': 'multiply the digits of the term together, then multiply by 6',
    'provenance_tier': 'T3_EXPERT',
    'origin': 'expert media candidate, independently recomputed',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--state-root', required=True)
    parser.add_argument('--evidence-root', required=True)
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
        {'kind': 'image_region', 'xyxy': [0, 0, width, height],
         'note': 'whole screenshot; the teaching content occupies the central video frame'},
        OBSERVED_TEXT, 'en',
        {'processor': 'Notion AI', 'version': 'session011-visual-1', 'method': 'MODEL_VISUAL',
         'model': 'Notion AI', 'prompt_version': 'read-visible-handwriting-v1'})
    source_candidate = intake.candidate(span, origin='SOURCE_DERIVED', text=OBSERVED_TEXT,
                                        uncertainty=SOURCE_UNCERTAINTY)
    model_candidate = intake.candidate(span, origin='MODEL_DERIVED', text=MODEL_INTERPRETATION,
                                       uncertainty=MODEL_UNCERTAINTY)

    # Independent deterministic recomputation. Nothing here reads the source claim.
    analogy = reasoning_verify.check_analogy([(86, 288), (36, 108)], 6)
    boundary = reasoning_verify.failure_boundary(40, 6)
    alternatives = reasoning_verify.alternative_rule_count((86, 288))
    report = {'rule': METHOD['rule'], 'analogy_checks': analogy,
              'failure_boundary': boundary, 'alternative_rules_for_single_pair': alternatives,
              'produced_by': 'scripts/reasoning_verify.py'}
    evidence_relative = 'session011/reasoning_MET-MEDIA-0001.json'
    reasoning_verify.write_report(Path(args.evidence_root) / evidence_relative, report)

    subject_revision = revision(METHOD)
    prior_failed = [r['payload'] for r in intake.journal.records('assessment')
                    if r['payload']['subject_id'] == METHOD['method_id']
                    and r['payload']['result'] != 'PASS']
    checks = [
        {'kind': 'valid_case', 'procedure': 'recompute 86 -> digit product 48 -> 48*6',
         'observed': analogy[0]['computed_output'], 'expected': 288, 'passed': analogy[0]['matches']},
        {'kind': 'valid_case', 'procedure': 'recompute 36 -> digit product 18 -> 18*6',
         'observed': analogy[1]['computed_output'], 'expected': 108, 'passed': analogy[1]['matches']},
        {'kind': 'boundary_case', 'procedure': 'input with a zero digit degenerates to 0',
         'observed': boundary['degenerate'], 'expected': True, 'passed': boundary['degenerate'] is True},
    ]
    all_passed = all(c['passed'] is True for c in checks)
    assessment = assess(
        intake.journal,
        subject_id=METHOD['method_id'], subject_revision=subject_revision,
        dimension='correctness', result='PASS' if all_passed else 'FAIL',
        procedure='independent recomputation of both analogy pairs and one degenerate boundary case',
        assessor='scripts/reasoning_verify.py', author='expert media candidate extraction',
        approach='DETERMINISTIC', evidence_root=args.evidence_root,
        evidence_paths=[evidence_relative], checks=checks, limitations=[])

    correctness_ok = eligible(intake.journal, METHOD['method_id'], subject_revision,
                              ('correctness',), args.evidence_root)
    state = fast_method_state(intake.journal, METHOD['method_id'], subject_revision,
                              args.evidence_root)

    print(json.dumps({
        'status': 'PARTIAL',
        'asset': {'relative_path': RELATIVE, 'git_blob_sha1': GIT_BLOB,
                  'sha256': asset['payload']['sha256'], 'bytes': asset['payload']['bytes'],
                  'width': width, 'height': height},
        'span_id': span['id'],
        'source_candidate': {'id': source_candidate['id'],
                             'tier': source_candidate['payload']['provenance_tier'],
                             'verification_status': source_candidate['payload']['verification_status']},
        'model_candidate': {'id': model_candidate['id'],
                            'tier': model_candidate['payload']['provenance_tier'],
                            'verification_status': model_candidate['payload']['verification_status']},
        'independent_assessment': {'id': assessment['id'],
                                   'dimension': 'correctness',
                                   'result': assessment['payload']['result'],
                                   'approach': 'DETERMINISTIC'},
        'correctness_eligible': correctness_ok,
        'retained_failed_assessments_for_earlier_rule_statements': len(prior_failed),
        'fast_method_state': state,
        'alternative_rules_matching_single_pair': len(alternatives),
        'unverified_dimensions': ['applicability', 'speed', 'recognition', 'retention'],
        'pyq_links': [],
        'videos_processed': 0,
        'note': 'Mathematical correctness of the recomputed rule is independently supported. '
                'Speed, applicability, recognition and retention remain unverified, so the '
                'method is deliberately NOT a verified fast method.',
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
