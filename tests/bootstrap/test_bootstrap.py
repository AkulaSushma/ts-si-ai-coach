"""L0 structural tests for the Telangana SI 2026 coaching system.

These assert the bootstrap acceptance criteria in TEST_PLAN.md independently of
scripts/validate_bootstrap.py, then additionally confirm that the validator itself
both passes on a valid repository and fails on a broken one.

Standard library only (decision D-0006). Run from the project folder:

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GOVERNANCE_FILES = [
    "CLAUDE.md", "PROJECT_STATE.md", "TASK_LEDGER.md", "DECISIONS.md",
    "KNOWLEDGE_LEDGER.md", "SOURCE_LEDGER.md", "VERIFICATION_POLICY.md",
    "TEST_PLAN.md", "README.md",
]

TOP_LEVEL_AREAS = [
    "docs", "specs", "source_material", "research", "knowledge", "pyq",
    "expert_methods", "verification", "agents", "backend", "frontend",
    "database", "tests", "scripts", "config", "physical", "data",
]

CANONICAL_ROLES = [
    "BULK_RESEARCH", "KNOWLEDGE_EXTRACTION", "CLASSIFICATION", "SUMMARIZATION",
    "DEEP_REASONING", "CODE_GENERATION", "CODE_REVIEW", "VERIFICATION",
    "ARBITRATION",
]

SECRET_PATTERNS = [
    re.compile(r"sk-" + r"ant-api\d{2}-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bgh" + r"p_[A-Za-z0-9]{30,}"),
    re.compile(r"\bAK" + r"IA[0-9A-Z]{16}\b"),
    re.compile(r"\bAI" + r"za[0-9A-Za-z_\-]{35}\b"),
]

SCAN_EXEMPT = {"scripts/validate_bootstrap.py", "tests/bootstrap/test_bootstrap.py", ".gitignore"}
def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def routing() -> dict:
    return json.loads(read("config/model_routing.json"))


def gitignore_lines() -> list[str]:
    return [ln.strip() for ln in read(".gitignore").splitlines()]


class TestDirectoryArchitecture(unittest.TestCase):
    def test_every_top_level_area_exists(self):
        for area in TOP_LEVEL_AREAS:
            with self.subTest(area=area):
                self.assertTrue((ROOT / area).is_dir(), f"{area}/ is missing")

    def test_every_top_level_area_has_readme(self):
        for area in TOP_LEVEL_AREAS:
            with self.subTest(area=area):
                p = ROOT / area / "README.md"
                self.assertTrue(p.is_file(), f"{area}/README.md is missing")
                self.assertGreater(p.stat().st_size, 200, f"{area}/README.md is near-empty")

    def test_knowledge_subareas_exist(self):
        for sub in [
            "schemas", "syllabus", "subjects", "topics", "question_families",
            "methods", "recognition", "traps", "confusions",
        ]:
            with self.subTest(sub=sub):
                self.assertTrue((ROOT / "knowledge" / sub).is_dir())

    def test_no_required_directory_is_empty(self):
        # Git does not record empty directories, so each must hold at least a
        # .gitkeep or a README. An empty directory would silently vanish on clone.
        empties = [
            p.relative_to(ROOT).as_posix()
            for p in ROOT.rglob("*")
            if p.is_dir()
            and ".git" not in p.parts
            and "__pycache__" not in p.parts
            and not any(p.iterdir())
        ]
        self.assertEqual(empties, [], f"empty directories would be lost by git: {empties}")
class TestGovernanceFiles(unittest.TestCase):
    def test_all_nine_exist(self):
        for f in GOVERNANCE_FILES:
            with self.subTest(file=f):
                self.assertTrue((ROOT / f).is_file(), f"{f} is missing")

    def test_none_is_near_empty(self):
        for f in GOVERNANCE_FILES:
            with self.subTest(file=f):
                self.assertGreater((ROOT / f).stat().st_size, 800, f"{f} is a stub")

    def test_required_sections_present(self):
        required = {
            "CLAUDE.md": ["## 0. Read-first order", "### Status vocabulary", "## 14. Prohibited actions"],
            "PROJECT_STATE.md": ["## Snapshot", "## Component Status", "## Blockers", "## Next Action"],
            "TASK_LEDGER.md": ["## Open Tasks", "## Blocked Tasks", "## Completed Tasks"],
            "DECISIONS.md": ["## D-0001", "## Open decisions"],
            "KNOWLEDGE_LEDGER.md": ["## Current state", "## Entries"],
            "SOURCE_LEDGER.md": ["## Current state", "## Required fields", "## Entries"],
            "VERIFICATION_POLICY.md": ["## 2. Provenance tiers", "## 4. Accepted verification methods"],
            "TEST_PLAN.md": ["## Test layers", "## Non-negotiable testing rules"],
            "README.md": ["## What this project is", "## What is in each folder"],
        }
        for f, sections in required.items():
            body = read(f)
            for s in sections:
                with self.subTest(file=f, section=s):
                    self.assertIn(s, body, f"{f} lacks section '{s}'")

    def test_status_vocabulary_is_defined(self):
        body = read("CLAUDE.md")
        for token in ("`COMPLETE`", "`PARTIAL`", "`BLOCKED`"):
            self.assertIn(token, body)

    def test_provenance_tiers_defined_in_policy(self):
        body = read("VERIFICATION_POLICY.md")
        for tier in ("T1_OFFICIAL", "T2_HISTORICAL_PYQ", "T3_EXPERT", "T4_AI"):
            self.assertIn(tier, body)

    def test_self_verification_is_forbidden_in_policy(self):
        body = read("VERIFICATION_POLICY.md")
        self.assertIn("produced an output may never verify it", body)
        self.assertIn("SELF_REVIEW", body)
        self.assertIn("not** a verification method", body)

    def test_no_unresolved_placeholder_markers(self):
        hits = []
        for marker in ("PENDING_VERIFICATION", "TODO_FILL", "FIXME_BOOTSTRAP"):
            for f in GOVERNANCE_FILES:
                if marker in read(f):
                    hits.append(f"{f}:{marker}")
        self.assertEqual(hits, [], f"unresolved placeholders: {hits}")
class TestModelRouting(unittest.TestCase):
    def test_config_is_valid_json(self):
        self.assertIsInstance(routing(), dict)

    def test_all_canonical_roles_are_routed(self):
        roles = routing()["roles"]
        self.assertEqual(sorted(roles), sorted(CANONICAL_ROLES))

    def test_every_provider_reference_resolves(self):
        cfg = routing()
        providers = cfg["providers"]
        for role, spec in cfg["roles"].items():
            with self.subTest(role=role):
                prov = spec["provider"]
                if prov == "AUTO_NOT_AUTHOR":
                    cands = spec.get("candidates") or []
                    self.assertGreaterEqual(len(cands), 2)
                    for c in cands:
                        self.assertIn(c, providers)
                else:
                    self.assertIn(prov, providers)

    def test_verifier_never_shares_provider_with_author(self):
        cfg = routing()
        roles = cfg["roles"]
        pairs = cfg["independence_pairs"]
        self.assertGreater(len(pairs), 0, "independence_pairs must not be empty")
        for pair in pairs:
            a, v = pair["author_role"], pair["verifier_role"]
            with self.subTest(pair=f"{a}->{v}"):
                ap, vp = roles[a]["provider"], roles[v]["provider"]
                if vp == "AUTO_NOT_AUTHOR":
                    alternatives = [c for c in roles[v]["candidates"] if c != ap]
                    self.assertTrue(alternatives, f"no verifier other than {ap} available")
                else:
                    self.assertNotEqual(ap, vp, f"{a} and {v} both use {ap}")

    def test_code_review_provider_differs_from_code_generation(self):
        roles = routing()["roles"]
        self.assertNotEqual(roles["CODE_GENERATION"]["provider"], roles["CODE_REVIEW"]["provider"])

    def test_every_provider_reads_key_from_environment(self):
        for name, spec in routing()["providers"].items():
            with self.subTest(provider=name):
                self.assertTrue(spec.get("api_key_env"), f"{name} has no api_key_env")

    def test_arbitration_limitation_is_documented(self):
        # Only two providers exist, so a neutral arbiter is unavailable. The config
        # must say so rather than implying disputes can be resolved automatically.
        self.assertIn("arbitration_limitation", routing()["rules"])
        self.assertIn("DISPUTED", routing()["rules"]["arbitration_limitation"])
class TestSecretSafety(unittest.TestCase):
    def test_gitignore_excludes_env_and_keys(self):
        lines = gitignore_lines()
        for pat in (".env", "*.key", "*.pem", "credentials.json"):
            with self.subTest(pattern=pat):
                self.assertIn(pat, lines, f".gitignore must exclude {pat}")

    def test_gitignore_keeps_env_example(self):
        self.assertIn("!.env.example", gitignore_lines())

    def test_gitignore_excludes_runtime_database(self):
        lines = gitignore_lines()
        for pat in ("*.db", "*.sqlite3", "data/*"):
            with self.subTest(pattern=pat):
                self.assertIn(pat, lines)

    def test_data_readme_is_re_included_after_exclusion(self):
        lines = gitignore_lines()
        self.assertIn("data/*", lines)
        self.assertIn("!data/README.md", lines)
        self.assertLess(
            lines.index("data/*"),
            lines.index("!data/README.md"),
            "a negation placed before its exclusion has no effect",
        )
        self.assertTrue((ROOT / "data/README.md").is_file())

    def test_env_example_exists_with_placeholders_only(self):
        body = read(".env.example")
        self.assertIn("ANTHROPIC_API_KEY", body)
        self.assertIn("GLM_API_KEY", body)
        for pat in SECRET_PATTERNS:
            self.assertIsNone(pat.search(body), "a real-looking key is in .env.example")

    def test_no_real_env_file_present(self):
        self.assertFalse((ROOT / ".env").exists(), ".env must never be in the repository")

    def test_no_credential_pattern_anywhere_in_project(self):
        suffixes = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".sql"}
        skip = {".git", "__pycache__", "node_modules", ".venv", "venv", "data"}
        hits = []
        for p in ROOT.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in suffixes:
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel in SCAN_EXEMPT or any(part in skip for part in p.relative_to(ROOT).parts[:-1]):
                continue
            body = p.read_text(encoding="utf-8", errors="replace")
            if any(pat.search(body) for pat in SECRET_PATTERNS):
                hits.append(rel)
        self.assertEqual(hits, [], f"credential-like strings found in: {hits}")
RECORD_LIST_KEYS = ("facts", "nodes", "entries", "records", "documents")


def declared_number(body: str, label: str):
    m = re.search(re.escape(label) + r":\s*\*{0,2}\s*(\d+)", body)
    return int(m.group(1)) if m else None


def reconcile(registries: dict, stored: int, raw: int, sl: str, kl: str) -> list[str]:
    """Return every disagreement between what the ledgers claim and what exists.

    A pure function over plain data, so the tests below can feed it fabricated
    registries and prove it complains. `registries` maps a path label to already
    parsed JSON; `stored` and `raw` are counts of acquired files.
    """
    problems: list[str] = []
    verified_total = 0
    harvested = stored + raw

    for rel, data in registries.items():
        key, records = None, None
        for k in RECORD_LIST_KEYS:
            if isinstance(data.get(k), list):
                key, records = k, [r for r in data[k] if isinstance(r, dict)]
                break
        if "record_count" in data and key is None:
            problems.append(f"{rel} declares record_count but holds no record list")
            continue
        if records is None:
            continue
        if isinstance(data.get("record_count"), int) and data["record_count"] != len(records):
            problems.append(
                f"{rel} declares record_count {data['record_count']} but holds {len(records)}"
            )
        def node_is_verified(r: dict) -> bool:
            # Same two legitimate record shapes as validate_bootstrap.py: fact
            # slots carry a top-level status; syllabus nodes carry a
            # verification block whose method is set once the node is sourced.
            if r.get("status") == "VERIFIED":
                return True
            v = r.get("verification") or {}
            return isinstance(v, dict) and bool(v.get("method"))

        for r in records:
            rid = r.get("fact_id") or r.get("node_id") or r.get("entry_id") or "<no id>"
            if node_is_verified(r):
                verified_total += 1
                if not (r.get("provenance") or {}).get("document_id"):
                    problems.append(f"{rel}:{rid} is VERIFIED with no provenance document")
            if r.get("value") is not None and r.get("status") not in (None, "VERIFIED"):
                problems.append(f"{rel}:{rid} holds a value while status is {r.get('status')!r}")

    available = [ln for ln in sl.splitlines() if ln.startswith("| SRC-") and "`AVAILABLE`" in ln]
    if available and harvested == 0:
        problems.append(f"{len(available)} ledger row(s) claim AVAILABLE while nothing is stored")

    dh = declared_number(sl, "harvested items")
    if dh is None:
        problems.append("SOURCE_LEDGER.md states no 'harvested items: N' figure")
    elif dh != harvested:
        problems.append(f"SOURCE_LEDGER.md declares {dh} harvested, disk holds {harvested}")

    dv = declared_number(kl, "Verified knowledge records")
    if dv is None:
        problems.append("KNOWLEDGE_LEDGER.md states no 'Verified knowledge records: N' figure")
    elif dv != verified_total:
        problems.append(
            f"KNOWLEDGE_LEDGER.md declares {dv} verified, registries hold {verified_total}"
        )
    return problems


BOOKKEEPING = {".gitkeep", "README.md", "RETRIEVAL_LOG.md"}


class TestHonestyOfState(unittest.TestCase):
    """The project must not claim knowledge it does not have."""

    @staticmethod
    def real_registries() -> dict:
        out = {}
        for p in sorted((ROOT / "knowledge").rglob("*.json")):
            if "schemas" in p.relative_to(ROOT).parts:
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:  # a broken registry is its own failure
                raise AssertionError(f"{p.relative_to(ROOT).as_posix()}: {exc}") from exc
            if isinstance(data, dict):
                out[p.relative_to(ROOT).as_posix()] = data
        return out

    @staticmethod
    def stored_and_raw() -> tuple[int, int]:
        stored = [
            p for a in ("source_material", "pyq", "expert_methods")
            for p in (ROOT / a).rglob("*")
            if p.is_file() and p.name not in BOOKKEEPING
        ]
        raw = ROOT / "data" / "raw"
        raw_items = (
            sum(1 for p in raw.rglob("*.json") if p.name != "_profile.json")
            if raw.is_dir() else 0
        )
        return len(stored), raw_items

    def test_ledgers_reconcile_with_what_is_actually_on_disk(self):
        stored, raw = self.stored_and_raw()
        problems = reconcile(
            self.real_registries(), stored, raw,
            read("SOURCE_LEDGER.md"), read("KNOWLEDGE_LEDGER.md"),
        )
        self.assertEqual(problems, [], "ledgers disagree with the repository: " + "; ".join(problems))

    # A reconciliation that cannot object proves nothing, so each case below feeds
    # `reconcile` fabricated data and requires the specific complaint.
    CLEAN_SL = "| SRC-0001 | a source | `INACCESSIBLE` |\nharvested items: 0\n"
    CLEAN_KL = "**Verified knowledge records: 0.**\n"

    @staticmethod
    def slot(**over) -> dict:
        rec = {"fact_id": "OFF-F01", "value": None, "status": "BLOCKED",
               "provenance": {"document_id": None}}
        rec.update(over)
        return rec

    def reg(self, *records, **over) -> dict:
        data = {"record_count": len(records), "facts": list(records)}
        data.update(over)
        return {"knowledge/official/required_facts.json": data}

    def test_a_consistent_zero_state_is_accepted(self):
        self.assertEqual(
            reconcile(self.reg(self.slot()), 0, 0, self.CLEAN_SL, self.CLEAN_KL), []
        )

    def test_a_consistent_positive_state_is_accepted(self):
        # Not hardwired to zero: one harvested file and one verified record also pass.
        verified = self.slot(value="x", status="VERIFIED",
                             provenance={"document_id": "DOC-OFF-002"})
        self.assertEqual(
            reconcile(self.reg(verified), 1, 0,
                      "harvested items: 1\n", "Verified knowledge records: 1\n"),
            [],
        )

    def test_a_value_without_verification_is_rejected(self):
        problems = reconcile(
            self.reg(self.slot(value="900 marks")), 0, 0, self.CLEAN_SL, self.CLEAN_KL
        )
        self.assertTrue(any("holds a value while status is" in p for p in problems), problems)

    def test_verified_without_provenance_is_rejected(self):
        problems = reconcile(
            self.reg(self.slot(value="x", status="VERIFIED")), 0, 0,
            self.CLEAN_SL, "Verified knowledge records: 1\n",
        )
        self.assertTrue(any("VERIFIED with no provenance" in p for p in problems), problems)

    def test_a_wrong_record_count_is_rejected(self):
        problems = reconcile(
            self.reg(self.slot(), record_count=25), 0, 0, self.CLEAN_SL, self.CLEAN_KL
        )
        self.assertTrue(any("declares record_count 25" in p for p in problems), problems)

    def test_a_record_count_without_records_is_rejected(self):
        problems = reconcile(
            {"knowledge/official/required_facts.json": {"record_count": 25}},
            0, 0, self.CLEAN_SL, self.CLEAN_KL,
        )
        self.assertTrue(any("holds no record list" in p for p in problems), problems)

    def test_an_overstated_knowledge_ledger_is_rejected(self):
        problems = reconcile(
            self.reg(self.slot()), 0, 0, self.CLEAN_SL,
            "Verified knowledge records: 25\n",
        )
        self.assertTrue(any("declares 25 verified" in p for p in problems), problems)

    def test_an_overstated_source_ledger_is_rejected(self):
        problems = reconcile(
            self.reg(self.slot()), 0, 0, "harvested items: 6\n", self.CLEAN_KL
        )
        self.assertTrue(any("declares 6 harvested" in p for p in problems), problems)

    def test_an_available_row_with_nothing_stored_is_rejected(self):
        problems = reconcile(
            self.reg(self.slot()), 0, 0,
            "| SRC-0001 | a source | `AVAILABLE` |\nharvested items: 0\n", self.CLEAN_KL,
        )
        self.assertTrue(any("claim AVAILABLE while nothing is stored" in p for p in problems),
                        problems)

    def test_a_ledger_that_states_no_figure_at_all_is_rejected(self):
        problems = reconcile(self.reg(self.slot()), 0, 0, "no figure here\n", "none either\n")
        self.assertEqual(len(problems), 2, problems)
        self.assertTrue(any("SOURCE_LEDGER.md states no" in p for p in problems), problems)
        self.assertTrue(any("KNOWLEDGE_LEDGER.md states no" in p for p in problems), problems)

    def test_physical_standards_are_not_invented(self):
        d = ROOT / "physical/standards"
        stray = [p.name for p in d.iterdir() if p.name not in {".gitkeep", "README.md"}]
        self.assertEqual(
            stray, [], "physical standards must come from an official document only"
        )

    def test_project_state_marks_exam_knowledge_blocked(self):
        body = read("PROJECT_STATE.md")
        self.assertIn("BLOCKED", body)
        for area in ("Official syllabus", "Physical event standards", "PYQ database"):
            with self.subTest(area=area):
                self.assertIn(area, body)

    def test_no_fabricated_exam_facts_in_governance(self):
        # A concrete syllabus/marks claim would need a T1_OFFICIAL source, and none
        # exists yet. Guard against the most likely invented specifics.
        forbidden = re.compile(
            r"(total marks\s*[:=]\s*\d+|cut[- ]off\s*[:=]\s*\d+|exam date\s*[:=]\s*\d)",
            re.IGNORECASE,
        )
        for f in GOVERNANCE_FILES:
            with self.subTest(file=f):
                self.assertIsNone(
                    forbidden.search(read(f)),
                    f"{f} states an unsourced examination fact",
                )
class TestGitRepository(unittest.TestCase):
    def test_repository_is_initialised(self):
        self.assertTrue((ROOT / ".git").exists(), "git repository not initialised")

    def test_head_is_on_main(self):
        ref = (ROOT / ".git" / "HEAD").read_text(encoding="utf-8").strip()
        self.assertIn("refs/heads/main", ref, f"HEAD is '{ref}'")


class TestValidatorScript(unittest.TestCase):
    def test_validator_exists(self):
        self.assertTrue((ROOT / "scripts/validate_bootstrap.py").is_file())

    def test_validator_uses_standard_library_only(self):
        body = read("scripts/validate_bootstrap.py")
        for banned in ("import requests", "import yaml", "import pytest", "from pydantic"):
            with self.subTest(banned=banned):
                self.assertNotIn(banned, body)

    def test_validator_passes_on_this_repository(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_bootstrap.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(
            proc.returncode, 0,
            f"validator reported failures:\n{proc.stdout[-2000:]}",
        )

    def test_validator_actually_fails_on_a_broken_repository(self):
        # A validator that cannot fail proves nothing. Run the same script against a
        # near-empty directory and require a non-zero exit.
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "scripts"
            fake.mkdir()
            shutil.copy(ROOT / "scripts/validate_bootstrap.py", fake / "validate_bootstrap.py")
            proc = subprocess.run(
                [sys.executable, str(fake / "validate_bootstrap.py")],
                capture_output=True, text=True, cwd=tmp,
            )
        self.assertEqual(
            proc.returncode, 1,
            "validator passed on an empty directory, so its checks are vacuous",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
