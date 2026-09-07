"""Session-007 PYQ foundation verification (SPEC-PYQ-001).

These tests protect one property above all others: **no previous-year question,
paper or frequency figure exists in this repository unless real, acquired bytes sit
behind it.** A past paper is evidence of behaviour, never official policy; a weightage
number is only ever a count over an enumerated, stated paper set.

Design note. As with SPEC-OFF-001, the checkers below are pure functions over plain
data, not methods that read files. That is deliberate: `TestPyqCheckersRejectFabrication`
feeds them poisoned records to prove they can fail. The content folders
(`pyq/papers`, `pyq/questions`, `pyq/weightage`) are empty today, so a suite that only
sees an empty tree would prove nothing about a populated one.

Standard library only (D-0006).
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]

SOURCE_REGISTRY = "config/pyq_source_registry.json"
DOC_REGISTRY = "config/pyq_documents.json"
PAPER_DIR = "pyq/papers"
QUESTION_DIR = "pyq/questions"
WEIGHTAGE_DIR = "pyq/weightage"
MANIFEST_DIR = "research/manifests/pyq"
RETRIEVAL_LOG = "source_material/pyq_raw/RETRIEVAL_LOG.md"
SPEC = "specs/features/pyq-questions-foundation.md"

SOURCE_TYPES = ("OFFICIAL_PUBLICATION", "COACHING_COPY", "CANDIDATE_RECALL")
URL_STATUSES = ("OBSERVED_ON_HOST", "INFERRED_UNVERIFIED", "UNKNOWN")
RETRIEVAL_STATUSES = ("RETRIEVED", "BLOCKED", "NOT_ATTEMPTED", "PARTIAL")
ANSWER_SOURCES = ("OFFICIAL_KEY", "COACHING_KEY", "UNVERIFIED")
CONFIDENCE = ("EXACT", "NEAR", "AMBIGUOUS", "UNKNOWN")
NQS = ("NONE", "PARTIAL", "COMPLETE")
DIFFICULTY = ("UNCLASSIFIED", "EASY", "MEDIUM", "HARD")
STATUSES = ("BLOCKED", "PARTIAL", "COMPLETE")
ACCEPTED_METHODS = (
    "SOURCE_DOCUMENT", "CROSS_SOURCE", "INDEPENDENT_MODEL",
    "DETERMINISTIC", "DB_CONSISTENCY",
)

# Bookkeeping files that may legitimately sit in a content folder with no content.
BOOKKEEPING_FILES = {".gitkeep", "README.md"}


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def text(value) -> str:
    return (value or "").strip() if isinstance(value, (str, type(None))) else ""


def norm(s: str) -> str:
    return " ".join(s.split())


def board_host(url: str) -> bool:
    """True only for hosts belonging to the recruitment board (SPEC-PYQ-001 R2)."""
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ("tgprb.in", "tslprb.in"))


def manifest_paths() -> list[Path]:
    return sorted((ROOT / MANIFEST_DIR).glob("*.json"))


def json_files(rel: str) -> list[Path]:
    return sorted((ROOT / rel).glob("*.json"))


def registered_paper_ids() -> set[str]:
    """Every paper id registered in the config registry or in pyq/papers."""
    ids = {d.get("paper_id") for d in load(DOC_REGISTRY)["documents"]}
    for p in json_files(PAPER_DIR):
        ids.add(json.loads(p.read_text(encoding="utf-8")).get("paper_id"))
    return {i for i in ids if i}


def papers_by_id() -> dict:
    """Paper records across the config registry and pyq/papers, keyed by id."""
    by_id: dict = {}
    for d in load(DOC_REGISTRY)["documents"]:
        by_id[d.get("paper_id")] = d
    for p in json_files(PAPER_DIR):
        rec = json.loads(p.read_text(encoding="utf-8"))
        by_id[rec.get("paper_id")] = rec
    return {k: v for k, v in by_id.items() if k}


def check_source_registry(reg: dict) -> list[str]:
    """Return every problem with the PYQ candidate-source registry (AC-1)."""
    required = (
        "registry_version", "spec", "purpose", "category", "provenance_tier",
        "status", "blocked_reason", "eligible_source_types", "eligibility_rules",
        "attempts", "accounting",
    )
    missing = [k for k in required if k not in reg]
    if missing:
        return [f"missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    if reg["provenance_tier"] != "T2_HISTORICAL_PYQ":
        p.append(f"tier is {reg['provenance_tier']!r}, must be T2_HISTORICAL_PYQ")
    if reg["status"] not in STATUSES:
        p.append(f"status {reg['status']!r} is not one of {STATUSES}")
    if reg["status"] != "COMPLETE" and len(text(reg.get("blocked_reason"))) < 20:
        p.append("not COMPLETE and no recorded reason (>= 20 chars)")

    eligible = reg["eligible_source_types"]
    for kind in SOURCE_TYPES:
        if kind not in eligible:
            p.append(f"eligible_source_types lacks {kind}")
        elif len(text(eligible[kind])) < 20:
            p.append(f"eligible_source_types[{kind}] does not say how it is eligible")
    if not reg["eligibility_rules"]:
        p.append("no eligibility_rules")

    if reg["status"] == "BLOCKED":
        if not reg["attempts"]:
            p.append("BLOCKED with no recorded attempt")
        for i, a in enumerate(reg["attempts"]):
            for k in ("timestamp", "tool", "url", "response"):
                if not text(a.get(k)):
                    p.append(f"attempt {i} has no {k}")
            if len(text(a.get("response"))) < 5:
                p.append(f"attempt {i} response is not verbatim enough")

    p += _accounting_problems(None, reg.get("accounting", {}), "source registry")
    return p


def _accounting_problems(expected, a: dict, label: str) -> list[str]:
    """The accounting identity: expected == sum of the five named buckets (AC-7).

    `expected` is passed separately because the two structures differ: the source
    registry nests it inside `accounting`, while a manifest keeps it as a sibling.
    """
    parts = ("processed", "inaccessible", "irrelevant", "duplicate", "failed")
    missing = [k for k in parts if k not in a]
    if missing:
        return [f"{label}: accounting lacks {', '.join(missing)}"]
    if "expected" not in a and expected is None:
        return [f"{label}: accounting lacks expected"]

    def whole(v) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and v >= 0

    value = a.get("expected", expected)
    if value is None:
        return [f"{label}: accounting lacks expected"]
    nonint = [k for k in parts if not whole(a[k])]
    if nonint or not whole(value):
        return [f"{label}: counts must be non-negative integers; bad {', '.join(nonint) or 'expected'}"]

    total = sum(a[k] for k in parts)
    if total != value:
        return [f"{label}: identity broken — expected {value} != " +
                " + ".join(f"{k} {a[k]}" for k in parts) + f" = {total}"]
    return []


def check_accounting(manifest: dict) -> list[str]:
    """Return every problem with a PYQ acquisition manifest's accounting identity."""
    mid = manifest.get("manifest_id", "<missing manifest_id>")
    for k in ("expected", "accounting"):
        if k not in manifest:
            return [f"{mid}: no {k} block (research/README.md requires the identity)"]
    p = _accounting_problems(manifest.get("expected"), manifest["accounting"], mid)
    if len(text(manifest.get("expected_justification"))) < 20:
        p.append(f"{mid}: expected has no recorded basis, so it is an estimate posing as a count")
    if manifest.get("status") == "blocked" and manifest["accounting"]["processed"]:
        p.append(f"{mid}: status blocked while claiming processed {manifest['accounting']['processed']}")
    return p


