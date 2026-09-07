"""Phase-1 verification: the official knowledge foundation (SPEC-OFF-001).

These tests protect one property above all others: **no official examination fact
exists in this repository unless an official document behind it has been retrieved,
stored and hashed.**

Design note. The checkers below are pure functions over plain data, not methods that
read files. That is deliberate: `TestCheckersRejectFabrication` feeds them poisoned
records to prove they can fail. A suite that only ever sees an empty tree proves
nothing about a populated one, and an empty tree is exactly what this phase has.

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

REQUIRED_FACT_IDS = [f"OFF-F{i:02d}" for i in range(1, 26)]
LEVELS = ("subject", "topic", "subtopic")
FACT_STATUSES = ("BLOCKED", "UNVERIFIED", "VERIFIED")
URL_STATUSES = ("OBSERVED_ON_OFFICIAL_DOMAIN", "INFERRED_UNVERIFIED", "UNKNOWN")
RETRIEVAL_STATUSES = ("RETRIEVED", "BLOCKED", "NOT_ATTEMPTED")
ACCEPTED_METHODS = (
    "SOURCE_DOCUMENT", "CROSS_SOURCE", "INDEPENDENT_MODEL",
    "DETERMINISTIC", "DB_CONSISTENCY",
)
NON_OFFICIAL_TIERS = ("T2_HISTORICAL_PYQ", "T3_EXPERT", "T4_AI")

DOC_REGISTRY = "config/official_documents.json"
FACTS = "knowledge/official/required_facts.json"
SYLLABUS = "knowledge/official/syllabus.json"
PREP_TAXONOMY = "knowledge/preparation_taxonomy/taxonomy.json"
WEIGHTAGE = {
    "official_marks_structure": "knowledge/weightage/official_marks_structure.json",
    "historical_observed": "knowledge/weightage/historical_observed.json",
    "estimated_priority": "knowledge/weightage/estimated_priority.json",
}
MANIFEST_DIR = "research/manifests/official"
RETRIEVAL_LOG = "source_material/official/RETRIEVAL_LOG.md"
CURRENT = "knowledge/official/current_official.json"

# A derived reading is arithmetic over sourced components, so DERIVED_ARITHMETIC
# is a legitimate independent method for the reconciliation registry.
CURRENT_ACCEPTED_METHODS = ACCEPTED_METHODS + ("DERIVED_ARITHMETIC",)


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def retrieved_document_ids(registry: dict) -> set[str]:
    return {
        d.get("document_id")
        for d in registry.get("documents", [])
        if d.get("retrieval_status") == "RETRIEVED"
    }


def text(value) -> str:
    return (value or "").strip() if isinstance(value, (str, type(None))) else ""


def check_document(doc: dict) -> list[str]:
    """Return every problem with one official-document registry entry."""
    did = doc.get("document_id", "<missing document_id>")
    required = (
        "document_id", "title", "publisher", "url", "url_status", "url_basis",
        "document_type", "expected_content", "retrieval_status", "attempts",
        "local_path", "sha256", "document_date", "retrieved_on",
    )
    missing = [k for k in required if k not in doc]
    if missing:
        return [f"{did}: missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    if not re.fullmatch(r"DOC-OFF-\d{3}", str(did)):
        p.append(f"{did}: document_id does not match DOC-OFF-###")
    if doc["url_status"] not in URL_STATUSES:
        p.append(f"{did}: url_status {doc['url_status']!r} is not one of {URL_STATUSES}")
    if len(text(doc["url_basis"])) < 20:
        p.append(f"{did}: url_basis must record how the URL was obtained")
    if not str(doc["url"]).startswith("https://"):
        p.append(f"{did}: url is not https")
    for fid in doc["expected_content"]:
        if not re.fullmatch(r"OFF-F\d{2}", str(fid)):
            p.append(f"{did}: expected_content {fid!r} is not a fact id")

    status = doc["retrieval_status"]
    if status not in RETRIEVAL_STATUSES:
        return p + [f"{did}: retrieval_status {status!r} is not one of {RETRIEVAL_STATUSES}"]

    if status == "RETRIEVED":
        for k in ("local_path", "sha256", "retrieved_on"):
            if not text(doc[k]):
                p.append(f"{did}: RETRIEVED but {k} is empty")
        if text(doc["sha256"]) and not re.fullmatch(r"[0-9a-f]{64}", text(doc["sha256"])):
            p.append(f"{did}: sha256 is not a 64-character hex digest")
    else:
        if not text(doc.get("blocked_reason")):
            p.append(f"{did}: {status} but no blocked_reason recorded")
        if text(doc["local_path"]) or text(doc["sha256"]):
            p.append(f"{did}: not retrieved yet claims stored bytes")
        if status == "BLOCKED":
            if not doc["attempts"]:
                p.append(f"{did}: BLOCKED with no recorded attempt")
            for i, a in enumerate(doc["attempts"]):
                for k in ("timestamp", "tool", "url", "response"):
                    if not text(a.get(k)):
                        p.append(f"{did}: attempt {i} has no {k}")
    return p


def check_fact(fact: dict, retrieved_ids: set[str]) -> list[str]:
    """Return every problem with one official fact record."""
    fid = fact.get("fact_id", "<missing fact_id>")
    required = (
        "fact_id", "name", "must_capture", "value", "value_te", "status",
        "provenance_tier", "provenance", "verification",
    )
    missing = [k for k in required if k not in fact]
    if missing:
        return [f"{fid}: missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    if fact["provenance_tier"] != "T1_OFFICIAL":
        p.append(f"{fid}: provenance_tier is {fact['provenance_tier']!r}, must be T1_OFFICIAL")
    if fact["status"] not in FACT_STATUSES:
        p.append(f"{fid}: status {fact['status']!r} is not one of {FACT_STATUSES}")
    if len(text(fact["must_capture"])) < 10:
        p.append(f"{fid}: must_capture does not say what a correct reading captures")

    prov = fact["provenance"] or {}
    doc_id = prov.get("document_id")

    if fact["value"] is not None:
        if fact["status"] != "VERIFIED":
            p.append(f"{fid}: holds a value while status is {fact['status']!r}")
        if not doc_id:
            p.append(f"{fid}: holds a value with no provenance document — unsupported claim")
        elif doc_id not in retrieved_ids:
            p.append(
                f"{fid}: provenance cites {doc_id}, which is not a retrieved document"
            )
        if not text(prov.get("quote")):
            p.append(f"{fid}: holds a value with no verbatim quote")
    else:
        if fact["status"] == "VERIFIED":
            p.append(f"{fid}: status VERIFIED with no value")
        if not text(fact.get("blocked_reason")):
            p.append(f"{fid}: not verified and no reason recorded")

    if fact["status"] == "VERIFIED":
        method = (fact["verification"] or {}).get("method")
        if method not in ACCEPTED_METHODS:
            p.append(
                f"{fid}: VERIFIED with method {method!r}; self-review is not a "
                f"verification method (VERIFICATION_POLICY.md)"
            )
    return p


def check_syllabus_node(node: dict, by_id: dict, retrieved_ids: set[str]) -> list[str]:
    """Return every problem with one official syllabus node."""
    nid = node.get("node_id", "<missing node_id>")
    required = (
        "node_id", "level", "parent_id", "title", "title_te", "ordinal",
        "provenance_tier", "provenance", "verification",
    )
    missing = [k for k in required if k not in node]
    if missing:
        return [f"{nid}: missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    if node["provenance_tier"] != "T1_OFFICIAL":
        p.append(f"{nid}: provenance_tier is {node['provenance_tier']!r}, must be T1_OFFICIAL")
    if not text(node["title"]):
        p.append(f"{nid}: empty title")
    if not isinstance(node["ordinal"], int) or isinstance(node["ordinal"], bool) or node["ordinal"] < 1:
        p.append(f"{nid}: ordinal must be a positive integer, got {node['ordinal']!r}")

    level = node["level"]
    parent = node["parent_id"]
    if level not in LEVELS:
        p.append(f"{nid}: level {level!r} is not one of {LEVELS}")
    elif level == "subject":
        if parent is not None:
            p.append(f"{nid}: a subject must have parent_id null, got {parent!r}")
    else:
        expected_parent_level = LEVELS[LEVELS.index(level) - 1]
        if parent is None:
            p.append(f"{nid}: {level} has no parent")
        elif parent not in by_id:
            p.append(f"{nid}: parent {parent!r} does not exist")
        elif by_id[parent].get("level") != expected_parent_level:
            p.append(
                f"{nid}: parent {parent} is a {by_id[parent].get('level')!r}, "
                f"expected a {expected_parent_level!r}"
            )

    doc_id = (node["provenance"] or {}).get("document_id")
    if not doc_id:
        p.append(f"{nid}: no provenance document — an unsourced syllabus node")
    elif doc_id not in retrieved_ids:
        p.append(f"{nid}: provenance cites {doc_id}, which is not a retrieved document")
    return p


def check_prep_node(node: dict, official_ids: set[str]) -> list[str]:
    """Return every problem with one preparation-taxonomy node (non-official by design)."""
    nid = node.get("node_id", "<missing node_id>")
    required = (
        "node_id", "title", "title_te", "official_anchor",
        "anchor_justification", "provenance_tier", "derived_from",
    )
    missing = [k for k in required if k not in node]
    if missing:
        return [f"{nid}: missing field(s) {', '.join(missing)}"]

    p: list[str] = []
    tier = node["provenance_tier"]
    if tier == "T1_OFFICIAL":
        p.append(
            f"{nid}: T1_OFFICIAL inside the preparation taxonomy — a coaching "
            f"breakdown wearing an official label"
        )
    elif tier not in NON_OFFICIAL_TIERS:
        p.append(f"{nid}: provenance_tier {tier!r} is not one of {NON_OFFICIAL_TIERS}")

    anchor = node["official_anchor"]
    if anchor != "NO_OFFICIAL_ANCHOR" and anchor not in official_ids:
        p.append(
            f"{nid}: official_anchor {anchor!r} is neither NO_OFFICIAL_ANCHOR nor an "
            f"existing official syllabus node"
        )
    if not node["derived_from"]:
        p.append(f"{nid}: derived_from is empty — a node nobody can trace back")
    if len(text(node["anchor_justification"])) < 10:
        p.append(f"{nid}: no anchor_justification")
    return p


def check_accounting(manifest: dict) -> list[str]:
    """Return every problem with a harvest manifest's accounting identity."""
    mid = manifest.get("manifest_id", "<missing manifest_id>")
    for k in ("expected", "accounting"):
        if k not in manifest:
            return [f"{mid}: no {k} block (research/README.md requires the identity)"]

    a = manifest["accounting"]
    parts = ("processed", "inaccessible", "irrelevant", "duplicate", "failed")
    missing = [k for k in parts if k not in a]
    if missing:
        return [f"{mid}: accounting lacks {', '.join(missing)}"]

    def whole(v) -> bool:
        return isinstance(v, int) and not isinstance(v, bool) and v >= 0

    nonint = [k for k in parts if not whole(a[k])]
    if nonint or not whole(manifest["expected"]):
        return [
            f"{mid}: counts must be non-negative integers; bad: "
            f"{', '.join(nonint) or 'expected'}"
        ]

    p: list[str] = []
    total = sum(a[k] for k in parts)
    if total != manifest["expected"]:
        p.append(
            f"{mid}: identity broken — expected {manifest['expected']} != "
            + " + ".join(f"{k} {a[k]}" for k in parts)
            + f" = {total}"
        )
    if len(text(manifest.get("expected_justification"))) < 20:
        p.append(f"{mid}: expected has no recorded basis, so it is an estimate posing as a count")
    if manifest.get("status") == "blocked" and a["processed"]:
        p.append(f"{mid}: status blocked while claiming processed {a['processed']}")
    return p


