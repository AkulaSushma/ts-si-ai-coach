#!/usr/bin/env python3
"""Bootstrap validator for the Telangana SI 2026 coaching system.

Checks that the repository's structure, governance files, and configuration are
intact. Standard library only, so it runs with no installation step (decision
D-0006).

Usage, from the project folder:

    python scripts/validate_bootstrap.py

Exit code 0 means every check passed. Exit code 1 means at least one failed.
A failure is a real finding: investigate it rather than relaxing the check.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files exempt from the secret-pattern scan because they legitimately contain
# the *patterns* used to detect secrets, not secrets themselves.
SECRET_SCAN_EXEMPT = {
    "scripts/validate_bootstrap.py",
    "tests/bootstrap/test_bootstrap.py",
    ".gitignore",
}

TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".sql", ".cfg", ".ini"}

GOVERNANCE_FILES = [
    "CLAUDE.md",
    "PROJECT_STATE.md",
    "TASK_LEDGER.md",
    "DECISIONS.md",
    "KNOWLEDGE_LEDGER.md",
    "SOURCE_LEDGER.md",
    "VERIFICATION_POLICY.md",
    "TEST_PLAN.md",
    "README.md",
]

MIN_GOVERNANCE_BYTES = 800

CANONICAL_ROLES = [
    "BULK_RESEARCH",
    "CLASSIFICATION",
    "SUMMARIZATION",
    "DEEP_REASONING",
    "CODE_GENERATION",
    "CODE_REVIEW",
    "VERIFICATION",
    "ARBITRATION",
]
TOP_LEVEL_AREAS = [
    "docs",
    "specs",
    "source_material",
    "research",
    "knowledge",
    "pyq",
    "expert_methods",
    "verification",
    "agents",
    "backend",
    "frontend",
    "database",
    "tests",
    "scripts",
    "config",
    "physical",
    "data",
]

REQUIRED_DIRS = TOP_LEVEL_AREAS + [
    "docs/guides", "docs/reports", "docs/architecture",
    "specs/data-model", "specs/features", "specs/api",
    "source_material/official", "source_material/pyq_raw", "source_material/books",
    "source_material/web", "source_material/media",
    "research/plans", "research/manifests", "research/extractions", "research/notes",
    "knowledge/schemas", "knowledge/syllabus", "knowledge/subjects", "knowledge/topics",
    "knowledge/question_families", "knowledge/methods", "knowledge/recognition",
    "knowledge/traps", "knowledge/confusions",
    "pyq/papers", "pyq/questions", "pyq/weightage",
    "expert_methods/claims", "expert_methods/educators",
    "verification/runs", "verification/evidence", "verification/disputes",
    "agents/roles", "agents/prompts", "agents/routing",
    "backend/app",
    "database/migrations", "database/seeds",
    "tests/bootstrap",
    "physical/standards", "physical/logs",
]

REQUIRED_SECTIONS = {
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
GITIGNORE_REQUIRED = [".env", "*.key", "data/*", "!data/README.md", "*.db", "__pycache__/"]

# Built from fragments so this file does not itself contain a literal key prefix.
SECRET_PATTERNS = [
    re.compile(r"sk-" + r"ant-api\d{2}-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bgh" + r"p_[A-Za-z0-9]{30,}"),
    re.compile(r"\bAK" + r"IA[0-9A-Z]{16}\b"),
    re.compile(r"\bAI" + r"za[0-9A-Za-z_\-]{35}\b"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,}"),
]

PLACEHOLDER_MARKERS = ["PENDING_VERIFICATION", "TODO_FILL", "FIXME_BOOTSTRAP", "XXX_PLACEHOLDER"]

results: list[tuple[bool, str, str]] = []


def check(name: str):
    """Register a check function. It returns (passed, detail)."""

    def wrapper(fn):
        passed, detail = fn()
        results.append((passed, name, detail))
        return fn

    return wrapper


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def tracked_text_files() -> list[Path]:
    out: list[Path] = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "data"}
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in skip_dirs for part in p.relative_to(ROOT).parts[:-1]):
            continue
        out.append(p)
    return out


def count_records(area: str) -> int:
    """Count real record files in a knowledge area, ignoring scaffolding."""
    d = ROOT / area
    if not d.is_dir():
        return 0
    return sum(1 for p in d.rglob("*") if p.is_file() and p.name not in {".gitkeep", "README.md"})
@check("required directories exist")
def _c_dirs():
    missing = [d for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
    if missing:
        return False, f"missing {len(missing)}: {', '.join(missing[:6])}"
    return True, f"all {len(REQUIRED_DIRS)} present"


@check("governance files exist at root")
def _c_gov_exist():
    missing = [f for f in GOVERNANCE_FILES if not (ROOT / f).is_file()]
    if missing:
        return False, f"missing: {', '.join(missing)}"
    return True, f"all {len(GOVERNANCE_FILES)} present"


@check("governance files have real content")
def _c_gov_size():
    thin = []
    for f in GOVERNANCE_FILES:
        p = ROOT / f
        if not p.is_file():
            thin.append(f"{f}(absent)")
        elif p.stat().st_size < MIN_GOVERNANCE_BYTES:
            thin.append(f"{f}({p.stat().st_size}B)")
    if thin:
        return False, f"below {MIN_GOVERNANCE_BYTES}B: {', '.join(thin)}"
    return True, f"all >= {MIN_GOVERNANCE_BYTES}B"


@check("governance files contain required sections")
def _c_gov_sections():
    problems = []
    for f, sections in REQUIRED_SECTIONS.items():
        if not (ROOT / f).is_file():
            problems.append(f"{f}(absent)")
            continue
        body = read(f)
        for s in sections:
            if s not in body:
                problems.append(f"{f} -> '{s}'")
    if problems:
        return False, f"{len(problems)} missing: {'; '.join(problems[:4])}"
    total = sum(len(v) for v in REQUIRED_SECTIONS.values())
    return True, f"{total} required sections found"
@check("every top-level area has a README")
def _c_area_readme():
    missing = [a for a in TOP_LEVEL_AREAS if not (ROOT / a / "README.md").is_file()]
    if missing:
        return False, f"missing README in: {', '.join(missing)}"
    return True, f"all {len(TOP_LEVEL_AREAS)} areas documented"


@check("empty directories retain .gitkeep")
def _c_gitkeep():
    bad = []
    for d in REQUIRED_DIRS:
        p = ROOT / d
        if not p.is_dir():
            continue
        if not any(p.iterdir()):
            bad.append(d)
    if bad:
        return False, f"empty, so git would not preserve them: {', '.join(bad)}"
    return True, "no required directory is completely empty"


@check("model_routing.json is valid JSON")
def _c_routing_json():
    p = ROOT / "config/model_routing.json"
    if not p.is_file():
        return False, "config/model_routing.json absent"
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"parse error line {e.lineno}: {e.msg}"
    return True, "parsed successfully"


def _routing() -> dict:
    p = ROOT / "config/model_routing.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


@check("all canonical agent roles are routed")
def _c_roles():
    roles = _routing().get("roles", {})
    missing = [r for r in CANONICAL_ROLES if r not in roles]
    extra = [r for r in roles if r not in CANONICAL_ROLES]
    if missing or extra:
        return False, f"missing={missing} unexpected={extra}"
    return True, f"{len(CANONICAL_ROLES)} roles routed"
@check("every routed provider is defined")
def _c_providers():
    cfg = _routing()
    providers = cfg.get("providers", {})
    problems = []
    for role, spec in cfg.get("roles", {}).items():
        prov = spec.get("provider")
        if prov == "AUTO_NOT_AUTHOR":
            cands = spec.get("candidates") or []
            if len(cands) < 2:
                problems.append(f"{role}: AUTO_NOT_AUTHOR needs >=2 candidates")
            for c in cands:
                if c not in providers:
                    problems.append(f"{role}: unknown candidate '{c}'")
        elif prov not in providers:
            problems.append(f"{role}: unknown provider '{prov}'")
        fb = spec.get("fallback")
        if fb is not None and fb not in providers:
            problems.append(f"{role}: unknown fallback '{fb}'")
    if problems:
        return False, "; ".join(problems[:4])
    return True, f"{len(providers)} providers, all references resolve"


@check("no provider verifies its own output")
def _c_independence():
    cfg = _routing()
    roles = cfg.get("roles", {})
    pairs = cfg.get("independence_pairs", [])
    if not pairs:
        return False, "independence_pairs is missing or empty"
    problems = []
    for pair in pairs:
        a, v = pair.get("author_role"), pair.get("verifier_role")
        if a not in roles or v not in roles:
            problems.append(f"{a}->{v}: role not defined")
            continue
        ap = roles[a].get("provider")
        vp = roles[v].get("provider")
        if vp == "AUTO_NOT_AUTHOR":
            cands = [c for c in (roles[v].get("candidates") or []) if c != ap]
            if not cands:
                problems.append(f"{a}->{v}: no candidate other than '{ap}'")
        elif ap == vp:
            problems.append(f"{a}->{v}: both use '{ap}'")
    if problems:
        return False, "; ".join(problems[:4])
    return True, f"{len(pairs)} author/verifier pairs are independent"
@check("routing config contains no credentials")
def _c_routing_no_secrets():
    p = ROOT / "config/model_routing.json"
    if not p.is_file():
        return False, "config absent"
    body = p.read_text(encoding="utf-8")
    for pat in SECRET_PATTERNS:
        if pat.search(body):
            return False, "a credential-like string is present"
    cfg = _routing()
    for name, spec in cfg.get("providers", {}).items():
        if not spec.get("api_key_env"):
            return False, f"provider '{name}' has no api_key_env"
        for key, val in spec.items():
            if isinstance(val, str) and key.endswith("key") and key != "api_key_env":
                return False, f"provider '{name}' has suspicious field '{key}'"
    return True, "keys referenced by environment variable only"


@check(".gitignore exists with required exclusions")
def _c_gitignore():
    p = ROOT / ".gitignore"
    if not p.is_file():
        return False, ".gitignore absent"
    lines = {ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()}
    missing = [pat for pat in GITIGNORE_REQUIRED if pat not in lines]
    if missing:
        return False, f"missing patterns: {', '.join(missing)}"
    return True, f"all {len(GITIGNORE_REQUIRED)} critical patterns present"


@check(".env.example exists and holds no real key")
def _c_env_example():
    p = ROOT / ".env.example"
    if not p.is_file():
        return False, ".env.example absent"
    body = p.read_text(encoding="utf-8")
    for pat in SECRET_PATTERNS:
        if pat.search(body):
            return False, "contains a credential-like string"
    if "ANTHROPIC_API_KEY" not in body or "GLM_API_KEY" not in body:
        return False, "does not document both providers' key variables"
    return True, "placeholders only, both providers documented"


@check("no credential-like string in any project file")
def _c_no_secrets():
    hits = []
    for p in tracked_text_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel in SECRET_SCAN_EXEMPT:
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        for pat in SECRET_PATTERNS:
            if pat.search(body):
                hits.append(rel)
                break
    if hits:
        return False, f"credential-like strings in: {', '.join(hits[:4])}"
    return True, "scanned project text files, none found"
@check("data/ ignored but data/README.md kept")
def _c_data_rules():
    p = ROOT / ".gitignore"
    if not p.is_file():
        return False, ".gitignore absent"
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()]
    if "data/*" not in lines:
        return False, "'data/*' not ignored"
    if "!data/README.md" not in lines:
        return False, "'!data/README.md' negation absent"
    if lines.index("data/*") > lines.index("!data/README.md"):
        return False, "negation appears before the exclusion, so it has no effect"
    if not (ROOT / "data/README.md").is_file():
        return False, "data/README.md missing"
    return True, "runtime data excluded, its README retained"


@check("status vocabulary is defined and exclusive")
def _c_status_vocab():
    body = read("CLAUDE.md")
    for token in ("`COMPLETE`", "`PARTIAL`", "`BLOCKED`"):
        if token not in body:
            return False, f"{token} not defined in CLAUDE.md"
    if "### Status vocabulary" not in body:
        return False, "status vocabulary section absent"
    return True, "COMPLETE / PARTIAL / BLOCKED defined in CLAUDE.md"


@check("no unresolved placeholder markers remain")
def _c_placeholders():
    hits = []
    for p in tracked_text_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel in {"scripts/validate_bootstrap.py", "tests/bootstrap/test_bootstrap.py"}:
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        for marker in PLACEHOLDER_MARKERS:
            if marker in body:
                hits.append(f"{rel}:{marker}")
                break
    if hits:
        return False, f"{len(hits)} unresolved: {', '.join(hits[:4])}"
    return True, "none found"


BOOKKEEPING_NAMES = {".gitkeep", "README.md", "RETRIEVAL_LOG.md"}
RECORD_LIST_KEYS = ("facts", "nodes", "entries", "records", "documents")


def _record_list(data: dict) -> tuple[str, list] | tuple[None, None]:
    """Return the (key, list) holding a registry's records, if it has one."""
    for key in RECORD_LIST_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            return key, value
    return None, None


