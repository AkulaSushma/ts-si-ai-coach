#!/usr/bin/env python3
"""Operator entry point for the ingestion subsystem.

    python scripts/ingest.py extract                    # all enabled sources
    python scripts/ingest.py extract --source IG001     # one source
    python scripts/ingest.py extract --url <profile url>
    python scripts/ingest.py resume [--source IG001]
    python scripts/ingest.py status [IG001]
    python scripts/ingest.py add --url <profile url>

Standard library only (D-0006). Safe to run twice: extraction is idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.ingestion.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