def check_stored_bytes(doc: dict, root: Path) -> list[str]:
    """Return problems with the bytes a RETRIEVED document claims to have stored.

    This is the check that ties a claim to reality: the file must exist where the
    registry says it does, live under source_material/official/, and hash to the
    recorded digest. A fact whose document fails here is not sourced, whatever its
    provenance block says.
    """
    did = doc.get("document_id", "<missing document_id>")
    if doc.get("retrieval_status") != "RETRIEVED":
        return []

    rel = text(doc.get("local_path"))
    if not rel:
        return [f"{did}: RETRIEVED with no local_path"]
    if not rel.replace("\\", "/").startswith("source_material/official/"):
        return [f"{did}: local_path {rel!r} is outside source_material/official/"]

    path = root / rel
    if not path.is_file():
        return [f"{did}: local_path {rel!r} does not exist on disk"]

    recorded = text(doc.get("sha256"))
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if recorded != actual:
        return [
            f"{did}: sha256 mismatch — registry says {recorded or '<empty>'}, "
            f"the bytes at {rel} hash to {actual}"
        ]
    return []


def check_current_record(record: dict, retrieved_ids: set[str]) -> list[str]:
    """Return every problem with one record in the current_official registry.

    This is the database row behind OFF-F09's resolution: the reconciliation of
    the base notification (DOC-OFF-002) with the supplementary one (DOC-OFF-003).
    A record here, like a fact, must be sourced, cited to a retrieved document,
    carry a verbatim quote, and — if it is a derived reading — label itself as
    derived rather than as a freshly stated official figure.
    """
    rid = record.get("record_id", "<missing record_id>")
    required = (
        "record_id", "kind", "title", "value",
        "provenance", "provenance_tier", "verification",
    )
    missing = [k for k in required if k not in record]
    if missing:
        return [f"{rid}: missing field(s) {', '.join(missing)}"]

    p = []
    if record["provenance_tier"] != "T1_OFFICIAL":
        p.append(f"{rid}: provenance_tier is {record['provenance_tier']!r}, must be T1_OFFICIAL")
    if record.get("value") is None:
        p.append(f"{rid}: record holds no value")
    prov = record["provenance"] or {}
    doc_id = prov.get("document_id")
    if not doc_id:
        p.append(f"{rid}: no provenance document — an unsupported claim")
    elif doc_id not in retrieved_ids:
        p.append(f"{rid}: provenance cites {doc_id}, which is not a retrieved document")
    if not text(prov.get("quote")):
        p.append(f"{rid}: holds a value with no verbatim quote")

    if record["kind"] == "derived":
        value = record["value"] or {}
        if not text(value.get("derivation")):
            p.append(f"{rid}: derived record carries no derivation label")
        if not text(value.get("reading")):
            p.append(f"{rid}: derived record carries no reading")

    method = (record["verification"] or {}).get("method")
    if method not in CURRENT_ACCEPTED_METHODS:
        p.append(
            f"{rid}: verification method {method!r} is not an accepted independent method"
        )
    return p


