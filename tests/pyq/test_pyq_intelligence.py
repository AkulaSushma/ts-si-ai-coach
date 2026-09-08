"""Session-009 question-intelligence verification (SPEC-PYQ-002).

These tests protect one property above all others: **no classification, fast method,
or verification exists in this repository unless it is honestly labelled.** A model's
reading of a previous-year question is `MODEL_DERIVED` analysis of `T2_HISTORICAL_PYQ`
evidence and is never promoted to sourced or verified without the matching evidence.
A question that cannot be confidently classified stays `unresolved` — it is never
guessed. A fast method becomes `VERIFIED_FAST_METHOD` only behind a verification
record whose result is `PASS`, produced by deterministic computation or a different
provider — never by the model's own confidence.

Design note. As with SPEC-PYQ-001, the checkers are pure functions over plain data,
not methods that read files: `TestIntelligenceCheckersRejectFabrication` feeds them
deliberately poisoned records to prove they can fail. A checker that only ever sees a
clean corpus proves nothing.

Standard library only (D-0006).
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

QUESTION_DIR = "pyq/questions"
PAPER_DIR = "pyq/papers"
WEIGHTAGE_DIR = "pyq/weightage"
INTEL_DIR = "pyq/intelligence"

FAMILY_BASIS = ("OBSERVED_FROM_CORPUS", "UNOBSERVED_CURRICULUM_CANDIDATE")
Q_TYPES = ("FACTUAL", "APPLICATION", "COMPUTATION", "INFERENCE", "PATTERN", "REASONING", "UNCLASSIFIED")
METHOD_STATES = (
    "OBSERVED_STANDARD", "MODEL_DERIVED", "EXPERT_SOURCED",
    "VERIFIED_FAST_METHOD", "UNVERIFIED_FAST_METHOD", "NO_FAST_METHOD_FOUND",
)
FAST_STATES = ("VERIFIED_FAST_METHOD", "UNVERIFIED_FAST_METHOD", "NO_FAST_METHOD_FOUND", "NOT_SET")
KINDS = ("STANDARD", "FAST", "MENTAL", "ALTERNATIVE")
DERIVED_FROM = ("OBSERVED_STANDARD", "MODEL_ANALYSIS", "EXPERT_SOURCE", "EXISTING_METHOD")
ANALYSIS_ORIGINS = ("OBSERVED_STANDARD", "MODEL_DERIVED", "EXPERT_SOURCED")
CONFIDENCE = ("EXACT", "NEAR", "AMBIGUOUS", "UNKNOWN")
VERIFY_METHODS = ("DETERMINISTIC", "INDEPENDENT_MODEL", "SOURCE_DOCUMENT", "CROSS_SOURCE")
VERIFY_RESULTS = ("PASS", "FAIL", "INCONCLUSIVE")
VERIFY_APPROACHES = ("DETERMINISTIC", "INDEPENDENT_MODEL", "SOURCE_DOCUMENT", "CROSS_SOURCE")
VERIFY_APPROACHES_BACK = ("DETERMINISTIC", "INDEPENDENT_MODEL", "SOURCE_DOCUMENT", "CROSS_SOURCE")
STATUSES = ("BLOCKED", "PARTIAL", "COMPLETE")
COMPLEXITY = ("VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH")
CLUE_KINDS = ("STRUCTURAL", "KEYWORD")
BANNED_EXPERT_HOSTS = ("instagram.com", "youtube.com", "www.instagram.com", "www.youtube.com")

Q_RE = re.compile(r"^Q-PYQ-\d{6}$")
PAPER_RE = re.compile(r"^PAPER-PYQ-\d{4}$")
FAM_RE = re.compile(r"^FAM-PYQ-\d{4}$")
CON_RE = re.compile(r"^CON-PYQ-\d{4}$")
MET_RE = re.compile(r"^MET-PYQ-\d{4}$")
VER_RE = re.compile(r"^VER-PYQ-\d{4}$")
INT_RE = re.compile(r"^INT-PYQ-\d{6}$")
VIS_RE = re.compile(r"^VIS-PYQ-\d{4}$")

# JSON files that may legitimately sit in a content folder with no content.
BOOKKEEPING_FILES = {".gitkeep", "README.md"}


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def json_files(rel: str) -> list[Path]:
    return sorted(p for p in (ROOT / rel).glob("*.json"))


def text(value) -> str:
    return (value or "").strip() if isinstance(value, (str, type(None))) else ""


def host_is_banned(url: str) -> bool:
    """True if the reference names Instagram or YouTube as the expert source."""
    if not url:
        return False
    low = url.lower()
    return any(b in low for b in BANNED_EXPERT_HOSTS)


def question_records() -> list[dict]:
    out = []
    for p in json_files(QUESTION_DIR):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def paper_ids() -> set[str]:
    ids = set()
    for p in json_files(PAPER_DIR):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("paper_id"):
            ids.add(rec["paper_id"])
    return ids


def intel_records() -> dict:
    """All intelligence-layer registers, keyed by their *_id field."""
    base = {}
    for name, key in (
        ("questions.json", "intelligence_id"),
        ("families.json", "family_id"),
        ("concepts.json", "concept_id"),
        ("methods.json", "method_id"),
        ("verifications.json", "verification_id"),
        ("visualizations.json", "visual_id"),
    ):
        base[key] = {}
        p = ROOT / INTEL_DIR / name
        if not p.exists():
            continue
        for rec in json.loads(p.read_text(encoding="utf-8")):
            base[key][rec.get(key)] = rec
    return base


# ---------------------------------------------------------------------------
# Register-level checkers (AC-1, AC-2, AC-9, AC-10)
# ---------------------------------------------------------------------------

def check_intel_register(data: list, key: str, pattern, file_label: str) -> list[str]:
    """Every intelligence record is a dict with a well-formed id, no duplicate id."""
    problems = []
    seen = set()
    for i, rec in enumerate(data):
        if not isinstance(rec, dict):
            problems.append(f"{file_label}[{i}]: not an object")
            continue
        rid = rec.get(key)
        if not isinstance(rid, str) or not pattern.fullmatch(rid):
            problems.append(f"{file_label}[{i}]: bad {key}={rid!r}")
        elif rid in seen:
            problems.append(f"{file_label}: duplicate {rid}")
        seen.add(rid)
    return problems


def check_family_register(families: list[dict]) -> list[str]:
    problems = check_intel_register(families, "family_id", FAM_RE, "families.json")
    seen = set()
    for f in families:
        fid = f.get("family_id")
        if f.get("basis") not in FAMILY_BASIS:
            problems.append(f"{fid}: basis {f.get('basis')!r}")
        if f.get("basis") == "OBSERVED_FROM_CORPUS":
            if not f.get("question_ids"):
                problems.append(f"{fid}: OBSERVED_FROM_CORPUS with no member questions")
        elif f.get("question_ids"):
            problems.append(f"{fid}: candidate family (UNOBSERVED) must have empty members")
        for qid in f.get("question_ids", []):
            if qid in seen:
                problems.append(f"{fid}: question {qid} appears in more than one family")
            seen.add(qid)
    return problems


def check_family_grounded(family: dict, q_by_id: dict) -> list[str]:
    """A family is grounded: every listed member resolves to a real question record."""
    fid = family.get("family_id")
    if family.get("basis") != "OBSERVED_FROM_CORPUS":
        return []
    problems = []
    for qid in family.get("question_ids", []):
        q = q_by_id.get(qid)
        if q is None:
            problems.append(f"{fid}: member {qid} does not resolve to a real question record")
    return problems


def check_concept_register(concepts: list[dict]) -> list[str]:
    return check_intel_register(concepts, "concept_id", CON_RE, "concepts.json")


def check_method_register(methods: list[dict]) -> list[str]:
    return check_intel_register(methods, "method_id", MET_RE, "methods.json")


def check_visual_register(visuals: list[dict]) -> list[str]:
    return check_intel_register(visuals, "visual_id", VIS_RE, "visualizations.json")


def check_verification_register(verifications: list[dict]) -> list[str]:
    return check_intel_register(verifications, "verification_id", VER_RE, "verifications.json")


# ---------------------------------------------------------------------------
# Per-question intelligence checker (AC-2 .. AC-6)
# ---------------------------------------------------------------------------

def check_question_intelligence(rec: dict, q_by_id: dict, paper_ids: set[str],
                                fam_by_id: dict, con_by_id: dict, met_by_id: dict,
                                ver_by_id: dict) -> list[str]:
    iid = rec.get("intelligence_id", "<missing>")
    required = (
        "intelligence_id", "question_id", "paper_id", "source_question_number",
        "source_page_number", "subject", "topic", "subtopic", "question_type",
        "question_family_id", "identification_clues", "required_concept_id",
        "standard_method_id", "candidate_fast_method_id", "fast_method_state",
        "fast_method_verified_id", "common_trap_ids", "confusing_family_ids",
        "how_to_distinguish", "expected_solving_complexity",
        "classification_confidence", "unresolved", "analysis_origin",
        "evidence_tier", "provenance", "verification",
    )
    missing = [k for k in required if k not in rec]
    if missing:
        return [f"{iid}: missing field(s) {', '.join(missing)}"]

    problems = []
    if not INT_RE.fullmatch(str(iid)):
        problems.append(f"{iid}: intelligence_id does not match INT-PYQ-######")
    if rec["evidence_tier"] != "T2_HISTORICAL_PYQ":
        problems.append(f"{iid}: evidence_tier {rec['evidence_tier']!r}, must be T2_HISTORICAL_PYQ")
    if rec["analysis_origin"] not in ANALYSIS_ORIGINS:
        problems.append(f"{iid}: analysis_origin {rec['analysis_origin']!r}")
    if rec["question_type"] not in Q_TYPES:
        problems.append(f"{iid}: question_type {rec['question_type']!r}")
    if rec["fast_method_state"] not in FAST_STATES:
        problems.append(f"{iid}: fast_method_state {rec['fast_method_state']!r}")
    if rec["expected_solving_complexity"] not in COMPLEXITY:
        problems.append(f"{iid}: complexity {rec['expected_solving_complexity']!r}")
    if rec["classification_confidence"] not in CONFIDENCE:
        problems.append(f"{iid}: confidence {rec['classification_confidence']!r}")

    # Question and paper resolution (AC-2).
    qid = rec["question_id"]
    q = q_by_id.get(qid)
    if q is None:
        problems.append(f"{iid}: question_id {qid!r} does not resolve to a real question record")
        return problems
    if rec["paper_id"] != q.get("paper_id"):
        problems.append(f"{iid}: paper_id {rec['paper_id']!r} does not match the question's paper {q.get('paper_id')!r}")
    if rec["paper_id"] not in paper_ids:
        problems.append(f"{iid}: paper_id {rec['paper_id']!r} is not a registered paper")
    if rec["subject"] != q.get("subject"):
        problems.append(f"{iid}: subject differs from the question record")
    if rec["source_question_number"] != q.get("question_number"):
        problems.append(f"{iid}: source_question_number differs from the question record")

    # Unresolved means unresolved: no family, topic, concept, method (AC-5).
    if rec["unresolved"]:
        for field in ("question_family_id", "topic", "required_concept_id", "standard_method_id", "subtopic"):
            if rec[field] is not None:
                problems.append(f"{iid}: unresolved but {field} is set")
        if rec["question_type"] != "UNCLASSIFIED":
            problems.append(f"{iid}: unresolved but question_type is {rec['question_type']!r}")
        return problems

    # Identification must be structural (AC: junk keyword lists are not identification).
    clues = rec["identification_clues"]
    if not clues:
        problems.append(f"{iid}: no identification clues for a classified question")
    for cl in clues:
        if not isinstance(cl, dict) or cl.get("kind") not in CLUE_KINDS:
            problems.append(f"{iid}: clue {cl!r} is not {{clue, kind}}")
    if clues and not any(c.get("kind") == "STRUCTURAL" for c in clues):
        problems.append(f"{iid}: no STRUCTURAL clue — keyword-only identification is not identification")

    # Family / concept / method resolution.
    fid = rec["question_family_id"]
    fam = fam_by_id.get(fid) if fid else None
    if not fid or fam is None:
        problems.append(f"{iid}: question_family_id {fid!r} does not resolve to a real family")
    if rec["required_concept_id"] not in con_by_id:
        problems.append(f"{iid}: required_concept_id {rec['required_concept_id']!r} does not resolve")
    if rec["standard_method_id"] not in met_by_id:
        problems.append(f"{iid}: standard_method_id {rec['standard_method_id']!r} does not resolve")

    # Fast-method state consistency (AC-3, AC-4).
    state, cand, vid = rec["fast_method_state"], rec["candidate_fast_method_id"], rec["fast_method_verified_id"]
    if state in ("VERIFIED_FAST_METHOD", "UNVERIFIED_FAST_METHOD"):
        if cand is None or cand not in met_by_id:
            problems.append(f"{iid}: state {state} but candidate_fast_method_id {cand!r} does not resolve")
        if state == "VERIFIED_FAST_METHOD":
            ver = ver_by_id.get(vid) if vid else None
            if vid is None or ver is None:
                problems.append(f"{iid}: VERIFIED_FAST_METHOD but fast_method_verified_id {vid!r} does not resolve")
            elif ver.get("result") != "PASS":
                problems.append(f"{iid}: VERIFIED_FAST_METHOD but verification {vid} result is {ver.get('result')!r}")
    elif state == "NO_FAST_METHOD_FOUND":
        if cand is not None:
            problems.append(f"{iid}: NO_FAST_METHOD_FOUND but candidate_fast_method_id is set")
    else:
        problems.append(f"{iid}: state {state!r} not allowed on a classified record")

    # EXPERT_SOURCED must name a source that is not Instagram/YouTube (AC-6).
    if rec["analysis_origin"] == "EXPERT_SOURCED":
        ref = (rec.get("provenance") or {}).get("expert_source_ref")
        if not text(ref):
            problems.append(f"{iid}: EXPERT_SOURCED but provenance.expert_source_ref is empty")
        elif host_is_banned(ref):
            problems.append(f"{iid}: EXPERT_SOURCED with a banned source host")
    return problems


def check_intelligence_set(recs: list[dict], q_by_id: dict, paper_ids: set[str],
                           fam_by_id: dict, con_by_id: dict, met_by_id: dict,
                           ver_by_id: dict) -> list[str]:
    problems = []
    for rec in recs:
        problems += check_question_intelligence(rec, q_by_id, paper_ids, fam_by_id, con_by_id, met_by_id, ver_by_id)
    # A classified question maps to a family that lists it as a member (families and
    # questions must agree; a silent drift between the two registers is a relabel).
    family_members = {}
    for fam in fam_by_id.values():
        for qid in fam.get("question_ids", []):
            family_members.setdefault(qid, []).append(fam["family_id"])
    for rec in recs:
        if rec.get("unresolved"):
            continue
        qid = rec["question_id"]
        fid = rec["question_family_id"]
        if qid in family_members and fid not in family_members[qid]:
            problems.append(f"{rec['intelligence_id']}: question {qid} claimed for {fid} but the family lists it under {family_members[qid]}")
    return problems


# ---------------------------------------------------------------------------
# Family checker (AC-9)
# ---------------------------------------------------------------------------

def check_family(rec: dict, q_by_id: dict, met_by_id: dict, con_by_id: dict) -> list[str]:
    fid = rec.get("family_id", "<missing>")
    required = (
        "family_id", "name", "subject", "topic", "subtopic", "question_type",
        "recognition_cues", "required_concept_ids", "standard_method_id",
        "candidate_fast_method_ids", "question_ids", "basis", "common_mistakes",
        "confusing_family_ids", "how_to_distinguish", "expected_complexity",
        "confidence", "analysis_origin", "evidence_tier", "provenance",
        "verification_status",
    )
    missing = [k for k in required if k not in rec]
    if missing:
        return [f"{fid}: missing field(s) {', '.join(missing)}"]

    problems = []
    if rec["evidence_tier"] != "T2_HISTORICAL_PYQ":
        problems.append(f"{fid}: evidence_tier {rec['evidence_tier']!r}, must be T2_HISTORICAL_PYQ")
    if rec["basis"] not in FAMILY_BASIS:
        problems.append(f"{fid}: basis {rec['basis']!r}")
    if rec["question_type"] not in Q_TYPES:
        problems.append(f"{fid}: question_type {rec['question_type']!r}")
    if rec["confidence"] not in CONFIDENCE:
        problems.append(f"{fid}: confidence {rec['confidence']!r}")
    if rec["verification_status"] not in ("VERIFIED", "UNVERIFIED", "DISPUTED", "REJECTED"):
        problems.append(f"{fid}: verification_status {rec['verification_status']!r}")

    if rec["basis"] == "OBSERVED_FROM_CORPUS":
        if not rec["question_ids"]:
            problems.append(f"{fid}: OBSERVED_FROM_CORPUS but question_ids is empty")
        for qid in rec["question_ids"]:
            if qid not in q_by_id:
                problems.append(f"{fid}: member {qid} does not resolve to a real question")
    else:
        if rec["question_ids"]:
            problems.append(f"{fid}: UNOBSERVED_CURRICULUM_CANDIDATE with member questions")

    for cid in rec["required_concept_ids"]:
        if cid not in con_by_id:
            problems.append(f"{fid}: required_concept_id {cid!r} does not resolve")
    if rec["standard_method_id"] is None:
        problems.append(f"{fid}: no standard_method_id")
    elif rec["standard_method_id"] not in met_by_id:
        problems.append(f"{fid}: standard_method_id does not resolve")
    for mid in rec["candidate_fast_method_ids"]:
        if mid not in met_by_id:
            problems.append(f"{fid}: candidate fast method {mid!r} does not resolve")
    for cid in rec["confusing_family_ids"]:
        if cid == fid:
            problems.append(f"{fid}: lists itself as a confusing family")
    return problems


# ---------------------------------------------------------------------------
# Method checker (AC-3, AC-7)
# ---------------------------------------------------------------------------

def check_method(rec: dict, ver_by_id: dict) -> list[str]:
    mid = rec.get("method_id", "<missing>")
    required = (
        "method_id", "name", "kind", "state", "description", "when_usable",
        "when_not_to_use", "family_ids", "concept_ids", "derived_from",
        "time_advantage", "verification_id", "expert_source_ref",
        "analysis_origin", "evidence_tier", "provenance", "verification_status",
    )
    missing = [k for k in required if k not in rec]
    if missing:
        return [f"{mid}: missing field(s) {', '.join(missing)}"]

    problems = []
    if rec["kind"] not in KINDS:
        problems.append(f"{mid}: kind {rec['kind']!r}")
    if rec["state"] not in METHOD_STATES:
        problems.append(f"{mid}: state {rec['state']!r}")
    if rec["derived_from"] not in DERIVED_FROM:
        problems.append(f"{mid}: derived_from {rec['derived_from']!r}")
    if rec["analysis_origin"] not in ANALYSIS_ORIGINS:
        problems.append(f"{mid}: analysis_origin {rec['analysis_origin']!r}")
    if rec["evidence_tier"] != "T2_HISTORICAL_PYQ":
        problems.append(f"{mid}: evidence_tier {rec['evidence_tier']!r}")
    if rec["verification_status"] not in ("VERIFIED", "UNVERIFIED", "DISPUTED", "REJECTED"):
        problems.append(f"{mid}: verification_status {rec['verification_status']!r}")
    if len(text(rec.get("name"))) < 3:
        problems.append(f"{mid}: name too short")

    state = rec["state"]
    # The six states are exclusive; a method is never silently promoted.
    if state == "VERIFIED_FAST_METHOD":
        vid = rec["verification_id"]
        ver = ver_by_id.get(vid) if vid else None
        if vid is None or ver is None:
            problems.append(f"{mid}: VERIFIED_FAST_METHOD but verification_id {vid!r} does not resolve")
        elif ver.get("result") != "PASS":
            problems.append(f"{mid}: VERIFIED_FAST_METHOD but verification result is {ver.get('result')!r}")
    elif state == "UNVERIFIED_FAST_METHOD":
        if rec["verification_id"] is not None:
            problems.append(f"{mid}: UNVERIFIED_FAST_METHOD but verification_id is set")
        if not text(rec["when_not_to_use"]):
            problems.append(f"{mid}: fast method with no when_not_to_use")
    elif state == "EXPERT_SOURCED":
        ref = rec["expert_source_ref"]
        if not text(ref):
            problems.append(f"{mid}: EXPERT_SOURCED but no expert_source_ref")
        elif host_is_banned(ref):
            problems.append(f"{mid}: EXPERT_SOURCED with a banned host")
    if state == "VERIFIED_FAST_METHOD" and rec["verification_status"] != "VERIFIED":
        problems.append(f"{mid}: VERIFIED_FAST_METHOD but verification_status is {rec['verification_status']!r}")
    return problems


# ---------------------------------------------------------------------------
# Verification checker (AC-8)
# ---------------------------------------------------------------------------

def check_verification(rec: dict) -> list[str]:
    vid = rec.get("verification_id", "<missing>")
    required = (
        "verification_id", "method_id", "approach", "procedure",
        "standard_vs_fast_equivalence", "variants_tested", "edge_cases_tested",
        "result", "verified_on", "verified_by", "evidence", "provenance_tier",
        "provenance",
    )
    missing = [k for k in required if k not in rec]
    if missing:
        return [f"{vid}: missing field(s) {', '.join(missing)}"]

    problems = []
    if rec["approach"] not in VERIFY_APPROACHES:
        problems.append(f"{vid}: approach {rec['approach']!r}")
    if rec["result"] not in VERIFY_RESULTS:
        problems.append(f"{vid}: result {rec['result']!r}")
    if rec["provenance_tier"] != "T2_HISTORICAL_PYQ":
        problems.append(f"{vid}: provenance_tier {rec['provenance_tier']!r}")

    eq = rec["standard_vs_fast_equivalence"] or {}
    if rec["result"] == "PASS":
        if not eq.get("fast_matches_standard"):
            problems.append(f"{vid}: PASS but fast_matches_standard is not true")
        if eq.get("mismatches") != 0:
            problems.append(f"{vid}: PASS but mismatches={eq.get('mismatches')!r}")
    if not rec["variants_tested"]:
        problems.append(f"{vid}: no variants_tested — one input is not verification")
    if not rec["edge_cases_tested"]:
        problems.append(f"{vid}: no edge_cases_tested")
    if not text(rec.get("procedure")):
        problems.append(f"{vid}: no procedure")
    if not text(rec.get("evidence")):
        problems.append(f"{vid}: no evidence")
    if not text(rec.get("verified_by")):
        problems.append(f"{vid}: no verified_by")
    if rec["approach"] == "INDEPENDENT_MODEL":
        problems.append(f"{vid}: INDEPENDENT_MODEL — the verifier must differ from the analyser; record which provider verified")
    return problems


# ---------------------------------------------------------------------------
# Frequency checker (AC-10) — over the pyq/weightage registers
# ---------------------------------------------------------------------------

def check_frequency_entry(entry: dict, paper_ids: set[str]) -> list[str]:
    eid = entry.get("entry_id", "<missing>")
    if not re.fullmatch(r"WGT-PYQ-\d{4}", str(eid)):
        return [f"{eid}: entry_id does not match WGT-PYQ-####"]

    problems = []
    if entry.get("basis") != "OBSERVED":
        problems.append(f"{eid}: basis {entry.get('basis')!r} must be OBSERVED")
    if entry.get("provenance_tier") != "T2_HISTORICAL_PYQ":
        problems.append(f"{eid}: provenance_tier {entry.get('provenance_tier')!r}")
    num = entry.get("numerator")
    den = entry.get("denominator")
    if num is not None and (den is None or den <= 0):
        problems.append(f"{eid}: numerator {num} with no positive denominator")
    included = entry.get("papers_included") or []
    if num is not None and not included:
        problems.append(f"{eid}: numerator with no enumerated paper set")
    if included:
        for pid in included:
            if pid not in paper_ids:
                problems.append(f"{eid}: counted paper {pid!r} is not registered")
    if entry.get("status") == "COMPLETE" and (num is None or den is None or not included):
        problems.append(f"{eid}: COMPLETE but not fully enumerated")
    return problems


def check_frequency_entries(entries: list[dict], paper_ids: set[str]) -> list[str]:
    problems = []
    for e in entries:
        problems += check_frequency_entry(e, paper_ids)
    return problems


# ---------------------------------------------------------------------------
# Visual-explanation checker (AC: a spec must specify)
# ---------------------------------------------------------------------------

def check_visual(rec: dict, fam_by_id: dict) -> list[str]:
    vid = rec.get("visual_id", "<missing>")
    if not VIS_RE.fullmatch(str(vid)):
        return [f"{vid}: visual_id does not match VIS-PYQ-####"]

    problems = []
    if not rec.get("must_appear"):
        problems.append(f"{vid}: must_appear is empty — a visual with nothing required is not a spec")
    if not rec.get("step_sequence"):
        problems.append(f"{vid}: no step_sequence")
    if not text(rec.get("metaphor")):
        problems.append(f"{vid}: no metaphor")
    fid = rec.get("family_id")
    if fid not in fam_by_id:
        problems.append(f"{vid}: family_id {fid!r} does not resolve to a family record")
    if rec.get("provenance_tier") != "T2_HISTORICAL_PYQ":
        problems.append(f"{vid}: provenance_tier {rec.get('provenance_tier')!r}")
    if rec.get("analysis_origin") == "EXPERT_SOURCED":
        ref = (rec.get("provenance") or {}).get("expert_source_ref")
        if not text(ref):
            problems.append(f"{vid}: EXPERT_SOURCED with no expert_source_ref")
        elif host_is_banned(ref):
            problems.append(f"{vid}: EXPERT_SOURCED with a banned host")
    return problems


# ---------------------------------------------------------------------------
# Register tests over the real files
# ---------------------------------------------------------------------------

class TestIntelligenceRegistersExist(unittest.TestCase):
    """AC-1 — the six registers exist and every record id is well-formed."""

    def setUp(self):
        self.regs = intel_records()

    def test_six_registers_present(self):
        for name in ("intelligence_id", "family_id", "concept_id", "method_id",
                     "verification_id", "visual_id"):
            p = ROOT / INTEL_DIR / {
                "intelligence_id": "questions.json", "family_id": "families.json",
                "concept_id": "concepts.json", "method_id": "methods.json",
                "verification_id": "verifications.json", "visual_id": "visualizations.json",
            }[name]
            self.assertTrue(p.exists(), f"missing register {p}")

    def test_intelligence_records_resolve_to_real_questions(self):
        q_by_id = {q["question_id"]: q for q in question_records()}
        pids = paper_ids()
        regs = intel_records()
        problems = check_intelligence_set(
            list(regs["intelligence_id"].values()), q_by_id, pids,
            regs["family_id"], regs["concept_id"], regs["method_id"], regs["verification_id"],
        )
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_family_is_well_formed_and_grounded(self):
        regs = intel_records()
        q_by_id = {q["question_id"]: q for q in question_records()}
        problems = []
        for fid, fam in regs["family_id"].items():
            problems += check_family(fam, q_by_id, regs["method_id"], regs["concept_id"])
            problems += check_family_grounded(fam, q_by_id)
        problems += check_family_register(list(regs["family_id"].values()))
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_method_is_well_formed(self):
        regs = intel_records()
        problems = [p for m in regs["method_id"].values() for p in check_method(m, regs["verification_id"])]
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_verification_record_is_well_formed(self):
        regs = intel_records()
        problems = [p for v in regs["verification_id"].values() for p in check_verification(v)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_visual_spec_is_well_formed(self):
        regs = intel_records()
        problems = [p for v in regs["visual_id"].values() for p in check_visual(v, regs["family_id"])]
        self.assertEqual([], problems, "\n".join(problems))

    def test_family_count_and_assignment_are_what_the_analysis_says(self):
        """The session report claims specific counts; the register must bear them out."""
        regs = intel_records()
        qs = list(regs["intelligence_id"].values())
        resolved = [r for r in qs if not r["unresolved"]]
        self.assertEqual(101, len(qs))
        self.assertGreaterEqual(len(resolved), 90)
        unresolved = [r["question_id"] for r in qs if r["unresolved"]]
        self.assertEqual(5, len(unresolved), f"unresolved set changed: {unresolved}")


class TestIntelligenceFrequencyHonest(unittest.TestCase):
    """AC-10 — weightage figures carry a denominator, an enumerated set, and no official label."""

    def setUp(self):
        self.entries = []
        for p in json_files(WEIGHTAGE_DIR):
            self.entries.append(json.loads(p.read_text(encoding="utf-8")))
        self.pids = paper_ids()

    def test_every_frequency_entry_is_honest(self):
        problems = check_frequency_entries(self.entries, self.pids)
        self.assertEqual([], problems, "\n".join(problems))

    def test_no_entry_claims_completeness_over_a_partial_corpus(self):
        bad = [
            e["entry_id"] for e in self.entries
            if e.get("status") == "COMPLETE"
        ]
        self.assertEqual([], bad, f"entries claiming COMPLETE over a partial corpus: {bad}")


class TestIntelligenceCheckersRejectFabrication(unittest.TestCase):
    """AC-11 — the checkers can fail. Poisoned records must be rejected.

    Every checker in this file runs over a curated clean corpus; these tests feed
    deliberately fabricated records and require a complaint. Without them, a green
    suite would be evidence of nothing.
    """

    def setUp(self):
        self.q = {
            "question_id": "Q-PYQ-010001", "paper_id": "PAPER-PYQ-1601",
            "question_number": 1, "page_number": 1,
            "subject": "Arithmetic & Test of Reasoning / Mental Ability",
        }
        self.q_by_id = {"Q-PYQ-010001": self.q}
        self.pids = {"PAPER-PYQ-1601"}
        self.fam_by_id = {
            "FAM-PYQ-0001": {
                "family_id": "FAM-PYQ-0001", "question_ids": ["Q-PYQ-010001"],
                "question_type": "COMPUTATION", "confidence": "NEAR",
                "basis": "OBSERVED_FROM_CORPUS",
                "topic": "Arithmetic", "subtopic": "Number system",
                "standard_method_id": "MET-PYQ-0001", "required_concept_ids": ["CON-PYQ-0001"],
                "candidate_fast_method_ids": [], "common_mistakes": [],
                "confusing_family_ids": [], "how_to_distinguish": None,
            },
        }
        self.con_by_id = {"CON-PYQ-0001": {"concept_id": "CON-PYQ-0001"}}
        self.met_by_id = {"MET-PYQ-0001": {"method_id": "MET-PYQ-0001", "state": "OBSERVED_STANDARD"}}
        self.ver_by_id = {}

    def good_intel(self, **over) -> dict:
        rec = {
            "intelligence_id": "INT-PYQ-010001",
            "question_id": "Q-PYQ-010001", "paper_id": "PAPER-PYQ-1601",
            "source_question_number": 1, "source_page_number": 1,
            "subject": "Arithmetic & Test of Reasoning / Mental Ability",
            "topic": "Arithmetic", "subtopic": "Number system",
            "question_type": "COMPUTATION", "question_family_id": "FAM-PYQ-0001",
            "identification_clues": [{"clue": "The form of the set", "kind": "STRUCTURAL"}],
            "required_concept_id": "CON-PYQ-0001", "standard_method_id": "MET-PYQ-0001",
            "candidate_fast_method_id": None, "fast_method_state": "NO_FAST_METHOD_FOUND",
            "fast_method_verified_id": None, "common_trap_ids": [],
            "confusing_family_ids": [], "how_to_distinguish": None,
            "expected_solving_complexity": "MEDIUM", "classification_confidence": "NEAR",
            "unresolved": False, "analysis_origin": "MODEL_DERIVED",
            "evidence_tier": "T2_HISTORICAL_PYQ",
            "provenance": {"source_document_id": "PAPER-PYQ-1601",
                           "expert_source_ref": None, "generated_at": "2026-09-07"},
            "verification": {"method": None, "verified_on": None, "verified_by": None},
        }
        rec.update(over)
        return rec

    def assertRejected(self, problems, fragment: str):
        self.assertTrue(problems, f"fabricated record accepted; expected a complaint about {fragment!r}")
        joined = " | ".join(problems).lower()
        self.assertIn(fragment.lower(), joined, f"complaint was {joined!r}")

    # -- AC-11: per-question records --------------------------------------

    def test_a_clean_intelligence_record_is_accepted(self):
        self.assertEqual([], check_question_intelligence(
            self.good_intel(), self.q_by_id, self.pids,
            self.fam_by_id, self.con_by_id, self.met_by_id, self.ver_by_id))

    def test_intelligence_with_no_question_is_rejected(self):
        rec = self.good_intel(question_id="Q-PYQ-999999")
        self.assertRejected(check_question_intelligence(
            rec, self.q_by_id, self.pids, self.fam_by_id, self.con_by_id, self.met_by_id, self.ver_by_id),
            "does not resolve")

    def test_intelligence_whose_paper_disagrees_is_rejected(self):
        rec = self.good_intel(paper_id="PAPER-PYQ-9999")
        self.assertRejected(check_question_intelligence(
            rec, self.q_by_id, self.pids, self.fam_by_id, self.con_by_id, self.met_by_id, self.ver_by_id),
            "does not match")

    def test_unresolved_with_a_family_is_rejected(self):
        rec = self.good_intel(unresolved=True, topic=None, question_type="UNCLASSIFIED",
                              required_concept_id=None, standard_method_id=None)
        # leaves question_family_id set
        self.assertRejected(check_question_intelligence(
            rec, self.q_by_id, self.pids, self.fam_by_id, self.con_by_id, self.met_by_id, self.ver_by_id),
            "unresolved")

    def test_fast_verified_without_verification_is_rejected(self):
        rec = self.good_intel(fast_method_state="VERIFIED_FAST_METHOD",
                              candidate_fast_method_id="MET-PYQ-0001")
        self.assertRejected(check_question_intelligence(
            rec, self.q_by_id, self.pids, self.fam_by_id, self.con_by_id, self.met_by_id, self.ver_by_id),
            "VERIFIED_FAST_METHOD")

    def test_keyword_only_identification_is_rejected(self):
        rec = self.good_intel(identification_clues=[{"clue": "percentage", "kind": "KEYWORD"}])
        self.assertRejected(check_question_intelligence(
            rec, self.q_by_id, self.pids, self.fam_by_id, self.con_by_id, self.met_by_id, self.ver_by_id),
            "STRUCTURAL")

    def test_model_derived_presented_as_expert_is_rejected(self):
        rec = self.good_intel(analysis_origin="EXPERT_SOURCED",
                              provenance={"source_document_id": "PAPER-PYQ-1601",
                                          "expert_source_ref": None, "generated_at": None})
        self.assertRejected(check_question_intelligence(
            rec, self.q_by_id, self.pids, self.fam_by_id, self.con_by_id, self.met_by_id, self.ver_by_id),
            "EXPERT_SOURCED")

    # -- AC-11: methods ---------------------------------------------

    def good_method(self, **over) -> dict:
        m = {
            "method_id": "MET-PYQ-0099", "name": "A method that does not exist yet",
            "kind": "FAST", "state": "UNVERIFIED_FAST_METHOD", "description": "step by step",
            "when_usable": "when the condition holds", "when_not_to_use": "when it fails",
            "family_ids": ["FAM-PYQ-0001"], "concept_ids": ["CON-PYQ-0001"],
            "derived_from": "MODEL_ANALYSIS", "time_advantage": None,
            "verification_id": None, "expert_source_ref": None,
            "analysis_origin": "MODEL_DERIVED", "evidence_tier": "T2_HISTORICAL_PYQ",
            "provenance": {"source_document_ids": ["PAPER-PYQ-1601"], "generated_at": None},
            "verification_status": "UNVERIFIED",
        }
        m.update(over)
        return m

    def test_a_clean_method_is_accepted(self):
        self.assertEqual([], check_method(self.good_method(), self.ver_by_id))

    def test_a_model_derived_method_presented_as_verified_is_rejected(self):
        m = self.good_method(state="VERIFIED_FAST_METHOD")
        self.assertRejected(check_method(m, self.ver_by_id), "VERIFIED_FAST_METHOD")

    def test_a_verified_method_whose_verification_is_not_pass_is_rejected(self):
        self.ver_by_id["VER-PYQ-0001"] = {"verification_id": "VER-PYQ-0001",
                                          "method_id": "MET-PYQ-0099", "result": "FAIL"}
        m = self.good_method(state="VERIFIED_FAST_METHOD",
                             verification_id="VER-PYQ-0001", verification_status="VERIFIED")
        self.assertRejected(check_method(m, self.ver_by_id), "result")

    def test_a_verified_method_without_verification_record_is_rejected(self):
        m = self.good_method(state="VERIFIED_FAST_METHOD", verification_status="VERIFIED")
        self.assertRejected(check_method(m, self.ver_by_id), "does not resolve")

    def test_an_unverified_fast_method_claiming_verification_is_rejected(self):
        m = self.good_method(verification_id="VER-PYQ-0001")
        self.assertRejected(check_method(m, self.ver_by_id), "UNVERIFIED_FAST_METHOD")

    def test_an_expert_sourced_method_from_youtube_is_rejected(self):
        m = self.good_method(state="EXPERT_SOURCED",
                             expert_source_ref="https://youtube.com/watch?v=x",
                             analysis_origin="EXPERT_SOURCED")
        self.assertRejected(check_method(m, self.ver_by_id), "banned")

    # -- AC-11: verifications ----------------------------------------------

    def good_verification(self, **over) -> dict:
        v = {
            "verification_id": "VER-PYQ-0001", "method_id": "MET-PYQ-0099",
            "approach": "DETERMINISTIC", "procedure": "computed both over the range",
            "standard_vs_fast_equivalence": {"fast_matches_standard": True, "mismatches": 0, "note": None},
            "variants_tested": ["integer inputs"], "edge_cases_tested": ["zero"],
            "result": "PASS", "verified_on": "2026-09-07", "verified_by": "check_fast_methods.py",
            "evidence": "scripts/check_fast_methods.py", "provenance_tier": "T2_HISTORICAL_PYQ",
            "provenance": {"source_document_ids": ["PAPER-PYQ-1601"], "generated_at": None},
        }
        v.update(over)
        return v

    def test_a_clean_verification_is_accepted(self):
        self.assertEqual([], check_verification(self.good_verification()))

    def test_a_pass_with_a_mismatch_is_rejected(self):
        v = self.good_verification(standard_vs_fast_equivalence={
            "fast_matches_standard": True, "mismatches": 3, "note": "three differed"})
        self.assertRejected(check_verification(v), "mismatches")

    def test_a_pass_claiming_no_variants_is_rejected(self):
        v = self.good_verification(variants_tested=[])
        self.assertRejected(check_verification(v), "variants_tested")

    def test_a_pass_claiming_no_edge_cases_is_rejected(self):
        v = self.good_verification(edge_cases_tested=[])
        self.assertRejected(check_verification(v), "edge_cases_tested")

    # -- AC-11: families ---------------------------------------------------

    def good_family(self, **over) -> dict:
        f = {
            "family_id": "FAM-PYQ-0099", "name": "A fabricated family",
            "subject": "Arithmetic & Test of Reasoning / Mental Ability",
            "topic": "Arithmetic", "subtopic": "Number system",
            "question_type": "COMPUTATION",
            "recognition_cues": [{"clue": "form", "kind": "STRUCTURAL"}],
            "required_concept_ids": ["CON-PYQ-0001"], "standard_method_id": "MET-PYQ-0001",
            "candidate_fast_method_ids": [], "question_ids": [],
            "basis": "OBSERVED_FROM_CORPUS", "common_mistakes": [],
            "confusing_family_ids": [], "how_to_distinguish": None,
            "expected_complexity": "MEDIUM", "confidence": "NEAR",
            "analysis_origin": "MODEL_DERIVED", "evidence_tier": "T2_HISTORICAL_PYQ",
            "provenance": {"source_document_ids": ["PAPER-PYQ-1601"]},
            "verification_status": "UNVERIFIED",
        }
        f.update(over)
        return f

    def test_a_family_observed_with_no_members_is_rejected(self):
        self.assertRejected(check_family(self.good_family(), self.q_by_id, self.met_by_id, self.con_by_id),
                            "question_ids is empty")

    def test_a_family_with_a_dangling_member_is_rejected(self):
        f = self.good_family(question_ids=["Q-PYQ-999999"])
        self.assertRejected(check_family(f, self.q_by_id, self.met_by_id, self.con_by_id),
                            "does not resolve")

    def test_a_candidate_family_with_members_is_rejected(self):
        f = self.good_family(basis="UNOBSERVED_CURRICULUM_CANDIDATE",
                             question_ids=["Q-PYQ-010001"])
        self.assertRejected(check_family(f, self.q_by_id, self.met_by_id, self.con_by_id),
                            "candidate")

    def test_a_question_in_two_families_is_rejected(self):
        recs = [
            self.good_family(family_id="FAM-PYQ-0098", question_ids=["Q-PYQ-010001"]),
            self.good_family(question_ids=["Q-PYQ-010001"]),
        ]
        self.assertRejected(check_family_register(recs), "more than one")

    # -- AC-11: frequency --------------------------------------------------

    def good_frequency(self, **over) -> dict:
        e = {
            "entry_id": "WGT-PYQ-9999", "subject": "Arithmetic & Test of Reasoning / Mental Ability",
            "topic": "Arithmetic", "numerator": 10, "denominator": 100,
            "papers_included": ["PAPER-PYQ-1601"], "years_included": [2016],
            "classification_confidence": "NEAR", "basis": "OBSERVED",
            "status": "COMPLETE", "blocked_reason": None,
            "provenance_tier": "T2_HISTORICAL_PYQ",
        }
        e.update(over)
        return e

    def test_frequency_with_no_denominator_is_rejected(self):
        self.assertRejected(check_frequency_entry(self.good_frequency(denominator=None), self.pids),
                            "denominator")

    def test_frequency_counting_an_unregistered_paper_is_rejected(self):
        self.assertRejected(check_frequency_entry(
            self.good_frequency(papers_included=["PAPER-PYQ-9999"]), self.pids),
            "not registered")

    def test_an_official_label_on_a_count_is_rejected(self):
        self.assertRejected(check_frequency_entry(self.good_frequency(basis="OFFICIAL"), self.pids),
                            "OBSERVED")

    # -- AC-11: visuals ----------------------------------------------------

    def good_visual(self, **over) -> dict:
        v = {
            "visual_id": "VIS-PYQ-0001", "family_id": "FAM-PYQ-0001",
            "metaphor": "a box", "diagram_type": "SET",
            "numbers_relationships": None,
            "must_appear": ["the box"], "step_sequence": ["draw the box"],
            "recognition_clue": "the box", "common_confusion": None, "memory_anchor": None,
            "must_not_appear": ["the wrong relationship"], "color_roles": None,
            "provenance_tier": "T2_HISTORICAL_PYQ", "analysis_origin": "MODEL_DERIVED",
            "provenance": {"source_document_ids": ["PAPER-PYQ-1601"]},
        }
        v.update(over)
        return v

    def test_a_visual_with_nothing_required_is_rejected(self):
        v = self.good_visual(must_appear=[])
        self.assertRejected(check_visual(v, self.fam_by_id), "must_appear")

    def test_a_visual_for_a_missing_family_is_rejected(self):
        v = self.good_visual(family_id="FAM-PYQ-9999")
        self.assertRejected(check_visual(v, self.fam_by_id), "does not resolve")


if __name__ == "__main__":
    unittest.main()
