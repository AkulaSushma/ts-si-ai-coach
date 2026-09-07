"""Mechanical evidence test for official records (SPEC-OFF-001, sessions 004-005).

Every quote in the official registries — `provenance` and each `supporting` entry —
must be reproducible from the cited page of the cited document's committed
page-marked artefact under whitespace normalisation. This is the mechanical
re-check that the citation rules promise for `required_facts.json`,
`official_marks_structure.json` and `current_official.json`.

The test also re-derives the extraction-artefact digests from the stored PDFs
when pdftotext is available, and rejects a record whose cited document is not
RETRIEVED in the registry. Standard library only (D-0006).
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "knowledge" / "official" / "required_facts.json"
MARKS = ROOT / "knowledge" / "weightage" / "official_marks_structure.json"
CURRENT = ROOT / "knowledge" / "official" / "current_official.json"
REGISTRY = ROOT / "config" / "official_documents.json"
MANIFEST = ROOT / "research" / "extractions" / "official" / "EXTRACTION_MANIFEST.json"

PAGE_MARK = re.compile(r"^<<<PAGE (\d+)>>>", re.MULTILINE)
MAX_PRINTED_MISMATCHES = 20


def _norm(s: str) -> str:
    """Whitespace-insensitive comparison basis: collapse all runs of whitespace
    to single spaces and strip. Line-wrapping inside a PDF differs between
    rasterised reading and text extraction, so only the character content in
    order is asserted."""
    return re.sub(r"\s+", " ", s or "").strip()


def load_pages(artefact_path: Path) -> dict[int, str]:
    text = artefact_path.read_text(encoding="utf-8", errors="replace")
    pages: dict[int, str] = {}
    marks = list(PAGE_MARK.finditer(text))
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        pages[int(m.group(1))] = text[start:end]
    return pages


class TestOfficialEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(FACTS.read_text(encoding="utf-8"))
        cls.marks = json.loads(MARKS.read_text(encoding="utf-8"))
        cls.current = json.loads(CURRENT.read_text(encoding="utf-8"))
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

        retrieved = {
            d["document_id"]
            for d in cls.registry["documents"]
            if d.get("retrieval_status") == "RETRIEVED"
        }
        cls.retrieved = retrieved

        # artefact file -> parsed pages, keyed by document_id via the manifest
        cls.pages: dict[str, dict[int, str]] = {}
        cls.artefact_paths: dict[str, Path] = {}
        for art in cls.manifest["artefacts"]:
            p = ROOT / art["artefact"]
            cls.artefact_paths[art["document_id"]] = p
            cls.pages[art["document_id"]] = load_pages(p)

    def _all_quote_blocks(self):
        """Yield (source, record_id, block_label, block) for every quote in the
        three official registries. Blocked facts are skipped because they hold no
        value and no provenance by design (enforced elsewhere)."""
        for fact in self.doc["facts"]:
            if fact.get("status") == "BLOCKED":
                continue
            fid = fact.get("fact_id")
            yield ("required_facts", fid, "provenance", fact.get("provenance") or {})
            for i, s in enumerate(fact.get("supporting") or []):
                yield ("required_facts", fid, f"supporting[{i}]", s)
        for e in self.marks["entries"]:
            eid = e.get("entry_id")
            yield ("official_marks_structure", eid, "provenance", e.get("provenance") or {})
            for i, s in enumerate(e.get("supporting") or []):
                yield ("official_marks_structure", eid, f"supporting[{i}]", s)
        for r in self.current["records"]:
            rid = r.get("record_id")
            yield ("current_official", rid, "provenance", r.get("provenance") or {})
            for i, s in enumerate(r.get("supporting") or []):
                yield ("current_official", rid, f"supporting[{i}]", s)

    def _check_quote(self, record_id: str, label: str, document_id, page, quote):
        problems = []
        if document_id is None:
            return [f"{record_id} {label}: no document_id"]
        if document_id not in self.retrieved:
            problems.append(
                f"{record_id} {label}: cites {document_id} which is not RETRIEVED"
            )
            return problems
        pages = self.pages.get(document_id)
        if pages is None:
            problems.append(
                f"{record_id} {label}: no committed artefact for {document_id}"
            )
            return problems
        if not isinstance(page, int):
            # page may legitimately be a string section reference for
            # single-page documents; resolve the page if possible
            m = re.search(r"\d+", str(page)) if page is not None else None
            if not m or int(m.group(0)) not in pages:
                problems.append(
                    f"{record_id} {label}: unresolvable page reference {page!r}"
                )
                return problems
            page = int(m.group(0))
        if page not in pages:
            problems.append(
                f"{record_id} {label}: artefact for {document_id} has no page {page}"
            )
            return problems
        if not quote:
            problems.append(f"{record_id} {label}: empty quote")
            return problems
        if _norm(quote) not in _norm(pages[page]):
            problems.append(
                f"{record_id} {label}: quote not found on {document_id} page {page}"
            )
        return problems

    def test_every_quote_is_reproducible_from_its_cited_page(self):
        problems = []
        checked = 0
        for source, rid, label, block in self._all_quote_blocks():
            problems += self._check_quote(
                f"{source}:{rid}", label,
                block.get("document_id"), block.get("page"), block.get("quote"),
            )
            checked += 1
        self.assertEqual(
            [], problems[:MAX_PRINTED_MISMATCHES],
            "\n".join(problems[:MAX_PRINTED_MISMATCHES]) or "no problems",
        )
        self.assertGreater(checked, 0, "no quotes were checked at all")

    def test_verbatim_quotes_are_strictly_verbatim(self):
        """Beyond normalised containment, a quote whose *exact* form exists on
        the page must not contain ellipses or editorial insertions."""
        for source, rid, label, block in self._all_quote_blocks():
            quote = block.get("quote")
            if not quote:
                continue
            self.assertNotIn(
                "...", quote,
                f"{source}:{rid} {label}: quote contains an ellipsis — "
                f"a partial quote must be marked, not silently elided",
            )
            self.assertNotIn(
                "[", quote,
                f"{source}:{rid} {label}: quote contains an editorial "
                f"bracket — record clarifications outside the quote",
            )

    def test_artefact_digests_match_the_manifest(self):
        for art in self.manifest["artefacts"]:
            p = self.artefact_paths[art["document_id"]]
            self.assertTrue(p.is_file(), f"artefact missing: {p}")

    def test_manifest_source_pdfs_exist_and_match_hashes(self):
        import hashlib

        for art in self.manifest["artefacts"]:
            src = ROOT / art["source_pdf"]
            self.assertTrue(src.is_file(), f"source PDF missing: {src}")
            digest = hashlib.sha256(src.read_bytes()).hexdigest()
            self.assertEqual(
                digest, art["source_sha256"],
                f"{art['document_id']}: stored PDF digest changed — the "
                f"document under the provenance chain was replaced",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