def check_current_reconciliation(rec: dict) -> list[str]:
    """Return every problem with the notification-to-supplementary reconciliation.

    Two invariants matter here. First, an *additive* amendment (a relaxation added
    on top of an existing reading) is not a conflict — recording it as a
    contradiction would mislabel the relationship. Second, a governing figure that
    exists only after adding sourced components must be presented as derived, never
    as a verbatim official number.
    """
    p = []
    for k in ("question_answered", "base_document", "supplementary_document",
              "reconciliation_summary"):
        if not text(rec.get(k)):
            p.append(f"reconciliation missing field {k}")
    if not rec.get("current_reading"):
        p.append("reconciliation missing field current_reading")

    records = rec.get("records") or []
    if not records:
        p.append("reconciliation has no records")

    derived = [r for r in records if r.get("kind") == "derived"]
    if not derived:
        p.append("no derived record states the governing reading")
    for r in derived:
        value = r.get("value") or {}
        if not text(value.get("derivation")):
            p.append(f"{r.get('record_id')}: derived record has no derivation label")
        if not text(value.get("reading")):
            p.append(f"{r.get('record_id')}: derived record has no reading")

    for r in records:
        if r.get("kind") == "reconciliation":
            conflict = text((r.get("value") or {}).get("conflict"))
            if conflict in ("contradiction", "conflict"):
                p.append(
                    f"{r.get('record_id')}: additive amendment recorded as a contradiction"
                )
    return p


def official_host(url: str) -> bool:
    """True only for hosts belonging to the recruitment board (SPEC-OFF-001 R1)."""
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ("tgprb.in", "tslprb.in"))


def norm(s: str) -> str:
    """Collapse whitespace, so a quote wrapped across lines still matches."""
    return " ".join(s.split())


def manifest_paths() -> list[Path]:
    return sorted((ROOT / MANIFEST_DIR).glob("*.json"))


class TestOfficialSourceRecordsExist(unittest.TestCase):
    """Requirement 1 — official source records exist, and describe real documents."""

    def setUp(self):
        self.registry = load(DOC_REGISTRY)
        self.docs = self.registry["documents"]

    def test_registry_holds_at_least_one_official_document(self):
        self.assertTrue(self.docs, f"{DOC_REGISTRY} registers no official document")

    def test_every_document_record_is_well_formed(self):
        problems = [p for d in self.docs for p in check_document(d)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_document_ids_are_unique(self):
        ids = [d["document_id"] for d in self.docs]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], dupes, f"duplicate document_id(s): {dupes}")

    def test_retrieved_count_matches_the_records(self):
        self.assertEqual(
            len(retrieved_document_ids(self.registry)),
            self.registry["retrieved_count"],
            "registry retrieved_count disagrees with the records it contains",
        )

    def test_every_registered_url_is_on_an_official_host(self):
        strays = [
            (d["document_id"], d["url"]) for d in self.docs if not official_host(d["url"])
        ]
        self.assertEqual(
            [], strays,
            f"registered as official authority but not on a board domain: {strays}",
        )

    def test_every_document_appears_in_the_source_ledger(self):
        ledger = read("SOURCE_LEDGER.md")
        absent = [d["document_id"] for d in self.docs if d["document_id"] not in ledger]
        self.assertEqual(
            [], absent,
            f"registered documents missing from SOURCE_LEDGER.md: {absent}",
        )

    def test_retrieval_log_records_the_attempt_history(self):
        log = read(RETRIEVAL_LOG)
        self.assertGreater(len(log), 500, f"{RETRIEVAL_LOG} is too thin to be a record")

    def test_an_acquisition_manifest_exists(self):
        self.assertTrue(manifest_paths(), f"no acquisition manifest under {MANIFEST_DIR}")


