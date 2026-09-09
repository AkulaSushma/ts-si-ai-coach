"""SPEC-INT-012: append-only exam-solving knowledge graph with fail-closed status.

Design constraints (deliberate):
- Nodes and edges are append-only records; nothing is rewritten in place.
- Every node carries an explicit origin. Model output can never enter as source text.
- Status is DERIVED from evidence at read time. It is never stored as a label,
  so no code path can "promote" a node by writing a string.
- Any FAIL or BLOCKED attempt on the current revision dominates. Fail closed.
- Edges that assert an exam relationship (solves / applies_to_pyq) require
  located evidence and a known PYQ identifier. Unsupported links are refused.

This module validates structure and evidence integrity. It does not decide
mathematical truth; that must be established upstream by an actual procedure.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from evidence_store import (
    DIMENSIONS,
    canonical,
    digest,
    eligible,
    file_digest,
    revision,
    safe_file,
)

STATUSES = (
    'VERIFIED',
    'SUPPORTED',
    'CANDIDATE',
    'UNVERIFIED',
    'FAILED',
    'INCOMPLETE',
    'BLOCKED',
)

ORIGINS = {
    'SOURCE_DERIVED',        # exact content observed in a real asset
    'MODEL_DERIVED',         # interpretation produced by a model
    'INDEPENDENTLY_DERIVED', # produced by a deterministic procedure
    'OFFICIAL_DOCUMENT',     # official notification / paper
}

NODE_KINDS = {
    'asset',
    'evidence_span',
    'observation',
    'recognition_pattern',
    'concept',
    'method',
    'fast_method',
    'pyq_question',
    'confusion',
    'visual_structure',
    'retention_cue',
    'subject_topic',
}

EDGE_KINDS = {
    'derived_from',    # any node -> asset/evidence_span it came from
    'locates',         # evidence_span -> asset region/interval
    'recognizes',      # recognition_pattern -> question family/concept
    'uses_concept',    # method -> concept
    'fast_variant_of', # fast_method -> method
    'solves',          # method/fast_method -> pyq_question
    'applies_to_pyq',  # recognition_pattern/concept -> pyq_question
    'contradicts',     # node -> node
    'explains',        # visual_structure -> concept
    'retains',         # retention_cue -> concept
    'prerequisite_of', # concept -> concept
    'related_to',      # symmetric weak association
}

# Edges that assert an examination relationship and therefore require evidence.
EVIDENCE_REQUIRED_EDGES = {'solves', 'applies_to_pyq', 'recognizes', 'contradicts'}

# Dimensions each node kind must satisfy before it can ever read as VERIFIED.
REQUIRED_DIMENSIONS = {
    'fast_method': ('correctness', 'applicability', 'speed'),
    'method': ('correctness', 'applicability'),
    'recognition_pattern': ('recognition',),
    'retention_cue': ('retention',),
    'visual_structure': ('source_fidelity',),
    'concept': ('correctness',),
    'observation': ('source_fidelity',),
}


class Graph:
    """Append-only node/edge log. One writer, trusted local filesystem."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- writing
    def _append(self, kind, payload):
        record = {
            'id': uuid.uuid4().hex,
            'kind': kind,
            'schema_version': 1,
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'payload': payload,
        }
        envelope = canonical({'record': record, 'sha256': digest(canonical(record))})
        path = self.root / (record['id'] + '.json')
        staging = path.with_suffix('.pending')
        with staging.open('xb') as f:
            f.write(envelope)
            f.flush()
            os.fsync(f.fileno())
        os.link(staging, path)
        return record

    def add_node(self, *, node_id, node_kind, origin, subject, language=None,
                 text=None, text_te=None, uncertainty=None, blocked_reason=None):
        if node_kind not in NODE_KINDS:
            raise ValueError('Unknown node kind')
        if origin not in ORIGINS:
            raise ValueError('Unknown origin')
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError('node_id required')
        if self.node(node_id) is not None:
            raise ValueError('Node already exists; graph is append-only')
        if not isinstance(subject, dict) or not subject:
            raise ValueError('subject payload required')
        payload = dict(
            node_id=node_id,
            node_kind=node_kind,
            origin=origin,
            subject=subject,
            subject_revision=revision(subject),
            language=language,
            text=text,
            text_te=text_te,
            uncertainty=uncertainty,
            blocked_reason=blocked_reason,
        )
        return self._append('node', payload)

    def add_edge(self, *, edge_kind, source_id, target_id, evidence_root=None,
                 evidence_paths=(), known_pyq_ids=(), justification=None):
        if edge_kind not in EDGE_KINDS:
            raise ValueError('Unknown edge kind')
        src = self.node(source_id)
        dst = self.node(target_id)
        if src is None or dst is None:
            raise ValueError('Edges require existing nodes')
        if source_id == target_id:
            raise ValueError('Self edges are not meaningful here')
        if self.edge(edge_kind, source_id, target_id) is not None:
            raise ValueError('Edge already exists; graph is append-only')
        if dst['node_kind'] == 'pyq_question' and dst['subject'].get('pyq_id') not in set(known_pyq_ids):
            # Never fabricate a PYQ relationship against an unknown question id.
            raise ValueError('Unknown PYQ identifier for an exam relationship')
        evidence = []
        if edge_kind in EVIDENCE_REQUIRED_EDGES:
            if not evidence_paths or evidence_root is None:
                raise ValueError('This edge kind requires located evidence')
            if not isinstance(justification, str) or not justification.strip():
                raise ValueError('This edge kind requires a written justification')
            evidence = [
                {'path': p, 'sha256': file_digest(safe_file(evidence_root, p))}
                for p in evidence_paths
            ]
        return self._append('edge', dict(
            edge_kind=edge_kind,
            source_id=source_id,
            target_id=target_id,
            evidence=evidence,
            justification=justification,
        ))

    # ---------------------------------------------------------------- reading
    def records(self, kind=None):
        found = []
        for p in sorted(self.root.iterdir()):
            if p.suffix != '.json':
                continue
            if p.is_symlink():
                raise ValueError('Symlink graph record')
            item = json.loads(p.read_bytes())
            record = item['record']
            if p.stem != record['id'] or digest(canonical(record)) != item['sha256']:
                raise ValueError('Corrupt graph record')
            if kind is None or record['kind'] == kind:
                found.append(record)
        found.sort(key=lambda r: (r['recorded_at'], r['id']))
        return found

    def nodes(self):
        return [r['payload'] for r in self.records('node')]

    def edges(self):
        return [r['payload'] for r in self.records('edge')]

    def node(self, node_id):
        for payload in self.nodes():
            if payload['node_id'] == node_id:
                return payload
        return None

    def edge(self, edge_kind, source_id, target_id):
        for payload in self.edges():
            if (payload['edge_kind'], payload['source_id'], payload['target_id']) == (edge_kind, source_id, target_id):
                return payload
        return None

    def provenance(self, node_id):
        """Assets/spans this node is transitively derived from."""
        seen, order, frontier = {node_id}, [], [node_id]
        while frontier:
            current = frontier.pop(0)
            for e in self.edges():
                if e['edge_kind'] in ('derived_from', 'locates') and e['source_id'] == current:
                    if e['target_id'] not in seen:
                        seen.add(e['target_id'])
                        order.append(e['target_id'])
                        frontier.append(e['target_id'])
        return order