def check_paper(paper: dict) -> list[str]:
    """Return every problem with one previous-year paper record (AC-2).

    Applied to both the config registry's `documents` entries and any record under
    `pyq/papers/`. This is the checker that keeps a `RETRIEVED` claim honest and stops
    a coaching copy from wearing an official label.
    """
    pid = paper.get("paper_id", "<missing paper_id>")
    required = (
        "paper_id", "exam", "post", "phase", "year", "language", "marks_total",
        "questions_total", "source_type", "source_url", "source_url_status",
        "source_url_basis", "local_path", "sha256", "retrieval_status", "attempts",
        "retrieved_on", "normalized_questions", "normalized_questions_status",
        "provenance_tier", "provenance", "verification",
    )
    missing = [k for k in required if k not in paper]
    if missing:
        return [f"{pid}: missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    if not re.fullmatch(r"PAPER-PYQ-\d{4}", str(pid)):
        p.append(f"{pid}: paper_id does not match PAPER-PYQ-####")
    if paper["exam"] not in ("TELANGANA_POLICE_SI", "TELANGANA_POLICE_CONSTABLE"):
        p.append(f"{pid}: exam {paper['exam']!r} is not a Telangana Police paper")
    if paper["phase"] not in ("PRELIMINARY", "FINAL", "UNKNOWN"):
        p.append(f"{pid}: phase {paper['phase']!r} is not one of (PRELIMINARY, FINAL, UNKNOWN)")
    if paper["source_type"] not in SOURCE_TYPES:
        p.append(f"{pid}: source_type {paper['source_type']!r} is not one of {SOURCE_TYPES}")
    if paper["source_url_status"] not in URL_STATUSES:
        p.append(f"{pid}: source_url_status {paper['source_url_status']!r} is not one of {URL_STATUSES}")
    if paper["normalized_questions_status"] not in NQS:
        p.append(f"{pid}: normalized_questions_status {paper['normalized_questions_status']!r} is not one of {NQS}")
    if paper["provenance_tier"] != "T2_HISTORICAL_PYQ":
        p.append(f"{pid}: provenance_tier is {paper['provenance_tier']!r}, must be T2_HISTORICAL_PYQ")
    if len(text(paper["source_url_basis"])) < 20:
        p.append(f"{pid}: source_url_basis does not record how the source was obtained")
    if not isinstance(paper["normalized_questions"], int) or isinstance(paper["normalized_questions"], bool) \
            or paper["normalized_questions"] < 0:
        p.append(f"{pid}: normalized_questions must be a non-negative integer")

    if paper["source_type"] == "OFFICIAL_PUBLICATION":
        if not text(paper["source_url"]):
            p.append(f"{pid}: OFFICIAL_PUBLICATION with no source_url")
        elif not board_host(paper["source_url"]):
            p.append(f"{pid}: OFFICIAL_PUBLICATION but source is not on a board host — relabelled tier")

    prov = paper["provenance"] or {}
    if not text(prov.get("source_type")):
        p.append(f"{pid}: provenance has no source_type")

    status = paper["retrieval_status"]
    if status not in RETRIEVAL_STATUSES:
        return p + [f"{pid}: retrieval_status {status!r} is not one of {RETRIEVAL_STATUSES}"]

    if status == "RETRIEVED":
        for k in ("local_path", "sha256", "retrieved_on"):
            if not text(paper[k]):
                p.append(f"{pid}: RETRIEVED but {k} is empty")
        if text(paper["sha256"]) and not re.fullmatch(r"[0-9a-f]{64}", text(paper["sha256"])):
            p.append(f"{pid}: sha256 is not a 64-character hex digest")
    else:
        if text(paper["local_path"]) or text(paper["sha256"]):
            p.append(f"{pid}: not retrieved yet claims stored bytes")
        if status in ("BLOCKED", "PARTIAL"):
            if not text(paper.get("blocked_reason")):
                p.append(f"{pid}: {status} with no blocked_reason recorded")
            if not paper["attempts"]:
                p.append(f"{pid}: {status} with no recorded attempt")
            for i, a in enumerate(paper["attempts"]):
                for k in ("timestamp", "tool", "url", "response"):
                    if not text(a.get(k)):
                        p.append(f"{pid}: attempt {i} has no {k}")

    if status != "RETRIEVED" and paper["normalized_questions"]:
        p.append(f"{pid}: claims {paper['normalized_questions']} normalized questions but is not RETRIEVED")
    return p


def check_stored_paper_bytes(paper: dict, root: Path) -> list[str]:
    """Return problems with the bytes a RETRIEVED paper claims to have stored (AC-2).

    Ties the claim to reality: the file must exist where the registry says it does,
    live under source_material/pyq_raw/, and hash to the recorded digest. A question
    whose paper fails here is not sourced, whatever its provenance block says.
    """
    pid = paper.get("paper_id", "<missing paper_id>")
    if paper.get("retrieval_status") != "RETRIEVED":
        return []

    rel = text(paper.get("local_path"))
    if not rel:
        return [f"{pid}: RETRIEVED with no local_path"]
    if not rel.replace("\\", "/").startswith("source_material/pyq_raw/"):
        return [f"{pid}: local_path {rel!r} is outside source_material/pyq_raw/"]

    path = root / rel
    if not path.is_file():
        return [f"{pid}: local_path {rel!r} does not exist on disk"]

    recorded = text(paper.get("sha256"))
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if recorded != actual:
        return [
            f"{pid}: sha256 mismatch — registry says {recorded or '<empty>'}, "
            f"the bytes at {rel} hash to {actual}"
        ]
    return []


def check_question(question: dict, paper_by_id: dict) -> list[str]:
    """Return every problem with one normalized question record (AC-3, AC-5).

    The hard invariants: a question always carries an `answer_source` (even when there
    is no key), always resolves to a registered and actually-extracted paper, and is
    never relabelled `T1_OFFICIAL`.
    """
    qid = question.get("question_id", "<missing question_id>")
    required = (
        "question_id", "paper_id", "question_number", "page_number", "stem", "stem_te",
        "options", "correct_answer", "answer_source", "subject", "topic", "subtopic",
        "question_type", "concept_tested", "difficulty", "paper_year", "post_code",
        "source_type", "solving_method", "estimated_normal_time_s",
        "verified_fast_method", "fast_method_source", "identification_clues",
        "confusion_pairs", "extraction_confidence", "extraction_issues",
        "provenance_tier", "provenance", "verification",
    )
    missing = [k for k in required if k not in question]
    if missing:
        return [f"{qid}: missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    if not re.fullmatch(r"Q-PYQ-\d{6}", str(qid)):
        p.append(f"{qid}: question_id does not match Q-PYQ-######")
    if question["provenance_tier"] != "T2_HISTORICAL_PYQ":
        p.append(f"{qid}: provenance_tier is {question['provenance_tier']!r}, must be T2_HISTORICAL_PYQ")
    if question["answer_source"] not in ANSWER_SOURCES:
        p.append(f"{qid}: answer_source {question['answer_source']!r} is not one of {ANSWER_SOURCES}")
    if question["source_type"] not in SOURCE_TYPES:
        p.append(f"{qid}: source_type {question['source_type']!r} is not one of {SOURCE_TYPES}")
    if question["extraction_confidence"] not in CONFIDENCE:
        p.append(f"{qid}: extraction_confidence {question['extraction_confidence']!r} is not one of {CONFIDENCE}")
    if question["difficulty"] not in DIFFICULTY:
        p.append(f"{qid}: difficulty {question['difficulty']!r} is not one of {DIFFICULTY}")
    if not text(question["stem"]):
        p.append(f"{qid}: empty stem")

    if question["correct_answer"] is not None and question["answer_source"] == "UNVERIFIED":
        p.append(f"{qid}: keyed answer (correct_answer) but answer_source is UNVERIFIED")

    # A keyed answer may not come from a coaching key while claiming a board source;
    # and an OFFICIAL_PUBLICATION question must point at a board host.
    prov = question["provenance"] or {}
    if not text(prov.get("source_type")) or not text(prov.get("source_document_id")):
        p.append(f"{qid}: provenance lacks source_type or source_document_id")
    if question["source_type"] == "OFFICIAL_PUBLICATION":
        if not text(prov.get("url")) or not board_host(prov["url"]):
            p.append(f"{qid}: OFFICIAL_PUBLICATION but provenance.url is not on a board host")

    # Resolve the paper.
    pid = question["paper_id"]
    paper = paper_by_id.get(pid)
    if paper is None:
        p.append(f"{qid}: paper_id {pid!r} does not resolve to a registered paper")
    else:
        if paper.get("normalized_questions_status") == "NONE":
            p.append(f"{qid}: paper {pid} has no questions extracted (normalized_questions_status NONE)")
        if paper.get("retrieval_status") in ("BLOCKED", "NOT_ATTEMPTED"):
            p.append(f"{qid}: paper {pid} was not retrieved — no questions can come from it")
        if text(paper.get("source_type")) and paper["source_type"] != paper.get("source_type"):
            p.append(f"{qid}: question source_type disagrees with its paper")

    # Subject/topic/subtopic hierarchy (AC-5).
    sub, top, subj = question["subtopic"], question["topic"], question["subject"]
    if sub is not None and top is None:
        p.append(f"{qid}: subtopic with no topic")
    if top is not None and subj is None:
        p.append(f"{qid}: topic with no subject")
    if any(v is not None for v in (sub, top, subj)) and question["extraction_confidence"] in ("EXACT", "NEAR") \
            and subj is None:
        p.append(f"{qid}: classification present but no subject")

    # A missing question number must be recorded as an issue, not dropped.
    if question["question_number"] is None and not question["extraction_issues"]:
        p.append(f"{qid}: question_number missing with no extraction issue recorded")

    method = (question["verification"] or {}).get("method")
    if method is not None and method not in ACCEPTED_METHODS:
        p.append(f"{qid}: verification method {method!r} is not an accepted independent method")
    return p


def check_question_set(questions: list[dict], paper_by_id: dict) -> list[str]:
    """Return every problem across a set of question records (AC-4).

    Detects duplicate question_ids and duplicate (paper, question_number) pairs, and
    runs the single-record checker on each.
    """
    p: list[str] = []
    ids = [q.get("question_id") for q in questions]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        p.append(f"duplicate question_id(s): {dupes}")

    seen_pairs: dict = {}
    for q in questions:
        p += check_question(q, paper_by_id)
        pid = q.get("paper_id")
        num = q.get("question_number")
        if pid and num is not None:
            key = (pid, num)
            if key in seen_pairs:
                p.append(f"duplicate (paper, question_number) ({pid}, {num})")
            seen_pairs[key] = True
    return p


def check_weightage(entry: dict, paper_ids: set[str]) -> list[str]:
    """Return every problem with one observed-frequency entry (AC-6).

    This is the checker that makes a weightage number honest: no numerator without a
    denominator, no zero denominator, every counted paper resolved, partial coverage
    labelled, and never an official label on an observed count.
    """
    eid = entry.get("entry_id", "<missing entry_id>")
    required = (
        "entry_id", "subject", "topic", "numerator", "denominator",
        "papers_included", "years_included", "classification_confidence",
        "basis", "status", "blocked_reason", "provenance_tier",
    )
    missing = [k for k in required if k not in entry]
    if missing:
        return [f"{eid}: missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    if not re.fullmatch(r"WGT-PYQ-\d{4}", str(eid)):
        p.append(f"{eid}: entry_id does not match WGT-PYQ-####")
    if entry["basis"] != "OBSERVED":
        p.append(f"{eid}: basis {entry['basis']!r} must be OBSERVED (counted from PYQs)")
    if entry["provenance_tier"] != "T2_HISTORICAL_PYQ":
        p.append(f"{eid}: provenance_tier is {entry['provenance_tier']!r}, must be T2_HISTORICAL_PYQ")
    if entry["status"] not in STATUSES:
        p.append(f"{eid}: status {entry['status']!r} is not one of {STATUSES}")
    if entry["classification_confidence"] not in CONFIDENCE:
        p.append(f"{eid}: classification_confidence {entry['classification_confidence']!r} is not one of {CONFIDENCE}")
    if not text(entry["subject"]):
        p.append(f"{eid}: empty subject")

    num = entry["numerator"]
    den = entry["denominator"]
    if num is not None:
        if den is None or den <= 0:
            p.append(f"{eid}: numerator {num} with no positive denominator")
    if den is None or den == 0:
        if num is not None:
            p.append(f"{eid}: a count over zero questions is not a count")
        elif den == 0 and num is None:
            p.append(f"{eid}: denominator is 0")

    if entry["status"] == "COMPLETE":
        if num is None or den is None:
            p.append(f"{eid}: COMPLETE but numerator/denominator not both set")
        if not entry["papers_included"]:
            p.append(f"{eid}: COMPLETE but no papers_included — an unenumerated set")
    if entry["status"] == "PARTIAL":
        pc = entry.get("partial_coverage")
        if not pc:
            p.append(f"{eid}: PARTIAL but no partial_coverage (counted/intended)")
        else:
            for k in ("papers_counted", "papers_intended", "questions_counted", "questions_intended"):
                if not isinstance(pc.get(k), int) or isinstance(pc.get(k), bool):
                    p.append(f"{eid}: partial_coverage.{k} is not an integer")
    if entry["status"] == "BLOCKED" and len(text(entry["blocked_reason"])) < 20:
        p.append(f"{eid}: BLOCKED with no recorded reason")

    included = entry["papers_included"]
    if included:
        for pid in included:
            if pid not in paper_ids:
                p.append(f"{eid}: counted paper {pid!r} is not a registered paper")
    else:
        if num is not None:
            p.append(f"{eid}: a numerator with no enumerated paper set")
    if not all(isinstance(y, int) and not isinstance(y, bool) for y in entry["years_included"]):
        p.append(f"{eid}: years_included must be integers")
    return p


class TestPyqSourceRegistryExists(unittest.TestCase):
    """AC-1 — the candidate-source registry exists and records the blocked state."""

    def setUp(self):
        self.reg = load(SOURCE_REGISTRY)

    def test_registry_declares_its_own_tier(self):
        self.assertEqual("T2_HISTORICAL_PYQ", self.reg["provenance_tier"])

    def test_every_eligible_source_type_is_documented(self):
        eligible = self.reg["eligible_source_types"]
        for kind in SOURCE_TYPES:
            with self.subTest(kind=kind):
                self.assertIn(kind, eligible)
                self.assertGreater(len(self.reg["eligible_source_types"][kind]), 20)

    def test_eligibility_rules_are_recorded(self):
        self.assertTrue(self.reg["eligibility_rules"], "no eligibility_rules recorded")

    def test_a_non_complete_status_explains_itself(self):
        if self.reg["status"] == "COMPLETE":
            self.skipTest("registry complete; the emptiness rules do not apply")
        self.assertGreater(len(text(self.reg["blocked_reason"])), 20)
        self.assertTrue(self.reg["attempts"], "blocked with no recorded attempt")

    def test_the_accounting_identity_holds(self):
        self.assertEqual([], _accounting_problems(None, self.reg["accounting"], "source registry"))

    def test_every_recorded_attempt_appears_verbatim_in_the_retrieval_log(self):
        log = norm(read(RETRIEVAL_LOG))
        problems = []
        for a in self.reg.get("attempts", []):
            if a["url"] not in log:
                problems.append(f"attempt url absent from the log: {a['url']}")
            if norm(a["response"]) not in log:
                problems.append(f"attempt response not recorded verbatim in the log: {a['url']}")
        self.assertEqual([], sorted(set(problems)), "\n".join(sorted(set(problems))))


class TestPyqDocumentRegistryExists(unittest.TestCase):
    """AC-1 — the target/acquired paper registry exists and records the blocked state."""

    def setUp(self):
        self.reg = load(DOC_REGISTRY)

    def test_registry_declares_its_own_tier(self):
        self.assertEqual("T2_HISTORICAL_PYQ", self.reg["provenance_tier"])

    def test_registry_is_bound_to_this_spec(self):
        self.assertEqual("SPEC-PYQ-001", self.reg["spec"])

    def test_a_non_complete_status_explains_itself(self):
        if self.reg["status"] == "COMPLETE":
            self.skipTest("registry complete; the emptiness rules do not apply")
        self.assertGreater(len(text(self.reg["blocked_reason"])), 20)

    def test_paper_requirements_cover_both_components(self):
        comps = self.reg["paper_requirements"]["components_to_cover"]
        self.assertGreaterEqual(len(comps), 2)
        self.assertTrue(any("Arithmetic" in c["component"] for c in comps))
        self.assertTrue(any("General Studies" in c["component"] for c in comps))

    def test_retrieved_count_matches_the_records(self):
        retrieved = {d["paper_id"] for d in self.reg["documents"]
                     if d.get("retrieval_status") == "RETRIEVED"}
        self.assertEqual(len(retrieved), self.reg["retrieved_count"])

    def test_extracted_question_count_matches_the_records(self):
        total = sum(d.get("normalized_questions", 0) or 0 for d in self.reg["documents"])
        self.assertEqual(total, self.reg["extracted_question_count"])


class TestPyqPaperRecords(unittest.TestCase):
    """AC-2 — every paper record is well-formed and its stored state is honest."""

    def setUp(self):
        self.by_id = papers_by_id()
        self.records = list(self.by_id.values())

    def test_every_paper_record_is_well_formed(self):
        problems = [p for r in self.records for p in check_paper(r)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_paper_ids_are_unique(self):
        ids = list(self.by_id)
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], dupes, f"duplicate paper_id(s): {dupes}")

    def test_every_registered_paper_is_on_a_board_host_if_official(self):
        strays = [
            (r["paper_id"], r.get("source_url"))
            for r in self.records
            if r.get("source_type") == "OFFICIAL_PUBLICATION" and not board_host(text(r.get("source_url")))
        ]
        self.assertEqual([], strays, f"official-labelled papers not on a board host: {strays}")

    def test_no_paper_claims_normalized_questions_without_retrieval(self):
        bad = [
            r["paper_id"] for r in self.records
            if r.get("retrieval_status") != "RETRIEVED" and (r.get("normalized_questions") or 0)
        ]
        self.assertEqual([], bad, f"papers claiming questions while not RETRIEVED: {bad}")

    def test_no_stored_bytes_claim_when_nothing_is_retrieved(self):
        retrieved = [r for r in self.records if r.get("retrieval_status") == "RETRIEVED"]
        if not retrieved:
            self.assertEqual([], self.records, "no paper retrieved, yet a paper record exists")
        for r in retrieved:
            self.assertEqual([], check_stored_paper_bytes(r, ROOT))


class TestPyqQuestionRecords(unittest.TestCase):
    """AC-3, AC-4, AC-5 — question records resolve, carry an answer source, and are unique."""

    def setUp(self):
        self.questions = []
        for p in json_files(QUESTION_DIR):
            self.questions.append(json.loads(p.read_text(encoding="utf-8")))
        self.paper_by_id = papers_by_id()

    def test_every_question_record_is_well_formed_and_sourced(self):
        problems = [p for q in self.questions for p in check_question(q, self.paper_by_id)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_the_whole_set_rejects_duplicates(self):
        self.assertEqual([], check_question_set(self.questions, self.paper_by_id))

    def test_no_question_exists_with_no_paper(self):
        unresolved = [
            q["question_id"] for q in self.questions
            if q.get("paper_id") not in self.paper_by_id
        ]
        if self.questions:
            self.assertEqual([], unresolved, f"questions with no registered paper: {unresolved}")

    def test_every_paper_included_truly_has_extracted_questions(self):
        bad = [
            q["question_id"] for q in self.questions
            if self.paper_by_id.get(q.get("paper_id"), {}).get("normalized_questions_status") == "NONE"
        ]
        self.assertEqual([], bad, f"questions sourced from a NONE-extracted paper: {bad}")


class TestPyqWeightageRecords(unittest.TestCase):
    """AC-6 — no observed frequency entry survives without a denominator and an enumerated set."""

    def setUp(self):
        self.entries = []
        for p in json_files(WEIGHTAGE_DIR):
            self.entries.append(json.loads(p.read_text(encoding="utf-8")))
        self.paper_ids = set(papers_by_id())

    def test_every_weightage_entry_is_well_formed(self):
        problems = [p for e in self.entries for p in check_weightage(e, self.paper_ids)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_entry_ids_are_unique(self):
        ids = [e.get("entry_id") for e in self.entries]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], dupes, f"duplicate entry_id(s): {dupes}")

    def test_no_entry_has_a_numerator_without_a_denominator(self):
        bad = [
            e["entry_id"] for e in self.entries
            if e.get("numerator") is not None and (e.get("denominator") is None or e.get("denominator") <= 0)
        ]
        self.assertEqual([], bad, f"entries with a numerator but no denominator: {bad}")

    def test_no_complete_entry_without_an_enumerated_paper_set(self):
        bad = [
            e["entry_id"] for e in self.entries
            if e.get("status") == "COMPLETE" and not e.get("papers_included")
        ]
        self.assertEqual([], bad, f"COMPLETE entries with no enumerated paper set: {bad}")

    def test_no_observed_frequency_is_labelled_official(self):
        bad = [
            e["entry_id"] for e in self.entries
            if e.get("basis") != "OBSERVED" or e.get("provenance_tier") != "T2_HISTORICAL_PYQ"
        ]
        self.assertEqual([], bad, f"entries not labelled as observed historical: {bad}")


class TestPyqBlockedSourcesRecordedExplicitly(unittest.TestCase):
    """AC-7 — what could not be obtained is written down, not passed over."""

    def setUp(self):
        self.manifests = [json.loads(p.read_text(encoding="utf-8")) for p in manifest_paths()]

    def test_every_manifest_balances_the_accounting_identity(self):
        problems = [p for m in self.manifests for p in check_accounting(m)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_unretrieved_paper_is_named_in_a_manifest(self):
        listed = {
            i.get("paper_id") for m in self.manifests for i in m.get("inaccessible_items", [])
        }
        missing = [
            d["paper_id"] for d in load(DOC_REGISTRY)["documents"]
            if d.get("retrieval_status") != "RETRIEVED" and d["paper_id"] not in listed
        ]
        self.assertEqual([], missing, f"papers not obtained and not accounted for: {missing}")

    def test_every_blocker_referenced_is_declared_in_project_state(self):
        state = read("PROJECT_STATE.md")
        referenced: set[str] = set()
        for rel in (SOURCE_REGISTRY, DOC_REGISTRY, RETRIEVAL_LOG, SPEC):
            referenced |= set(re.findall(r"\bB-\d{2}\b", read(rel)))
        for p in manifest_paths():
            referenced |= set(re.findall(r"\bB-\d{2}\b", p.read_text(encoding="utf-8")))
        missing = sorted(b for b in referenced if b not in state)
        self.assertEqual(
            [], missing,
            f"blockers cited by PYQ records but absent from PROJECT_STATE.md: {missing}",
        )

    def test_an_acquisition_manifest_exists(self):
        self.assertTrue(manifest_paths(), f"no acquisition manifest under {MANIFEST_DIR}")


DIGEST = "a" * 64


def good_source_paper(**over) -> dict:
    """A paper that has been retrieved and fully extracted — a legit question source."""
    p = {
        "paper_id": "PAPER-PYQ-2024",
        "exam": "TELANGANA_POLICE_SI",
        "post": "SI (Civil et al)",
        "phase": "PRELIMINARY",
        "paper_number": 3,
        "year": 2024,
        "language": "English",
        "marks_total": 200,
        "questions_total": 200,
        "source_type": "COACHING_COPY",
        "source_url": "https://www.somecoaching.com/tgprb-si-2024.pdf",
        "source_url_status": "OBSERVED_ON_HOST",
        "source_url_basis": "Observed on the coaching site by a search restricted to that host.",
        "local_path": "source_material/pyq_raw/si-2024.pdf",
        "sha256": DIGEST,
        "retrieval_status": "RETRIEVED",
        "attempts": [],
        "retrieved_on": "2026-09-07",
        "normalized_questions": 200,
        "normalized_questions_status": "COMPLETE",
        "provenance_tier": "T2_HISTORICAL_PYQ",
        "provenance": {"source_type": "COACHING_COPY"},
        "verification": {"method": "SOURCE_DOCUMENT", "verified_on": "2026-09-07", "verified_by": "session 007"},
        "blocked_reason": None,
    }
    p.update(over)
    return p


def good_paper(**over) -> dict:
    """A retrieved paper record not tied to any fixture question, for the stored-bytes
    checks. Explicit overrides win; defaults describe a retrieved paper with no
    questions extracted yet."""
    p = {
        "paper_id": "PAPER-PYQ-2024",
        "exam": "TELANGANA_POLICE_SI",
        "post": "SI (Civil et al)",
        "phase": "PRELIMINARY",
        "paper_number": 3,
        "year": 2024,
        "language": "English",
        "marks_total": 200,
        "questions_total": 200,
        "source_type": "COACHING_COPY",
        "source_url": "https://www.somecoaching.com/tgprb-si-2024.pdf",
        "source_url_status": "OBSERVED_ON_HOST",
        "source_url_basis": "Observed on the coaching site by a search restricted to that host.",
        "local_path": "source_material/pyq_raw/si-2024.pdf",
        "sha256": DIGEST,
        "retrieval_status": "RETRIEVED",
        "attempts": [],
        "retrieved_on": "2026-09-07",
        "normalized_questions": 0,
        "normalized_questions_status": "NONE",
        "provenance_tier": "T2_HISTORICAL_PYQ",
        "provenance": {"source_type": "COACHING_COPY"},
        "verification": {"method": "SOURCE_DOCUMENT", "verified_on": "2026-09-07", "verified_by": "session 007"},
        "blocked_reason": None,
    }
    p.update(over)
    return p


def good_question(**over) -> dict:
    q = {
        "question_id": "Q-PYQ-000001",
        "paper_id": "PAPER-PYQ-2024",
        "question_number": 1,
        "page_number": 3,
        "stem": "Which of the following numbers is a perfect square?",
        "stem_te": None,
        "options": {"A": "10", "B": "16", "C": "18", "D": "20"},
        "correct_answer": "B",
        "answer_source": "COACHING_KEY",
        "subject": "Arithmetic & Test of Reasoning / Mental Ability",
        "topic": "Squares and Roots",
        "subtopic": "Perfect squares",
        "question_type": "COMPUTATION",
        "concept_tested": "Perfect squares",
        "difficulty": "EASY",
        "paper_year": 2024,
        "post_code": "SI-Civil",
        "source_type": "COACHING_COPY",
        "solving_method": None,
        "estimated_normal_time_s": 30,
        "verified_fast_method": None,
        "fast_method_source": None,
        "identification_clues": [],
        "confusion_pairs": [],
        "extraction_confidence": "EXACT",
        "extraction_issues": [],
        "provenance_tier": "T2_HISTORICAL_PYQ",
        "provenance": {
            "source_type": "COACHING_COPY", "source_document_id": "PAPER-PYQ-2024",
            "url": None, "page": 3, "question_number": 1,
        },
        "verification": {"method": None, "verified_on": None, "verified_by": None},
    }
    q.update(over)
    return q


def good_weightage(**over) -> dict:
    e = {
        "entry_id": "WGT-PYQ-0001",
        "subject": "Arithmetic & Test of Reasoning / Mental Ability",
        "topic": "Percentage",
        "question_type": None,
        "numerator": 12,
        "denominator": 200,
        "papers_included": ["PAPER-PYQ-2024"],
        "years_included": [2024],
        "classification_confidence": "EXACT",
        "basis": "OBSERVED",
        "status": "COMPLETE",
        "blocked_reason": None,
        "provenance_tier": "T2_HISTORICAL_PYQ",
        "partial_coverage": None,
    }
    e.update(over)
    return e


class TestPyqCheckersRejectFabrication(unittest.TestCase):
    """AC-8 — prove the checkers above can fail.

    Every check in this file currently runs over empty or blocked records, where
    passing is easy. These tests feed the same checkers deliberately fabricated
    records and require a complaint. Without them, a green suite would be evidence
    of nothing.
    """

    def setUp(self):
        self.paper_by_id = {"PAPER-PYQ-2024": good_source_paper()}
        self.paper_ids = {"PAPER-PYQ-2024"}

    def assertRejected(self, problems, fragment: str):
        self.assertTrue(problems, f"fabricated record accepted; expected a complaint about {fragment!r}")
        joined = " | ".join(problems).lower()
        self.assertIn(fragment.lower(), joined, f"complaint was {joined!r}")

    def test_a_clean_record_set_is_accepted(self):
        """The other half of the proof: these checkers are not simply always failing."""
        self.assertEqual([], check_paper(good_paper()))
        self.assertEqual([], check_question(good_question(), self.paper_by_id))
        self.assertEqual([], check_weightage(good_weightage(), self.paper_ids))
        reg = load(SOURCE_REGISTRY)
        self.assertEqual([], check_source_registry(reg))

    def test_a_question_with_no_paper_is_rejected(self):
        q = good_question(paper_id="PAPER-PYQ-9999")
        self.assertRejected(check_question(q, self.paper_by_id), "does not resolve")

    def test_a_question_with_no_answer_source_is_rejected(self):
        q = good_question()
        del q["answer_source"]
        self.assertRejected(check_question(q, self.paper_by_id), "answer_source")

    def test_a_paper_claiming_retrieved_bytes_that_do_not_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source_material" / "pyq_raw").mkdir(parents=True)
            (root / "source_material" / "pyq_raw" / "si-2024.pdf").write_bytes(b"paper bytes")
            self.assertRejected(check_stored_paper_bytes(good_paper(), root), "sha256 mismatch")
            real = hashlib.sha256(b"paper bytes").hexdigest()
            self.assertEqual([], check_stored_paper_bytes(good_paper(sha256=real), root))

    def test_a_paper_with_no_stored_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertRejected(check_stored_paper_bytes(good_paper(), Path(tmp)), "does not exist on disk")

    def test_a_coaching_copy_labelled_official_is_rejected(self):
        paper = good_paper(
            source_type="OFFICIAL_PUBLICATION",
            source_url="https://www.somecoaching.com/tgprb-si-2024.pdf",
        )
        self.assertRejected(check_paper(paper), "not on a board host")

    def test_a_question_labelled_official_with_a_coaching_url_is_rejected(self):
        q = good_question(
            source_type="OFFICIAL_PUBLICATION",
            provenance=dict(good_question()["provenance"], url="https://www.somecoaching.com/x.pdf"),
        )
        self.assertRejected(check_question(q, self.paper_by_id), "not on a board host")

    def test_a_weightage_entry_with_a_numerator_but_no_denominator_is_rejected(self):
        self.assertRejected(check_weightage(good_weightage(denominator=None), self.paper_ids), "denominator")

    def test_a_weightage_entry_with_a_zero_denominator_is_rejected(self):
        self.assertRejected(check_weightage(good_weightage(numerator=None, denominator=0), self.paper_ids), "denominator")

    def test_a_question_with_a_missing_number_and_no_issue_is_rejected(self):
        q = good_question(question_number=None, extraction_issues=[])
        self.assertRejected(check_question(q, self.paper_by_id), "extraction issue")

    def test_a_paper_claiming_questions_while_not_retrieved_is_rejected(self):
        paper = good_paper(
            retrieval_status="BLOCKED",
            blocked_reason="The paper host refused by the egress allowlist.",
            attempts=[{"timestamp": "2026-09-07T00:00:00Z", "tool": "fetch", "url": "https://x", "response": "refused"}],
            local_path=None, sha256=None, retrieved_on=None,
            normalized_questions=200, normalized_questions_status="COMPLETE",
        )
        self.assertRejected(check_paper(paper), "claims")

    def test_a_question_from_a_none_extracted_paper_is_rejected(self):
        self.assertRejected(
            check_question(good_question(), {"PAPER-PYQ-2024": good_source_paper(normalized_questions=0, normalized_questions_status="NONE")}),
            "no questions extracted",
        )

    def test_an_unbalanced_manifest_is_rejected(self):
        m = {
            "manifest_id": "PYQ-ACQ-999", "expected": 7,
            "expected_justification": "Counted from an enumerated candidate list.",
            "accounting": {"processed": 1, "inaccessible": 1, "irrelevant": 0, "duplicate": 0, "failed": 0},
        }
        self.assertRejected(check_accounting(m), "identity broken")

    def test_a_blocked_source_registry_with_no_attempt_is_rejected(self):
        reg = dict(load(SOURCE_REGISTRY))
        reg["attempts"] = []
        reg["blocked_reason"] = "The paper host was refused by the egress allowlist and no source was reached."
        self.assertRejected(check_source_registry(reg), "no recorded attempt")

    def test_a_weightage_entry_counting_an_unregistered_paper_is_rejected(self):
        self.assertRejected(
            check_weightage(good_weightage(papers_included=["PAPER-PYQ-9999"]), self.paper_ids),
            "not a registered paper",
        )


if __name__ == "__main__":
    unittest.main()