def knowledge_registries() -> list[Path]:
    """Every JSON registry under knowledge/, excluding the declarative schemas."""
    d = ROOT / "knowledge"
    if not d.is_dir():
        return []
    return sorted(
        p for p in d.rglob("*.json")
        if p.is_file() and "schemas" not in p.relative_to(d).parts
    )


def stored_source_files() -> list[str]:
    """Acquired source bytes under source_material/, excluding bookkeeping files."""
    d = ROOT / "source_material"
    if not d.is_dir():
        return []
    return sorted(
        p.relative_to(ROOT).as_posix()
        for p in d.rglob("*")
        if p.is_file() and p.name not in BOOKKEEPING_NAMES
    )


def declared_number(body: str, label: str) -> int | None:
    m = re.search(re.escape(label) + r":\s*\*{0,2}\s*(\d+)", body)
    return int(m.group(1)) if m else None


@check("ledger claims match the filesystem")
def _c_ledger_counts():
    areas = ["knowledge", "pyq", "expert_methods", "source_material", "verification"]
    actual = {a: count_records(a) for a in areas}
    # Raw ingestion records (data/raw/<platform>/<source_id>/*.json) are the
    # other place acquired content lives. _profile.json is metadata, not a
    # content record.
    raw_items = 0
    raw_dir = ROOT / "data" / "raw"
    if raw_dir.is_dir():
        raw_items = sum(
            1 for p in raw_dir.rglob("*.json") if p.name != "_profile.json"
        )
    stored = stored_source_files()
    harvested_total = len(stored) + raw_items

    problems: list[str] = []
    verified_total = 0
    records_total = 0

    for path in knowledge_registries():
        rel = path.relative_to(ROOT).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{rel} is not valid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            continue
        key, records = _record_list(data)
        if "record_count" in data and key is None:
            problems.append(f"{rel} declares record_count but holds no recognised record list")
            continue
        if records is None:
            continue
        records = [r for r in records if isinstance(r, dict)]
        records_total += len(records)
        if isinstance(data.get("record_count"), int) and data["record_count"] != len(records):
            problems.append(
                f"{rel} declares record_count {data['record_count']} but holds {len(records)}"
            )
        for r in records:
            rid = r.get("fact_id") or r.get("node_id") or r.get("entry_id") or "<no id>"
            status = r.get("status")
            if status == "VERIFIED":
                verified_total += 1
                if not (r.get("provenance") or {}).get("document_id"):
                    problems.append(f"{rel}:{rid} is VERIFIED with no provenance document")
            if r.get("value") is not None and status != "VERIFIED":
                problems.append(f"{rel}:{rid} holds a value while status is {status!r}")
        if isinstance(data.get("verified_count"), int):
            got = sum(1 for r in records if r.get("status") == "VERIFIED")
            if data["verified_count"] != got:
                problems.append(
                    f"{rel} declares verified_count {data['verified_count']} but holds {got}"
                )

    sl = read("SOURCE_LEDGER.md")
    kl = read("KNOWLEDGE_LEDGER.md")
    # A ledger row claims harvested content when it is AVAILABLE. Registration
    # rows (INACCESSIBLE / pending) are honest bookkeeping of *intent*.
    available_rows = [
        ln for ln in sl.splitlines()
        if ln.startswith("| SRC-") and "`AVAILABLE`" in ln
    ]
    if available_rows and harvested_total == 0:
        problems.append(
            f"{len(available_rows)} ledger row(s) claim AVAILABLE content but nothing is stored"
        )

    declared_harvest = declared_number(sl, "harvested items")
    if declared_harvest is None:
        problems.append("SOURCE_LEDGER.md states no 'harvested items: N' figure")
    elif declared_harvest != harvested_total:
        problems.append(
            f"SOURCE_LEDGER.md declares harvested items {declared_harvest}, "
            f"disk holds {harvested_total}"
        )

    declared_verified = declared_number(kl, "Verified knowledge records")
    if declared_verified is None:
        problems.append("KNOWLEDGE_LEDGER.md states no 'Verified knowledge records: N' figure")
    elif declared_verified != verified_total:
        problems.append(
            f"KNOWLEDGE_LEDGER.md declares {declared_verified} verified records, "
            f"registries hold {verified_total}"
        )

    if problems:
        return False, "; ".join(problems[:4]) + (
            f" (+{len(problems) - 4} more)" if len(problems) > 4 else ""
        )
    return True, (
        f"{records_total} knowledge record(s), {verified_total} VERIFIED and declared as such; "
        f"{harvested_total} harvested item(s) ({len(stored)} stored file(s), {raw_items} raw); "
        f"area files {actual}; no value without verification"
    )