def attempts_for(journal, node):
    return [
        r['payload'] for r in journal.records('assessment')
        if r['payload']['subject_id'] == node['node_id']
        and r['payload']['subject_revision'] == node['subject_revision']
    ]


def node_status(graph, journal, node_id, evidence_root):
    """Derive status from evidence. Never reads a stored status label.

    Precedence is intentionally pessimistic:
    BLOCKED > FAILED > INCOMPLETE > VERIFIED > SUPPORTED > CANDIDATE > UNVERIFIED
    """
    node = graph.node(node_id)
    if node is None:
        return 'INCOMPLETE'
    if node.get('blocked_reason'):
        return 'BLOCKED'

    try:
        attempts = attempts_for(journal, node)
    except (OSError, ValueError, KeyError, TypeError):
        return 'BLOCKED'

    if any(a['result'] == 'FAIL' for a in attempts):
        return 'FAILED'

    required = REQUIRED_DIMENSIONS.get(node['node_kind'])
    if node['node_kind'] in ('asset', 'evidence_span'):
        # Identity-only nodes: complete when they carry located identity.
        return 'SUPPORTED' if node['subject'].get('sha256') or node['subject'].get('location') else 'INCOMPLETE'

    if required is None:
        return 'CANDIDATE' if node['origin'] != 'OFFICIAL_DOCUMENT' else 'SUPPORTED'

    if not set(required) <= DIMENSIONS:
        return 'INCOMPLETE'

    if eligible(journal, node['node_id'], node['subject_revision'], required, evidence_root):
        return 'VERIFIED'

    if any(a['result'] == 'INCONCLUSIVE' for a in attempts):
        return 'UNVERIFIED'

    if node['origin'] == 'OFFICIAL_DOCUMENT':
        return 'SUPPORTED'
    if node['origin'] == 'SOURCE_DERIVED' and graph.provenance(node['node_id']):
        # An expert teaching claim with located evidence is supported, not proven.
        return 'SUPPORTED'
    if node['origin'] in ('MODEL_DERIVED', 'INDEPENDENTLY_DERIVED'):
        return 'CANDIDATE'
    return 'UNVERIFIED'


def learning_view(graph, journal, node_id, evidence_root):
    """Read-only projection for a future learning layer.

    Returns status plus the evidence trail. Callers must render the status;
    there is deliberately no field that says a claim is reliable.
    """
    node = graph.node(node_id)
    if node is None:
        raise ValueError('Unknown node')
    return {
        'node_id': node_id,
        'node_kind': node['node_kind'],
        'origin': node['origin'],
        'status': node_status(graph, journal, node_id, evidence_root),
        'subject_revision': node['subject_revision'],
        'required_dimensions': list(REQUIRED_DIMENSIONS.get(node['node_kind'], ())),
        'provenance': graph.provenance(node_id),
        'uncertainty': node.get('uncertainty'),
        'pyq_links': sorted(
            e['target_id'] for e in graph.edges()
            if e['source_id'] == node_id and e['edge_kind'] in ('solves', 'applies_to_pyq')
        ),
        'attempts': [
            {'dimension': a['dimension'], 'result': a['result'], 'approach': a['approach']}
            for a in attempts_for(journal, node)
        ],
    }