class TestOfficialSyllabusIsFullyMapped(unittest.TestCase):
    """Requirement 2 — every official syllabus item is mapped, placed and sourced."""

    def setUp(self):
        self.syllabus = load(SYLLABUS)
        self.nodes = self.syllabus["nodes"]
        self.by_id = {n.get("node_id"): n for n in self.nodes}
        self.retrieved = retrieved_document_ids(load(DOC_REGISTRY))

    def test_record_count_matches_the_nodes_present(self):
        self.assertEqual(
            len(self.nodes), self.syllabus["record_count"],
            "syllabus record_count disagrees with the nodes in the file",
        )

    def test_node_ids_are_unique(self):
        ids = [n.get("node_id") for n in self.nodes]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual([], dupes, f"duplicate node_id(s): {dupes}")

    def test_every_node_is_well_formed_placed_and_sourced(self):
        problems = [
            p for n in self.nodes for p in check_syllabus_node(n, self.by_id, self.retrieved)
        ]
        self.assertEqual([], problems, "\n".join(problems))

    def test_sibling_ordinals_are_contiguous_from_one(self):
        """A gap in a parent's ordinals means a listed item was skipped, not mapped."""
        groups: dict = {}
        for n in self.nodes:
            groups.setdefault(n.get("parent_id"), []).append(n.get("ordinal"))
        problems = []
        for parent, ordinals in groups.items():
            got = sorted(o for o in ordinals if isinstance(o, int))
            want = list(range(1, len(ordinals) + 1))
            if got != want:
                problems.append(f"under parent {parent!r}: ordinals {got} != {want}")
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_node_reaches_a_subject_root(self):
        problems = []
        for n in self.nodes:
            seen, cur = [], n
            while cur is not None and cur.get("parent_id") is not None:
                nid = cur.get("node_id")
                if nid in seen:
                    problems.append(f"{n.get('node_id')}: parent chain cycles at {nid}")
                    break
                seen.append(nid)
                cur = self.by_id.get(cur.get("parent_id"))
            else:
                if cur is None:
                    problems.append(f"{n.get('node_id')}: parent chain breaks before a subject")
        self.assertEqual([], problems, "\n".join(problems))

    def test_an_empty_syllabus_states_why_it_is_empty(self):
        if self.nodes:
            self.skipTest("syllabus is populated; emptiness rules do not apply")
        self.assertEqual("BLOCKED", self.syllabus["status"])
        self.assertGreater(
            len(text(self.syllabus.get("blocked_reason"))), 20,
            "an empty official syllabus must record why it is empty",
        )
        self.assertEqual(
            set(), self.retrieved,
            "no syllabus nodes exist even though an official document was retrieved",
        )