@check("physical standards folder is empty until sourced")
def _c_physical_guard():
    d = ROOT / "physical/standards"
    if not d.is_dir():
        return False, "physical/standards missing"
    files = [p.name for p in d.iterdir() if p.name not in {".gitkeep", "README.md"}]
    if files:
        return False, (
            "contains data that must come from an official document: " + ", ".join(files[:4])
        )
    return True, "empty, as required until an official TGPRB document is obtained"


@check("git repository is initialised on main")
def _c_git():
    g = ROOT / ".git"
    if not g.exists():
        return False, ".git not found; repository not initialised"
    head = g / "HEAD"
    if not head.is_file():
        return False, ".git/HEAD missing"
    ref = head.read_text(encoding="utf-8").strip()
    if "refs/heads/main" not in ref:
        return False, f"HEAD is '{ref}', expected refs/heads/main"
    return True, "initialised, HEAD on main"


@check("no .env file is present in the repository")
def _c_no_env():
    if (ROOT / ".env").exists():
        return False, ".env exists; it is git-ignored but must never be committed"
    return True, "absent (expected: user creates it locally from .env.example)"


def main() -> int:
    print("=" * 72)
    print("Bootstrap validation - Telangana SI 2026 Coaching System")
    print(f"Repository: {ROOT}")
    print("=" * 72)
    failed = 0
    for i, (passed, name, detail) in enumerate(results, 1):
        tag = "PASS" if passed else "FAIL"
        if not passed:
            failed += 1
        print(f"[{tag}] {i:2d}. {name}\n         {detail}")
    print("=" * 72)
    total = len(results)
    print(f"{total - failed} passed, {failed} failed, {total} checks total")
    if failed:
        print("RESULT: FAIL - the repository is not in a valid state.")
        print("Investigate each failure. Do not relax a check to make it pass.")
    else:
        print("RESULT: PASS - repository structure and governance are intact.")
    print("=" * 72)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
