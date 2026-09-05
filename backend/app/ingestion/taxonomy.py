"""Fixed vocabularies for the ingestion and later AI-processing stages.

These enums are the contract between the ingestion subsystem and the future
GLM classification stage. Values are fixed by SPEC-ING-001 §4.5 and by the
user's task instruction; a later stage must not invent categories.
"""

from __future__ import annotations

# Provenance tiers (mirrors CLAUDE.md §5; never relabelled upward)
PROVENANCE_TIERS = ("T1_OFFICIAL", "T2_HISTORICAL_PYQ", "T3_EXPERT", "T4_AI")

# Subjects for the later GLM classification stage
SUBJECTS = (
    "Indian History",
    "Telangana History",
    "Indian Polity",
    "Constitution",
    "Geography",
    "Telangana Geography",
    "Economy",
    "General Science",
    "Current Affairs",
    "Telangana GK",
    "Arithmetic",
    "Reasoning",
    "English",
    "Telugu",
    "Other SI/Constable subject",
    "Not relevant",
)

# Knowledge types for the later GLM classification stage
KNOWLEDGE_TYPES = (
    "FACT", "CONCEPT", "DEFINITION", "DATE", "PERSON", "PLACE", "LAW",
    "ARTICLE", "AMENDMENT", "FORMULA", "SHORTCUT", "MCQ", "QUESTION",
    "CURRENT_AFFAIRS", "EXPLANATION", "OTHER",
)

# Relevance / quality fields the later stage may fill. All values stay null
# until that stage exists; ingestion never populates them.
AI_RELEVANCE_FIELDS = (
    "si_relevance",          # bool: useful for SI preparation
    "constable_relevance",   # bool: useful for Constable preparation
    "telangana_relevance",   # bool: Telangana-specific content
    "pyq_similarity",        # float 0..1: similarity to a known PYQ
    "revision_priority",     # int 0..5: how early/often to revise
    "confidence",            # float 0..1: classifier confidence
)

# Verification statuses (mirrors knowledge/README.md vocabulary)
VERIFICATION_STATUSES = ("VERIFIED", "UNVERIFIED", "DISPUTED", "REJECTED")

# Content types produced by adapters
CONTENT_TYPES = ("post", "carousel", "reel", "unclassified")

# Checkpoint lifecycle
SOURCE_STATUSES = (
    "not_started", "in_progress", "partial", "complete", "blocked",
)

# Hard cap per source. SPEC-ING-001 §2: never interpretable as 299+299.
MAX_ITEMS_HARD_CAP = 299

# Accounting identity terms (research/README.md)
ACCOUNTING_DISPOSITIONS = ("extracted", "duplicate", "failed", "inaccessible")
