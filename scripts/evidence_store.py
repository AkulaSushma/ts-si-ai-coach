"""SPEC-INT-010: immutable attempts and fail-closed eligibility.
Validates evidence structure/integrity, not the truth of arbitrary assessments.
Independent verification must actually occur upstream. Never rewrites legacy JSON.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import uuid
from datetime import datetime, timezone

DIMENSIONS = {'correctness', 'applicability', 'speed', 'recognition', 'retention', 'source_fidelity'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')


def revision(value):
    return digest(canonical(value))


def safe_file(root, relative):
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('Expected a relative evidence path')
    p = root
    for part in rel.parts:
        p = p / part
        if p.is_symlink():
            raise ValueError('Symlink evidence is not allowed')
    if not p.resolve().is_relative_to(root):
        raise ValueError('Evidence escapes root')
    return p


def file_digest(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular non-symlink file')
    before = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('File changed while hashing')
    return h.hexdigest()


class Journal:
    """Atomic exclusive-create records on a trusted local filesystem.
    Interrupted staging files remain auditable. Not hostile-tamper-proof storage.
    """
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, kind, payload):
        if kind not in {'assessment', 'asset', 'occurrence', 'attempt', 'span', 'candidate'}:
            raise ValueError('Unknown record kind')
        record = {'id': uuid.uuid4().hex, 'kind': kind, 'schema_version': 1,
                  'recorded_at': datetime.now(timezone.utc).isoformat(), 'payload': payload}
        envelope = canonical({'record': record, 'sha256': digest(canonical(record))})
        path = self.root / (record['id'] + '.json')
        staging = path.with_suffix('.pending')
        with staging.open('xb') as f:
            f.write(envelope)
            f.flush()
            os.fsync(f.fileno())
        # Atomic, refuses replacement. Retain staging bytes; only JSON is committed.
        os.link(staging, path)
        return record

    def records(self, kind=None):
        found = []
        for p in sorted(self.root.iterdir()):
            if p.suffix != '.json':
                continue
            if p.is_symlink():
                raise ValueError('Symlink journal record')
            item = json.loads(p.read_bytes())
            record = item['record']
            if p.stem != record['id'] or digest(canonical(record)) != item['sha256']:
                raise ValueError('Corrupt journal record')
            if kind is None or record['kind'] == kind:
                found.append(record)
        return found


def assess(journal, *, subject_id, subject_revision, dimension, result,
           procedure, assessor, author, approach, evidence_root, evidence_paths,
           checks, limitations):
    """Persist actual upstream results, including FAIL/INCONCLUSIVE; not promotion."""
    if dimension not in DIMENSIONS or result not in {'PASS', 'FAIL', 'INCONCLUSIVE'}:
        raise ValueError('Invalid assessment dimension/result')
    evidence = [{'path': p, 'sha256': file_digest(safe_file(evidence_root, p))}
                for p in evidence_paths]
    return journal.append('assessment', dict(subject_id=subject_id,
        subject_revision=subject_revision, dimension=dimension, result=result,
        procedure=procedure, assessor=assessor, author=author, approach=approach,
        evidence=evidence, checks=checks, limitations=limitations))


def eligible(journal, subject_id, subject_revision, required_dimensions, evidence_root):
    """Consider every attempt on the exact revision; contradictory attempts block.
    This is structural eligibility only, not an independent verifier or publisher.
    For this bounded build correctness means mathematical correctness and requires
    deterministic checks. Different evaluator names alone do not prove independence.
    """
    try:
        if not required_dimensions or not set(required_dimensions) <= DIMENSIONS:
            return False
        if not subject_id or len(subject_revision) != 64 or any(c not in '0123456789abcdef' for c in subject_revision):
            return False
        attempts = [r['payload'] for r in journal.records('assessment')
                    if r['payload']['subject_id'] == subject_id and r['payload']['subject_revision'] == subject_revision]
        for dimension in required_dimensions:
            matches = [a for a in attempts if a['dimension'] == dimension]
            if not matches:
                return False
            for a in matches:
                if a['result'] != 'PASS' or a['limitations'] != []:
                    return False
                if not all(isinstance(a[k], str) and a[k].strip() for k in ('procedure', 'assessor', 'author')):
                    return False
                if a['approach'] not in {'DETERMINISTIC', 'INDEPENDENT_MODEL', 'SOURCE_DOCUMENT'}:
                    return False
                if a['approach'] == 'INDEPENDENT_MODEL' and a['assessor'].casefold() == a['author'].casefold():
                    return False
                if dimension == 'correctness' and a['approach'] != 'DETERMINISTIC':
                    return False
                if not a['evidence']:
                    return False
                for ref in a['evidence']:
                    if file_digest(safe_file(evidence_root, ref['path'])) != ref['sha256']:
                        return False
                checks = a['checks']
                if not isinstance(checks, list) or not checks:
                    return False
                for check in checks:
                    if check['passed'] is not True or not check['procedure'] or 'observed' not in check or 'expected' not in check:
                        return False
                    if check['observed'] is None or check['expected'] is None:
                        return False
                    if canonical(check['observed']) != canonical(check['expected']):
                        return False
                if dimension == 'correctness':
                    if sum(c.get('kind') == 'valid_case' for c in checks) < 2 or not any(c.get('kind') == 'boundary_case' for c in checks):
                        return False
        return True
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def fast_method_state(journal, subject_id, subject_revision, evidence_root):
    """Conservative fast-method projection; callers cannot omit required dimensions.
    Legacy stored VERIFIED labels are intentionally not an input.
    """
    if eligible(journal, subject_id, subject_revision,
                ('correctness', 'applicability', 'speed'), evidence_root):
        return 'VERIFIED_FAST_METHOD'
    return 'UNVERIFIED_FAST_METHOD'