class TestEveryOfficialFactHasProvenance(unittest.TestCase):
    """Requirement 3 — no official fact carries a value without a traceable source."""

    def setUp(self):
        self.doc = load(FACTS)
        self.facts = self.doc["facts"]
        self.registry = load(DOC_REGISTRY)
        self.retrieved = retrieved_document_ids(self.registry)
        self.registered = {d.get("document_id") for d in self.registry["documents"]}

    def test_all_twenty_five_required_facts_are_present_exactly_once(self):
        ids = [f.get("fact_id") for f in self.facts]
        self.assertEqual(
            REQUIRED_FACT_IDS, sorted(ids),
            f"missing: {sorted(set(REQUIRED_FACT_IDS) - set(ids))}; "
            f"unexpected: {sorted(set(ids) - set(REQUIRED_FACT_IDS))}",
        )

    def test_every_fact_record_is_well_formed_and_sourced(self):
        problems = [p for f in self.facts for p in check_fact(f, self.retrieved)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_declared_counts_match_the_records(self):
        self.assertEqual(len(self.facts), self.doc["record_count"], "record_count is wrong")
        self.assertEqual(
            sum(1 for f in self.facts if f.get("status") == "VERIFIED"),
            self.doc["verified_count"],
            "verified_count disagrees with the statuses in the file",
        )

    def test_every_expected_document_is_registered(self):
        strays = sorted(
            {
                f.get("expected_document")
                for f in self.facts
                if f.get("expected_document") not in self.registered
            }
        )
        self.assertEqual(
            [], strays,
            f"facts expect documents that are not registered: {strays}",
        )

    def test_registry_expectations_name_real_facts(self):
        known = set(REQUIRED_FACT_IDS)
        strays = sorted(
            {
                fid
                for d in self.registry["documents"]
                for fid in d.get("expected_content", [])
                if fid not in known
            }
        )
        self.assertEqual([], strays, f"registry expects unknown fact ids: {strays}")

    def test_the_whole_fact_set_declares_its_status(self):
        self.assertIn(self.doc["status"], ("BLOCKED", "PARTIAL", "COMPLETE", "UNVERIFIED"))
        if self.doc["status"] != "COMPLETE":
            reason = text(
                self.doc.get("blocked_reason") or self.doc.get("partial_reason")
            )
            self.assertGreater(
                len(reason), 20,
                "a fact set that is not COMPLETE must say what is missing",
            )


BOOKKEEPING_FILES = {".gitkeep", "README.md", "RETRIEVAL_LOG.md"}


class TestNoUnsupportedOfficialClaim(unittest.TestCase):
    """Requirement 4 — an official claim exists only if bytes on disk back it."""

    def setUp(self):
        self.registry = load(DOC_REGISTRY)
        self.docs = self.registry["documents"]
        self.by_id = {d.get("document_id"): d for d in self.docs}
        self.facts = load(FACTS)["facts"]
        self.retrieved = retrieved_document_ids(self.registry)

    def test_every_retrieved_document_hashes_to_its_recorded_digest(self):
        problems = [p for d in self.docs for p in check_stored_bytes(d, ROOT)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_file_in_the_official_folder_is_a_registered_document(self):
        """The other direction: a PDF nobody registered is an unaccounted claim."""
        folder = ROOT / "source_material" / "official"
        stored = {
            str(p.relative_to(ROOT)).replace("\\", "/")
            for p in folder.rglob("*")
            if p.is_file() and p.name not in BOOKKEEPING_FILES
        }
        registered = {
            text(d.get("local_path")).replace("\\", "/")
            for d in self.docs
            if text(d.get("local_path"))
        }
        self.assertEqual(
            set(), stored - registered,
            f"files present with no registry entry: {sorted(stored - registered)}",
        )

    def test_a_fact_with_a_value_names_a_document_whose_bytes_exist(self):
        problems = []
        for f in self.facts:
            if f.get("value") is None:
                continue
            did = (f.get("provenance") or {}).get("document_id")
            doc = self.by_id.get(did)
            if doc is None:
                problems.append(f"{f.get('fact_id')}: cites unregistered document {did!r}")
                continue
            problems += [f"{f.get('fact_id')} -> {p}" for p in check_stored_bytes(doc, ROOT)]
            if did not in self.retrieved:
                problems.append(f"{f.get('fact_id')}: cites {did}, which is not RETRIEVED")
        self.assertEqual([], problems, "\n".join(problems))

    def test_with_no_document_retrieved_nothing_official_is_populated(self):
        if self.retrieved:
            self.skipTest("a document has been retrieved; the empty-state rules do not apply")
        valued = [f["fact_id"] for f in self.facts if f.get("value") is not None]
        self.assertEqual([], valued, f"facts hold values with no document retrieved: {valued}")
        self.assertEqual([], load(SYLLABUS)["nodes"], "syllabus nodes exist with no document")
        marks = load(WEIGHTAGE["official_marks_structure"])
        self.assertEqual([], marks["entries"], "official marks entries exist with no document")

    def test_official_marks_entries_are_each_sourced(self):
        marks = load(WEIGHTAGE["official_marks_structure"])
        problems = []
        for e in marks["entries"]:
            did = (e.get("provenance") or {}).get("document_id")
            if did not in self.retrieved:
                problems.append(f"marks entry {e.get('entry_id', e)!r} cites {did!r}")
        self.assertEqual([], problems, "\n".join(problems))


DECLARED_TIERS = {
    "official_marks_structure": "T1_OFFICIAL",
    "historical_observed": "T2_HISTORICAL_PYQ",
    "estimated_priority": "T4_AI",
}


class TestOfficialAndInferredStaySeparated(unittest.TestCase):
    """Requirement 5 — official, historical, expert and AI content never mix."""

    def test_preparation_taxonomy_forbids_the_official_tier(self):
        t = load(PREP_TAXONOMY)
        self.assertEqual("T1_OFFICIAL", t["forbidden_tier"])
        self.assertEqual(sorted(NON_OFFICIAL_TIERS), sorted(t["permitted_tiers"]))

    def test_every_preparation_node_is_non_official_and_anchored(self):
        t = load(PREP_TAXONOMY)
        official_ids = {n.get("node_id") for n in load(SYLLABUS)["nodes"]}
        problems = [p for n in t["nodes"] for p in check_prep_node(n, official_ids)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_the_three_weightage_categories_are_separate_files_with_fixed_tiers(self):
        for key, rel in WEIGHTAGE.items():
            with self.subTest(category=key):
                data = load(rel)
                self.assertEqual(
                    DECLARED_TIERS[key], data["provenance_tier"],
                    f"{rel} declares the wrong tier for its category",
                )

    def test_no_weightage_entry_carries_a_tier_other_than_its_files_own(self):
        problems = []
        for key, rel in WEIGHTAGE.items():
            expected = DECLARED_TIERS[key]
            for e in load(rel)["entries"]:
                tier = e.get("provenance_tier", expected)
                if tier != expected:
                    problems.append(f"{rel}: entry claims {tier!r}, file is {expected!r}")
        self.assertEqual([], problems, "\n".join(problems))

    def test_official_knowledge_files_all_declare_the_official_tier(self):
        for rel in (FACTS, SYLLABUS):
            with self.subTest(file=rel):
                self.assertEqual("T1_OFFICIAL", load(rel)["provenance_tier"])

    def test_an_inferred_url_is_never_also_a_retrieved_document(self):
        """Retrieval confirms a URL. Claiming both states at once hides which is true."""
        bad = [
            d["document_id"]
            for d in load(DOC_REGISTRY)["documents"]
            if d.get("url_status") == "INFERRED_UNVERIFIED"
            and d.get("retrieval_status") == "RETRIEVED"
        ]
        self.assertEqual(
            [], bad,
            f"documents both inferred and retrieved — resolve url_status first: {bad}",
        )

    def test_excluded_source_types_are_declared_and_include_the_obvious_ones(self):
        excluded = load(DOC_REGISTRY)["excluded_source_types"]["types"]
        for kind in ("coaching_website", "youtube", "telegram", "blog", "search_result_summary"):
            with self.subTest(kind=kind):
                self.assertIn(kind, excluded)


PHASE1_ARTEFACTS = (DOC_REGISTRY, FACTS, SYLLABUS, PREP_TAXONOMY, RETRIEVAL_LOG, *WEIGHTAGE.values())


class TestBlockedSourcesAreRecordedExplicitly(unittest.TestCase):
    """Requirement 6 — what could not be obtained is written down, not passed over."""

    def setUp(self):
        self.registry = load(DOC_REGISTRY)
        self.docs = self.registry["documents"]
        self.manifests = [json.loads(p.read_text(encoding="utf-8")) for p in manifest_paths()]

    def test_every_manifest_balances_the_accounting_identity(self):
        problems = [p for m in self.manifests for p in check_accounting(m)]
        self.assertEqual([], problems, "\n".join(problems))

    def test_item_lists_match_their_counts(self):
        problems = []
        for m in self.manifests:
            a = m["accounting"]
            for key, field in (("inaccessible", "inaccessible_items"), ("irrelevant", "irrelevant_items")):
                listed = len(m.get(field, []))
                if listed != a[key]:
                    problems.append(
                        f"{m['manifest_id']}: {field} lists {listed} but {key} counts {a[key]}"
                    )
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_unretrieved_document_is_named_in_a_manifest(self):
        listed = {
            i.get("document_id") for m in self.manifests for i in m.get("inaccessible_items", [])
        }
        missing = [
            d["document_id"]
            for d in self.docs
            if d.get("retrieval_status") != "RETRIEVED" and d["document_id"] not in listed
        ]
        self.assertEqual(
            [], missing,
            f"documents not obtained and not accounted for in any manifest: {missing}",
        )

    def test_deliberately_unregistered_urls_are_counted_as_irrelevant(self):
        counted = {i.get("url") for m in self.manifests for i in m.get("irrelevant_items", [])}
        missing = [
            n["url"] for n in self.registry.get("not_registered", []) if n["url"] not in counted
        ]
        self.assertEqual(
            [], missing,
            f"urls set aside in the registry but absent from the accounting: {missing}",
        )

    def test_every_unresolved_conflict_names_what_would_settle_it(self):
        problems = []
        for c in self.registry.get("conflicts", []):
            cid = c.get("conflict_id", "<no id>")
            for field in ("question", "observation", "why_it_matters", "resolution_rule"):
                if len(text(c.get(field))) < 20:
                    problems.append(f"{cid}: {field} is missing or too thin")
            if c.get("status") == "UNRESOLVED" and not text(c.get("blocked_by")):
                problems.append(f"{cid}: UNRESOLVED with no blocker recorded")
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_recorded_attempt_appears_verbatim_in_the_retrieval_log(self):
        log = norm(read(RETRIEVAL_LOG))
        problems = []
        for d in self.docs:
            for a in d.get("attempts", []):
                if a["url"] not in log:
                    problems.append(f"{d['document_id']}: attempt url absent from the log")
                if norm(a["response"]) not in log:
                    problems.append(
                        f"{d['document_id']}: attempt response not recorded verbatim in the log"
                    )
        self.assertEqual([], sorted(set(problems)), "\n".join(sorted(set(problems))))

    def test_every_blocker_referenced_is_declared_in_project_state(self):
        state = read("PROJECT_STATE.md")
        referenced = set()
        for rel in PHASE1_ARTEFACTS:
            referenced |= set(re.findall(r"\bB-\d{2}\b", read(rel)))
        for path in manifest_paths():
            referenced |= set(re.findall(r"\bB-\d{2}\b", path.read_text(encoding="utf-8")))
        missing = sorted(b for b in referenced if b not in state)
        self.assertEqual(
            [], missing,
            f"blockers cited by Phase-1 records but absent from PROJECT_STATE.md: {missing}",
        )


DIGEST = "a" * 64


def good_document(**over) -> dict:
    d = {
        "document_id": "DOC-OFF-009",
        "title": "SI 2026 Notification",
        "publisher": "TGPRB / TSLPRB",
        "url": "https://www.tgprb.in/SI_PC_2026/x.pdf",
        "url_status": "OBSERVED_ON_OFFICIAL_DOMAIN",
        "url_basis": "Observed on the official domain by a search restricted to it.",
        "document_type": "notification",
        "expected_content": ["OFF-F01"],
        "retrieval_status": "RETRIEVED",
        "attempts": [],
        "local_path": "source_material/official/x.pdf",
        "sha256": DIGEST,
        "document_date": "2026-07-29",
        "retrieved_on": "2026-09-06",
    }
    d.update(over)
    return d


def good_fact(**over) -> dict:
    f = {
        "fact_id": "OFF-F01",
        "name": "Notification number",
        "must_capture": "The Rc. number exactly as printed on the document.",
        "value": "Rc. No. 1/2026",
        "value_te": None,
        "status": "VERIFIED",
        "provenance_tier": "T1_OFFICIAL",
        "provenance": {
            "document_id": "DOC-OFF-009", "page": 1,
            "section": "Preamble", "quote": "Rc. No. 1/2026",
        },
        "verification": {
            "method": "SOURCE_DOCUMENT", "verified_on": "2026-09-06",
            "verified_by": "session 003",
        },
    }
    f.update(over)
    return f


def good_node(**over) -> dict:
    n = {
        "node_id": "OFF-SYL-0001", "level": "subject", "parent_id": None,
        "title": "Arithmetic", "title_te": None, "ordinal": 1,
        "provenance_tier": "T1_OFFICIAL",
        "provenance": {
            "document_id": "DOC-OFF-009", "page": 7,
            "section": "Annexure II", "quote": "Arithmetic",
        },
        "verification": {
            "method": "SOURCE_DOCUMENT", "verified_on": "2026-09-06",
            "verified_by": "session 003",
        },
    }
    n.update(over)
    return n


def good_prep_node(**over) -> dict:
    n = {
        "node_id": "PREP-0001", "title": "Percentage shortcuts", "title_te": None,
        "official_anchor": "OFF-SYL-0001",
        "anchor_justification": "Sits under the official Arithmetic subject heading.",
        "provenance_tier": "T3_EXPERT", "derived_from": ["SRC-0001"],
    }
    n.update(over)
    return n


class TestCheckersRejectFabrication(unittest.TestCase):
    """AC-7 — prove the checkers above can fail.

    Every check in this file currently runs over empty or blocked records, where
    passing is easy. These tests feed the same checkers deliberately fabricated
    records and require a complaint. Without them, a green suite would be evidence
    of nothing.
    """

    RETRIEVED = {"DOC-OFF-009"}

    def assertRejected(self, problems, fragment: str):
        self.assertTrue(problems, f"fabricated record accepted; expected a complaint about {fragment!r}")
        joined = " | ".join(problems).lower()
        self.assertIn(fragment.lower(), joined, f"complaint was {joined!r}")

    def test_a_clean_record_set_is_accepted(self):
        """The other half of the proof: these checkers are not simply always failing."""
        self.assertEqual([], check_document(good_document(sha256=DIGEST)))
        self.assertEqual([], check_fact(good_fact(), self.RETRIEVED))
        node = good_node()
        self.assertEqual([], check_syllabus_node(node, {node["node_id"]: node}, self.RETRIEVED))
        self.assertEqual([], check_prep_node(good_prep_node(), {"OFF-SYL-0001"}))

    def test_a_value_with_no_provenance_document_is_rejected(self):
        fact = good_fact(provenance={"document_id": None, "page": None, "section": None, "quote": None})
        self.assertRejected(check_fact(fact, self.RETRIEVED), "unsupported claim")

    def test_a_value_citing_an_unretrieved_document_is_rejected(self):
        fact = good_fact(provenance=dict(good_fact()["provenance"], document_id="DOC-OFF-002"))
        self.assertRejected(check_fact(fact, self.RETRIEVED), "not a retrieved document")

    def test_a_value_with_no_verbatim_quote_is_rejected(self):
        fact = good_fact(provenance=dict(good_fact()["provenance"], quote="  "))
        self.assertRejected(check_fact(fact, self.RETRIEVED), "no verbatim quote")

    def test_self_review_is_not_accepted_as_verification(self):
        fact = good_fact(verification={"method": "SELF_REVIEW", "verified_on": "2026-09-06", "verified_by": "me"})
        self.assertRejected(check_fact(fact, self.RETRIEVED), "self-review is not a")

    def test_a_value_held_while_still_blocked_is_rejected(self):
        fact = good_fact(status="BLOCKED")
        self.assertRejected(check_fact(fact, self.RETRIEVED), "holds a value while status is")

    def test_an_upgraded_tier_on_an_official_fact_is_rejected(self):
        fact = good_fact(provenance_tier="T3_EXPERT")
        self.assertRejected(check_fact(fact, self.RETRIEVED), "must be t1_official")

    def test_a_verified_fact_with_no_value_is_rejected(self):
        fact = good_fact(value=None, blocked_reason="")
        self.assertRejected(check_fact(fact, self.RETRIEVED), "verified with no value")


    def test_a_retrieved_document_with_no_hash_is_rejected(self):
        self.assertRejected(check_document(good_document(sha256="")), "sha256 is empty")

    def test_a_truncated_hash_is_rejected(self):
        self.assertRejected(check_document(good_document(sha256="abc123")), "64-character hex")

    def test_a_blocked_document_with_no_attempt_is_rejected(self):
        doc = good_document(
            retrieval_status="BLOCKED", blocked_reason="Host refused by the egress allowlist.",
            local_path=None, sha256=None, retrieved_on=None, attempts=[],
        )
        self.assertRejected(check_document(doc), "no recorded attempt")

    def test_a_blocked_document_with_no_reason_is_rejected(self):
        doc = good_document(
            retrieval_status="BLOCKED", local_path=None, sha256=None, retrieved_on=None,
            attempts=[{"timestamp": "t", "tool": "fetch", "url": "https://x", "response": "refused"}],
        )
        self.assertRejected(check_document(doc), "no blocked_reason")

    def test_an_unretrieved_document_claiming_stored_bytes_is_rejected(self):
        doc = good_document(
            retrieval_status="BLOCKED", blocked_reason="Host refused by the egress allowlist.",
            attempts=[{"timestamp": "t", "tool": "fetch", "url": "https://x", "response": "refused"}],
        )
        self.assertRejected(check_document(doc), "claims stored bytes")

    def test_an_inferred_url_with_no_recorded_basis_is_rejected(self):
        self.assertRejected(check_document(good_document(url_basis="guessed")), "url_basis")

    def test_a_syllabus_node_with_no_source_document_is_rejected(self):
        node = good_node(provenance={"document_id": None, "page": None, "section": None, "quote": None})
        self.assertRejected(
            check_syllabus_node(node, {node["node_id"]: node}, self.RETRIEVED),
            "unsourced syllabus node",
        )

    def test_a_syllabus_node_citing_an_unretrieved_document_is_rejected(self):
        node = good_node(provenance=dict(good_node()["provenance"], document_id="DOC-OFF-002"))
        self.assertRejected(
            check_syllabus_node(node, {node["node_id"]: node}, self.RETRIEVED),
            "not a retrieved document",
        )

    def test_a_subject_with_a_parent_is_rejected(self):
        node = good_node(parent_id="OFF-SYL-0002")
        self.assertRejected(
            check_syllabus_node(node, {node["node_id"]: node}, self.RETRIEVED),
            "must have parent_id null",
        )

    def test_a_subtopic_hung_directly_off_a_subject_is_rejected(self):
        subject = good_node()
        sub = good_node(node_id="OFF-SYL-0002", level="subtopic", parent_id="OFF-SYL-0001")
        by_id = {subject["node_id"]: subject, sub["node_id"]: sub}
        self.assertRejected(check_syllabus_node(sub, by_id, self.RETRIEVED), "expected a 'topic'")

    def test_a_node_whose_parent_does_not_exist_is_rejected(self):
        node = good_node(node_id="OFF-SYL-0003", level="topic", parent_id="OFF-SYL-0099")
        self.assertRejected(
            check_syllabus_node(node, {node["node_id"]: node}, self.RETRIEVED), "does not exist"
        )


    def test_an_official_tier_in_the_preparation_taxonomy_is_rejected(self):
        node = good_prep_node(provenance_tier="T1_OFFICIAL")
        self.assertRejected(check_prep_node(node, {"OFF-SYL-0001"}), "wearing an official label")

    def test_a_preparation_node_with_no_traceable_origin_is_rejected(self):
        self.assertRejected(
            check_prep_node(good_prep_node(derived_from=[]), {"OFF-SYL-0001"}), "derived_from is empty"
        )

    def test_a_preparation_node_anchored_to_nothing_real_is_rejected(self):
        node = good_prep_node(official_anchor="OFF-SYL-9999")
        self.assertRejected(check_prep_node(node, {"OFF-SYL-0001"}), "no_official_anchor")

    def test_an_unbalanced_manifest_is_rejected(self):
        m = {
            "manifest_id": "M-1", "expected": 7,
            "expected_justification": "Counted from an enumerated candidate list.",
            "accounting": {"processed": 1, "inaccessible": 1, "irrelevant": 0, "duplicate": 0, "failed": 0},
        }
        self.assertRejected(check_accounting(m), "identity broken")

    def test_an_expected_count_with_no_basis_is_rejected(self):
        m = {
            "manifest_id": "M-2", "expected": 2, "expected_justification": "about right",
            "accounting": {"processed": 2, "inaccessible": 0, "irrelevant": 0, "duplicate": 0, "failed": 0},
        }
        self.assertRejected(check_accounting(m), "estimate posing as a count")

    def test_a_blocked_manifest_claiming_processed_items_is_rejected(self):
        m = {
            "manifest_id": "M-3", "expected": 1, "status": "blocked",
            "expected_justification": "Counted from an enumerated candidate list.",
            "accounting": {"processed": 1, "inaccessible": 0, "irrelevant": 0, "duplicate": 0, "failed": 0},
        }
        self.assertRejected(check_accounting(m), "while claiming processed")

    def test_a_balanced_manifest_is_accepted(self):
        m = {
            "manifest_id": "M-4", "expected": 2, "status": "blocked",
            "expected_justification": "Counted from an enumerated candidate list.",
            "accounting": {"processed": 0, "inaccessible": 2, "irrelevant": 0, "duplicate": 0, "failed": 0},
        }
        self.assertEqual([], check_accounting(m))

    def test_a_hash_that_does_not_match_the_bytes_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source_material" / "official").mkdir(parents=True)
            (root / "source_material" / "official" / "x.pdf").write_bytes(b"official bytes")
            self.assertRejected(check_stored_bytes(good_document(), root), "sha256 mismatch")
            real = hashlib.sha256(b"official bytes").hexdigest()
            self.assertEqual([], check_stored_bytes(good_document(sha256=real), root))

    def test_a_document_whose_file_is_absent_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertRejected(check_stored_bytes(good_document(), Path(tmp)), "does not exist on disk")

    def test_a_stored_file_outside_the_official_folder_is_rejected(self):
        doc = good_document(local_path="data/raw/x.pdf")
        self.assertRejected(check_stored_bytes(doc, ROOT), "outside source_material/official/")

    def test_a_coaching_domain_is_not_an_official_host(self):
        self.assertFalse(official_host("https://www.somecoaching.com/tgprb.in/notification.pdf"))
        self.assertFalse(official_host("https://tgprb.in.example.com/notification.pdf"))
        self.assertTrue(official_host("https://www.tgprb.in/SI_PC_2026/x.pdf"))
        self.assertTrue(official_host("https://tslprb.in/"))


def good_current_record(kind="base_document", **overrides) -> dict:
    record = {
        "record_id": "REC-900",
        "kind": kind,
        "title": "A reconciliation record",
        "value": {"note": "something"},
        "provenance": {
            "document_id": "DOC-OFF-002", "page": 16,
            "section": "Para 15-B (i)", "quote": "a verbatim quote from that page",
        },
        "provenance_tier": "T1_OFFICIAL",
        "verification": {"method": "SOURCE_DOCUMENT"},
    }
    record.update(overrides)
    return record


def good_reconciliation(records) -> dict:
    return {
        "question_answered": "How do the two notifications reconcile?",
        "base_document": "DOC-OFF-002 — base notification",
        "supplementary_document": "DOC-OFF-003 — supplementary notification",
        "reconciliation_summary": "The supplementary amends only the age paragraph; it does not contradict the base.",
        "current_reading": {"age": {"x": 1}, "everything_else": "governed by the base"},
        "records": records,
    }


class TestCurrentOfficialReconciliation(unittest.TestCase):
    """Requirement 3 (reconcile the supplementary against the original) — the
    registry that answers OFF-F09's `current_official_resolution`."""

    @classmethod
    def setUpClass(cls):
        cls.rec = load(CURRENT)
        cls.retrieved = retrieved_document_ids(load(DOC_REGISTRY))

    def test_every_record_is_well_formed_and_sourced(self):
        problems = [
            p for r in self.rec["records"]
            for p in check_current_record(r, self.retrieved)
        ]
        self.assertEqual([], problems, "\n".join(problems))

    def test_reconciliation_metadata_is_complete(self):
        self.assertEqual([], check_current_reconciliation(self.rec))

    def test_both_documents_are_retrieved(self):
        for doc in (self.rec["base_document"], self.rec["supplementary_document"]):
            did = doc.split(" — ")[0].strip()
            self.assertIn(did, self.retrieved, f"{did} is not a retrieved document")

    def test_record_counts_are_consistent(self):
        records = self.rec["records"]
        verified = [r for r in records if (r.get("verification") or {}).get("method")]
        self.assertEqual(self.rec["record_count"], len(records), "record_count mismatch")
        self.assertEqual(self.rec["verified_count"], len(verified), "verified_count mismatch")

    def test_derived_upper_limit_is_arithmetic_over_sourced_components(self):
        derived = [r for r in self.rec["records"] if r.get("kind") == "derived"]
        self.assertTrue(derived, "no derived record found")
        value = derived[0]["value"]
        total = (
            value["base_maximum_age_years"]
            + value["raise_go87_years"]
            + value["raise_go122_years"]
        )
        self.assertEqual(
            total, value["effective_general_upper_limit_years"],
            "derived arithmetic does not recompute",
        )
        self.assertIn(str(total), value["reading"],
                      "the derived reading does not state the computed figure")

    def test_the_supplementary_only_amends_age(self):
        age = self.rec["current_reading"]["age"]
        self.assertIn("21", age["minimum_age"])
        self.assertIn("32", age["general_upper_limit"])
        everything_else = self.rec["current_reading"]["everything_else"]
        self.assertIn("DOC-OFF-002", everything_else,
                      "the base document is expected to govern everything else")


class TestCurrentOfficialRejectsFabrication(unittest.TestCase):
    """Anti-vacuity: the reconciliation checkers must reject poisoned records."""

    def assertRejected(self, problems, needle):
        self.assertTrue(problems, "checker accepted a fabricated record")
        self.assertTrue(
            any(needle in p for p in problems),
            f"expected {needle!r} in problems, got: {problems}",
        )

    def setUp(self):
        self.RETRIEVED = {"DOC-OFF-002", "DOC-OFF-003"}

    def test_an_unsourced_current_record_is_rejected(self):
        self.assertRejected(
            check_current_record(
                good_current_record(provenance={"document_id": None}), self.RETRIEVED),
            "no provenance document",
        )

    def test_a_current_record_citing_an_unretrieved_document_is_rejected(self):
        self.assertRejected(
            check_current_record(
                good_current_record(provenance={"document_id": "DOC-OFF-999"}),
                self.RETRIEVED),
            "not a retrieved document",
        )

    def test_a_current_record_with_a_non_official_tier_is_rejected(self):
        self.assertRejected(
            check_current_record(
                good_current_record(provenance_tier="T3_EXPERT"), self.RETRIEVED),
            "must be T1_OFFICIAL",
        )

    def test_a_derived_record_with_no_derivation_label_is_rejected(self):
        rec = good_current_record(kind="derived", value={"reading": "32 years"})
        self.assertRejected(check_current_record(rec, self.RETRIEVED), "derivation label")

    def test_a_derived_record_verified_by_an_invalid_method_is_rejected(self):
        rec = good_current_record(
            kind="derived",
            value={"reading": "32", "derivation": "DETERMINISTIC"},
            verification={"method": "self-review"},
        )
        self.assertRejected(check_current_record(rec, self.RETRIEVED), "not an accepted")

    def test_an_additive_amendment_recorded_as_a_conflict_is_rejected(self):
        rec = good_reconciliation([
            {"record_id": "R-1", "kind": "reconciliation",
             "value": {"conflict": "contradiction", "nature": "additive relaxation"}},
        ])
        self.assertRejected(check_current_reconciliation(rec), "contradiction")

    def test_a_reconciliation_with_no_derived_reading_is_rejected(self):
        rec = good_reconciliation([
            {"record_id": "R-1", "kind": "base_document", "value": {"x": 1}},
        ])
        self.assertRejected(check_current_reconciliation(rec), "no derived record")


if __name__ == "__main__":
    unittest.main()















