"""SPEC-INT-014 local orchestrator: Phases 1-9 of the real-video pilot.

This script is meant to be run inside the real local checkout (for example
D:\\Projects\\ts-si-ai-coach) where the actual media binaries exist. It performs,
in order, and records exactly what happened at each step:

  Phase 1  git ground truth + Session 013 file presence + asset identity
  Phase 2  media capability probe (ffmpeg, ffprobe, tesseract langs, ASR backend)
  Phase 3  the real bounded video pilot via scripts/run_video_pilot.py
  Phase 8  full unittest suite and the bootstrap validator
  Phase 9  second pilot run (resumability) and a tamper-refusal check on a COPY

It never modifies the original media: the tamper check copies the asset into a
temporary source root and mutates the copy. It never asserts a concept, method,
shortcut, translation or PYQ relationship; those layers stay evidence-gated.

Output: <work>/session014-orchestrator.json and <work>/session014-report.md,
both containing only observed values, with BLOCKED recorded where a capability
is genuinely missing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from video_intake import git_blob_sha1  # noqa: E402
from video_pipeline import VideoPipeline, stage_summary  # noqa: E402
from asr_whisper import (BACKENDS, WhisperAsrAdapter, capability_snapshot,  # noqa: E402
                         local_registry)

VIDEO_RELATIVE = 'SI & Constable Concepts Videos & photos/Dynasties & Founders (Tricks).mp4'
EXPECTED_BLOB = '5766d6575b6a54ab477d188558223f319b72f8dd'
EXPECTED_SIZE = 2347758
COLLECTION = 'SI-Constable-media-25e49e9'
SESSION_013_FILES = ('scripts/video_pipeline.py', 'scripts/run_video_pilot.py',
                     'tests/test_session013_video_pipeline.py',
                     'specs/features/session013-video-intelligence.md',
                     'docs/reports/2026-09-09-session013-video-intelligence.md')


def run_cmd(args, cwd=None, timeout=3600):
    """Run a command and record it verbatim. Never raises on failure."""
    started = time.time()
    try:
        proc = subprocess.run(list(args), cwd=None if cwd is None else str(cwd),
                              capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        return {'command': list(args), 'available': False, 'returncode': None,
                'stdout': '', 'stderr': str(exc), 'seconds': 0.0}
    except subprocess.TimeoutExpired as exc:
        return {'command': list(args), 'available': True, 'returncode': None,
                'stdout': exc.stdout or '', 'stderr': 'TIMEOUT',
                'seconds': round(time.time() - started, 2)}
    return {'command': list(args), 'available': True, 'returncode': proc.returncode,
            'stdout': proc.stdout, 'stderr': proc.stderr,
            'seconds': round(time.time() - started, 2)}


def sha256_file(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(chunk), b''):
            digest.update(block)
    return digest.hexdigest()


def git_ground_truth(repo):
    return {
        'status_short': run_cmd(['git', 'status', '--short'], cwd=repo),
        'head': run_cmd(['git', 'rev-parse', 'HEAD'], cwd=repo),
        'log': run_cmd(['git', 'log', '--oneline', '-10'], cwd=repo),
        'branch': run_cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo),
    }


def session013_presence(repo):
    present = {}
    for relative in SESSION_013_FILES:
        target = Path(repo) / relative
        present[relative] = {'exists': target.is_file(),
                             'size': target.stat().st_size if target.is_file() else None}
    return present


def asset_identity(repo, relative=VIDEO_RELATIVE, expected_blob=EXPECTED_BLOB,
                   expected_size=EXPECTED_SIZE):
    target = Path(repo) / relative
    if not target.is_file():
        return {'relative_path': relative, 'exists': False, 'status': 'BLOCKED',
                'reason': 'Asset not found in the local checkout'}
    size = target.stat().st_size
    blob = git_blob_sha1(target)
    return {'relative_path': relative, 'exists': True, 'size_bytes': size,
            'expected_size_bytes': expected_size, 'size_matches': size == expected_size,
            'sha256': sha256_file(target), 'git_blob_sha1': blob,
            'expected_git_blob_sha1': expected_blob,
            'identity_matches': blob == expected_blob,
            'status': 'PASS' if blob == expected_blob else 'FAILED'}


def media_capabilities():
    """Probe the environment. Presence of a command is not proof of capability."""
    report = {}
    for tool in ('ffmpeg', 'ffprobe', 'tesseract'):
        path = shutil.which(tool)
        probe = run_cmd([tool, '-version' if tool != 'tesseract' else '--version'])
        first_line = (probe['stdout'] or probe['stderr'] or '').strip().splitlines()
        report[tool] = {'path': path, 'usable': probe['returncode'] == 0,
                        'version_line': first_line[0] if first_line else None}
    langs = run_cmd(['tesseract', '--list-langs'])
    available = []
    if langs['returncode'] == 0:
        for line in (langs['stdout'] or '').splitlines()[1:]:
            value = line.strip()
            if value:
                available.append(value)
    report['tesseract_languages'] = available
    report['ocr_telugu'] = 'tel' in available
    report['ocr_english'] = 'eng' in available
    adapter = WhisperAsrAdapter()
    report['asr'] = {'searched_backends': list(BACKENDS), 'backend': adapter.backend,
                     'version': adapter.version, 'model_size': adapter.model_size,
                     'available_te': adapter.available('te'),
                     'available_mixed': adapter.available('mixed')}
    report['asr_telugu_capable'] = bool(adapter.backend) and adapter.available('te')
    report['registry'] = capability_snapshot()
    gaps = []
    if not report['ffmpeg']['usable'] or not report['ffprobe']['usable']:
        gaps.append('ffmpeg/ffprobe missing: decoding and audio extraction will be BLOCKED')
    if not report['tesseract']['usable']:
        gaps.append('tesseract missing: on-screen text stage will be BLOCKED')
    elif not report['ocr_telugu']:
        gaps.append("tesseract 'tel' language data missing: Telugu OCR will be BLOCKED")
    if not report['asr_telugu_capable']:
        gaps.append('no local Whisper-class ASR backend: speech stage will be BLOCKED '
                    '(install with: pip install faster-whisper)')
    report['capability_gaps'] = gaps
    report['status'] = 'PASS' if not gaps else 'BLOCKED'
    return report


def run_pilot(repo, work, out_name, python_exe=None, language_hint='mixed',
              max_frames=12):
    """Phase 3: the real bounded pilot, exactly as specified."""
    python_exe = python_exe or sys.executable
    out_path = Path(work) / out_name
    command = [python_exe, str(Path('scripts') / 'run_video_pilot.py'),
               '--source-root', '.', '--relative', VIDEO_RELATIVE,
               '--git-blob', EXPECTED_BLOB,
               '--state-root', str(Path(work) / 'state'),
               '--artifact-root', str(Path(work) / 'artifacts'),
               '--collection', COLLECTION,
               '--language-hint', language_hint,
               '--max-frames', str(max_frames),
               '--out', str(out_path)]
    result = run_cmd(command, cwd=repo)
    payload = None
    if out_path.is_file():
        try:
            payload = json.loads(out_path.read_text(encoding='utf-8'))
        except ValueError as exc:
            result['parse_error'] = str(exc)
    return {'invocation': result, 'out_path': str(out_path), 'report': payload}


def observation_counts(report):
    """Phase 10 counts, derived strictly from the observed pilot report."""
    if not isinstance(report, dict):
        return {'decoded': False, 'asr': False, 'ocr': False, 'real_timestamps': 0,
                'frame_evidence': 0, 'source_observations': 0, 'asr_spans': 0,
                'ocr_spans': 0, 'low_confidence_spans': 0, 'candidate_concepts': 0,
                'candidate_methods': 0, 'candidate_pyq_links': 0,
                'verified_new_knowledge': 0, 'status': 'BLOCKED'}
    stages = report.get('stages', {}) or {}
    spans = report.get('spans', []) or []
    return {
        'decoded': stages.get('probe') == 'PASS',
        'asr': stages.get('asr') == 'PASS',
        'ocr': stages.get('ocr') == 'PASS',
        'real_timestamps': len(report.get('sampled_timestamps', []) or []),
        'frame_evidence': len(report.get('frames', []) or []),
        'source_observations': len(spans),
        'asr_spans': len([s for s in spans if s.get('method') == 'ASR']),
        'ocr_spans': len([s for s in spans if s.get('method') == 'OCR']),
        'low_confidence_spans': len([s for s in spans if s.get('low_confidence')]),
        # This pipeline layer asserts no interpretation, so these are always 0
        # here. They can only be created by a later evidence-gated step.
        'candidate_concepts': 0,
        'candidate_methods': 0,
        'candidate_pyq_links': 0,
        'verified_new_knowledge': 0,
        'status': report.get('status', 'BLOCKED'),
    }


def resumability(first, second):
    """Phase 9: compare two pilot reports of the same unchanged asset."""
    if not isinstance(first, dict) or not isinstance(second, dict):
        return {'status': 'BLOCKED', 'reason': 'A pilot report is missing'}
    first_asset = (first.get('asset') or {}).get('sha256')
    second_asset = (second.get('asset') or {}).get('sha256')
    reused = second.get('reused_stages') or {}
    checks = {
        'asset_hash_identical': bool(first_asset) and first_asset == second_asset,
        'stage_results_identical': first.get('stages') == second.get('stages'),
        'span_count_identical': first.get('span_count') == second.get('span_count'),
        'frame_count_identical': len(first.get('frames', []) or []) ==
                                 len(second.get('frames', []) or []),
        'blocked_stages_still_recorded':
            sorted(k for k, v in (first.get('stages') or {}).items() if v == 'BLOCKED') ==
            sorted(k for k, v in (second.get('stages') or {}).items() if v == 'BLOCKED'),
    }
    return {'status': 'PASS' if all(checks.values()) else 'FAILED',
            'checks': checks, 'reused_stages_reported': reused}


def tamper_refusal(repo, work):
    """Phase 9: prove tampering is refused, using a COPY of the real asset.

    The original file is only read. The copy lives in a temporary directory and
    is deleted afterwards.
    """
    source = Path(repo) / VIDEO_RELATIVE
    if not source.is_file():
        return {'status': 'BLOCKED', 'reason': 'Asset not present locally'}
    original_sha = sha256_file(source)
    with tempfile.TemporaryDirectory(dir=str(work)) as tmp:
        root = Path(tmp)
        copy_root = root / 'source'
        copy_root.mkdir()
        copy = copy_root / 'asset.mp4'
        shutil.copyfile(source, copy)
        pipeline = VideoPipeline(copy_root, root / 'state', root / 'artifacts',
                                 registry=local_registry())
        blob = git_blob_sha1(copy)
        outcome = {'copy_blob_matches_original': blob == original_blob_of(source)}
        try:
            pipeline.run('asset.mp4', COLLECTION + '-tamper-check', blob, max_frames=2)
            outcome['first_run'] = 'completed'
        except Exception as exc:  # recorded, not hidden
            outcome['first_run'] = 'error: ' + str(exc)
        with open(copy, 'ab') as handle:
            handle.write(b'tamper')
        try:
            pipeline.run('asset.mp4', COLLECTION + '-tamper-check', blob, max_frames=2)
            outcome['refused_after_tamper'] = False
        except ValueError as exc:
            outcome['refused_after_tamper'] = True
            outcome['refusal_message'] = str(exc)
    outcome['original_unchanged'] = sha256_file(source) == original_sha
    outcome['status'] = 'PASS' if outcome.get('refused_after_tamper') and \
        outcome['original_unchanged'] else 'FAILED'
    return outcome


def original_blob_of(path):
    return git_blob_sha1(path)


def build_markdown(payload):
    """Render the observed results. Values are copied, never inferred."""
    counts = payload['real_video_results']
    lines = ['# Session 014 - real video pilot (observed run)', '',
             'Generated by scripts/run_session014_local.py on the local checkout.',
             'Every value below was observed in this run.', '',
             '## Ground truth', '',
             '- HEAD: ' + (payload['git']['head']['stdout'] or '').strip(),
             '- branch: ' + (payload['git']['branch']['stdout'] or '').strip(),
             '- working tree clean: ' +
             str(not (payload['git']['status_short']['stdout'] or '').strip()),
             '- Session 013 files present: ' +
             str(all(v['exists'] for v in payload['session013_files'].values())),
             '', '## Asset identity', '']
    for key in ('relative_path', 'size_bytes', 'sha256', 'git_blob_sha1',
                'identity_matches', 'status'):
        if key in payload['asset']:
            lines.append('- {}: {}'.format(key, payload['asset'][key]))
    lines += ['', '## Capabilities', '']
    caps = payload['capabilities']
    for tool in ('ffmpeg', 'ffprobe', 'tesseract'):
        entry = caps[tool]
        lines.append('- {}: usable={} path={} version={}'.format(
            tool, entry['usable'], entry['path'], entry['version_line']))
    lines += ['- tesseract languages: ' + (', '.join(caps['tesseract_languages']) or 'none'),
              '- ASR backend: ' + str(caps['asr']['backend']) +
              ' (' + caps['asr']['version'] + ')',
              '- Telugu ASR capable: ' + str(caps['asr_telugu_capable'])]
    for gap in caps['capability_gaps']:
        lines.append('- GAP: ' + gap)
    lines += ['', '## REAL VIDEO RESULTS', '',
              '- decoded: ' + ('YES' if counts['decoded'] else 'NO'),
              '- ASR: ' + ('YES' if counts['asr'] else 'NO'),
              '- OCR: ' + ('YES' if counts['ocr'] else 'NO'),
              '- real timestamps: {}'.format(counts['real_timestamps']),
              '- real frame evidence: {}'.format(counts['frame_evidence']),
              '- source observations (located spans): {}'.format(counts['source_observations']),
              '  - ASR spans: {}'.format(counts['asr_spans']),
              '  - OCR spans: {}'.format(counts['ocr_spans']),
              '  - low-confidence spans retained: {}'.format(counts['low_confidence_spans']),
              '- candidate concepts: {}'.format(counts['candidate_concepts']),
              '- candidate methods: {}'.format(counts['candidate_methods']),
              '- candidate PYQ links: {}'.format(counts['candidate_pyq_links']),
              '- VERIFIED new knowledge: {}'.format(counts['verified_new_knowledge']),
              '- pilot status: ' + str(counts['status']),
              '',
              'Interpretation, candidate concepts, candidate methods and PYQ links are',
              'NOT produced by this pipeline layer. They stay 0 until a separate',
              'evidence-gated step reads these located spans.',
              '', '## PIPELINE RESULTS', '',
              '- full unittest suite: ' + payload['tests']['verdict'],
              '- bootstrap validator: ' + payload['validator']['verdict'],
              '- resumability: ' + payload['resumability']['status'],
              '- tamper refusal: ' + payload['tamper_check'].get('status', 'BLOCKED'),
              '- original asset unchanged: ' +
              str(payload['tamper_check'].get('original_unchanged')),
              '', '## BLOCKERS', '']
    if payload['blockers']:
        lines += ['- ' + blocker for blocker in payload['blockers']]
    else:
        lines.append('- none observed in this run')
    lines += ['', '## Session status', '',
              'Session status: ' + payload['session_status'],
              '', 'This session is not COMPLETE while the real video remains BLOCKED or',
              'while extracted intelligence has not been independently verified.', '']
    return '\n'.join(lines)


def summarise_run(command_result, name):
    text = (command_result.get('stdout') or '') + (command_result.get('stderr') or '')
    if command_result.get('available') is False:
        verdict = 'UNAVAILABLE'
    elif command_result.get('returncode') == 0:
        verdict = 'PASSED'
    elif command_result.get('returncode') is None:
        verdict = 'UNAVAILABLE'
    else:
        verdict = 'FAILED'
    tail = text.strip().splitlines()[-12:]
    return {'name': name, 'verdict': verdict,
            'returncode': command_result.get('returncode'),
            'tail': tail, 'command': command_result.get('command')}


def collect_blockers(payload):
    blockers = []
    asset = payload['asset']
    if not asset.get('exists'):
        blockers.append('Real video not present at the expected path in this checkout')
    elif not asset.get('identity_matches'):
        blockers.append('Local bytes do not match the committed Git blob SHA-1')
    blockers.extend(payload['capabilities']['capability_gaps'])
    counts = payload['real_video_results']
    if not counts['decoded']:
        blockers.append('Video decoding did not succeed; no metadata was observed')
    if not counts['asr']:
        blockers.append('Speech recognition did not succeed; no transcript evidence exists')
    if not counts['ocr']:
        blockers.append('On-screen text recognition did not succeed')
    if payload['tests']['verdict'] != 'PASSED':
        blockers.append('Full test suite did not pass in this environment')
    blockers.append('Speed, recognition and retention still have no evidence procedure')
    return blockers


def build_parser():
    parser = argparse.ArgumentParser(description='Session 014 local orchestrator')
    parser.add_argument('--repo', default='.', help='Local checkout root')
    parser.add_argument('--work', default='../si-pilot',
                        help='Working directory for state, artifacts and reports')
    parser.add_argument('--python', default=None, help='Python executable to use')
    parser.add_argument('--language-hint', default='mixed',
                        choices=['te', 'en', 'mixed', 'und'])
    parser.add_argument('--max-frames', type=int, default=12)
    parser.add_argument('--skip-tests', action='store_true')
    parser.add_argument('--skip-tamper-check', action='store_true')
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    repo = Path(args.repo).resolve()
    work = Path(args.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    python_exe = args.python or sys.executable

    payload = {'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
               'repo': str(repo), 'work': str(work),
               'git': git_ground_truth(repo),
               'session013_files': session013_presence(repo),
               'asset': asset_identity(repo),
               'capabilities': media_capabilities()}

    first = run_pilot(repo, work, 'video-pilot.json', python_exe,
                      args.language_hint, args.max_frames)
    second = run_pilot(repo, work, 'video-pilot-rerun.json', python_exe,
                       args.language_hint, args.max_frames)
    payload['pilot_first'] = first
    payload['pilot_second'] = second
    payload['real_video_results'] = observation_counts(first.get('report'))
    payload['stage_status'] = (first.get('report') or {}).get('stage_status') or {}
    payload['resumability'] = resumability(first.get('report'), second.get('report'))

    if args.skip_tests:
        payload['tests'] = {'name': 'unittest', 'verdict': 'UNAVAILABLE',
                            'tail': ['skipped by --skip-tests'], 'returncode': None}
        payload['validator'] = {'name': 'validate_bootstrap', 'verdict': 'UNAVAILABLE',
                                'tail': ['skipped by --skip-tests'], 'returncode': None}
    else:
        payload['tests'] = summarise_run(
            run_cmd([python_exe, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                    cwd=repo), 'unittest')
        validator = repo / 'scripts' / 'validate_bootstrap.py'
        if validator.is_file():
            payload['validator'] = summarise_run(
                run_cmd([python_exe, str(Path('scripts') / 'validate_bootstrap.py')],
                        cwd=repo), 'validate_bootstrap')
        else:
            payload['validator'] = {'name': 'validate_bootstrap', 'verdict': 'UNAVAILABLE',
                                    'tail': ['validator not present'], 'returncode': None}

    if args.skip_tamper_check:
        payload['tamper_check'] = {'status': 'BLOCKED', 'reason': 'skipped by flag'}
    else:
        payload['tamper_check'] = tamper_refusal(repo, work)

    payload['blockers'] = collect_blockers(payload)
    counts = payload['real_video_results']
    fully_observed = counts['decoded'] and counts['asr'] and counts['ocr']
    payload['session_status'] = 'PARTIAL' if fully_observed else 'BLOCKED'

    json_path = work / 'session014-orchestrator.json'
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding='utf-8')
    md_path = work / 'session014-report.md'
    md_path.write_text(build_markdown(payload), encoding='utf-8')
    print(build_markdown(payload))
    print('\nJSON: ' + str(json_path))
    print('Markdown: ' + str(md_path))
    return 0 if payload['session_status'] == 'PARTIAL' else 1


if __name__ == '__main__':
    raise SystemExit(main())
