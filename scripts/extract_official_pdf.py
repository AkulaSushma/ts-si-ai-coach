#!/usr/bin/env python3
"""Extract a page-marked text artefact from an official PDF, reproducibly.

Why this exists
---------------
Every official fact in this repository must cite a document and a page. A citation is
only checkable if the page text itself is available to the checker, so the extraction
is committed as an artefact and its digest is recorded. Anyone holding the same PDF can
re-run this script and must obtain a byte-identical artefact; if they do not, either the
PDF or the artefact changed and the provenance chain is broken.

Usage
-----
    python scripts/extract_official_pdf.py DOC-OFF-002
    python scripts/extract_official_pdf.py --all
    python scripts/extract_official_pdf.py --all --check

`--check` re-extracts into a temporary file and compares digests without writing,
so it can be run to confirm that committed artefacts still match their PDFs.

Requires the `pdftotext` binary (poppler-utils). The exact version used for the
committed artefacts is recorded in the extraction manifest; a different version may
lay text out differently, which `--check` will report as a mismatch rather than hide.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "official_documents.json"
OUT_DIR = ROOT / "research" / "extractions" / "official"
PAGE_MARK = "<<<PAGE {n}>>>"

# document_id -> artefact file name. Only documents listed here are extractable;
# a document absent from this map has not been retrieved.
ARTEFACTS = {
    "DOC-OFF-002": "DOC-OFF-002-si-notification-pages.txt",
    "DOC-OFF-003": "DOC-OFF-003-supplementary-notification-pages.txt",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pdftotext_version() -> str:
    proc = subprocess.run(
        ["pdftotext", "-v"], capture_output=True, text=True, check=False
    )
    first = (proc.stdout + proc.stderr).strip().splitlines()
    return first[0].strip() if first else "unknown"


def extract(pdf: Path) -> bytes:
    """Return the page-marked artefact bytes for one PDF.

    The raw `pdftotext -layout` output separates pages with a form feed. Pages are
    numbered from 1 in physical order; each is prefixed with a marker so a checker can
    locate the page a quote was cited from without re-reading the PDF.
    """
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.txt"
        subprocess.run(
            ["pdftotext", "-layout", str(pdf), str(raw)],
            check=True,
            capture_output=True,
        )
        text = raw.read_text(encoding="utf-8", errors="replace")

    pages = text.split("\f")
    if pages and pages[-1].strip() == "":
        pages = pages[:-1]

    chunks = []
    for number, body in enumerate(pages, start=1):
        chunks.append(PAGE_MARK.format(n=number) + "\n" + body.rstrip("\n") + "\n")
    return ("\n".join(chunks)).encode("utf-8")


def registry_documents() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {d["document_id"]: d for d in data["documents"]}


def resolve_pdf(doc: dict) -> Path:
    local = doc.get("local_path")
    if not local:
        raise SystemExit(
            f"{doc['document_id']} has no local_path; it has not been retrieved"
        )
    path = ROOT / local
    if not path.is_file():
        raise SystemExit(f"{doc['document_id']} local_path does not exist: {path}")
    return path


def run(doc_ids: list[str], check_only: bool) -> int:
    docs = registry_documents()
    problems: list[str] = []
    for doc_id in doc_ids:
        if doc_id not in ARTEFACTS:
            problems.append(f"{doc_id} is not in the extractable set {sorted(ARTEFACTS)}")
            continue
        doc = docs.get(doc_id)
        if doc is None:
            problems.append(f"{doc_id} is not in {REGISTRY.name}")
            continue

        pdf = resolve_pdf(doc)
        actual_pdf_digest = sha256_file(pdf)
        if doc.get("sha256") and doc["sha256"] != actual_pdf_digest:
            problems.append(
                f"{doc_id} PDF digest {actual_pdf_digest} != registry {doc['sha256']}"
            )
            continue

        artefact = OUT_DIR / ARTEFACTS[doc_id]
        produced = extract(pdf)
        produced_digest = sha256_bytes(produced)

        if check_only:
            if not artefact.is_file():
                problems.append(f"{doc_id} artefact missing: {artefact}")
            elif sha256_file(artefact) != produced_digest:
                problems.append(
                    f"{doc_id} artefact does not match a fresh extraction "
                    f"({sha256_file(artefact)} != {produced_digest})"
                )
            else:
                print(f"[OK]   {doc_id} artefact matches a fresh extraction")
            continue

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        artefact.write_bytes(produced)
        pages = produced.decode("utf-8").count("<<<PAGE ")
        print(
            f"[WROTE] {doc_id} -> {artefact.relative_to(ROOT)}  "
            f"{pages} page(s)  sha256 {produced_digest}"
        )
        print(f"        source sha256 {actual_pdf_digest}  tool {pdftotext_version()}")

    for problem in problems:
        print(f"[FAIL] {problem}")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document_id", nargs="*", help="e.g. DOC-OFF-002")
    parser.add_argument("--all", action="store_true", help="every extractable document")
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare committed artefacts against a fresh extraction; write nothing",
    )
    args = parser.parse_args()

    doc_ids = sorted(ARTEFACTS) if args.all else args.document_id
    if not doc_ids:
        parser.error("give at least one document id, or --all")
    return run(doc_ids, args.check)


if __name__ == "__main__":
    sys.exit(main())
