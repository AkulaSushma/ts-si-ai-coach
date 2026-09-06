"""Vocabularies for the knowledge pipeline (SPEC-KNW-001 §5, §6).

Extends the ingestion taxonomy with the pipeline's own enums. New subjects are
added by editing SUBJECTS here (or the allowlist config) — core processing
logic never changes for a new subject, because every consumer reads these
tuples instead of hard-coding names.
"""

from __future__ import annotations

# Provenance tiers (unchanged from ingestion; mirrored for convenience)
PROVENANCE_TIERS = ("T1_OFFICIAL", "T2_HISTORICAL_PYQ", "T3_EXPERT", "T4_AI")

# Subjects (user requirement §5). "Indian Constitution" is distinct from
# "Indian Polity" per the user's list; "Other SI/Constable-relevant subjects"
# is the explicit catch-all so the enum is closed and future subjects are a
# data edit here, not a code change elsewhere.
SUBJECTS = (
    "Indian History",
    "Telangana History",
    "Indian Polity",
    "Indian Constitution",
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
    "Other SI/Constable-relevant subject",
)

# Telangana-specific subjects (drives telangana_relevance, scoring.py)
TELANGANA_SUBJECTS = (
    "Telangana History",
    "Telangana Geography",
    "Telangana GK",
)

# Knowledge types (user requirement §6)
KNOWLEDGE_TYPES = (
    "FACT", "CONCEPT", "DEFINITION", "DATE", "PERSON", "PLACE", "LAW",
    "ARTICLE", "AMENDMENT", "FORMULA", "SHORTCUT", "CURRENT_AFFAIRS",
    "EXPLANATION", "MCQ", "QUESTION", "OTHER",
)

# Per-item relevance verdicts (user requirement §4)
RELEVANCE = ("RELEVANT", "NOT_RELEVANT", "UNCERTAIN")

# Question formats
QUESTION_FORMATS = ("MCQ", "QUESTION")

# Whether a source stated the answer (never invented, user requirement §8)
ANSWER_STATUSES = ("STATED_BY_SOURCE", "NOT_STATED")

# Verification states a candidate may hold. UNVERIFIED is the only value the
# pipeline may create; VERIFIED / REJECTED / NEEDS_REVIEW belong to the
# separate verification stage only.
VERIFICATION_STATUSES = ("UNVERIFIED", "VERIFIED", "REJECTED", "NEEDS_REVIEW")
INITIAL_VERIFICATION_STATUS = "UNVERIFIED"

# Source-diversity buckets for corroboration (SPEC-KNW-001 §6)
SOURCE_DIVERSITY = ("SAME_ACCOUNT", "FEW_ACCOUNTS", "MANY_ACCOUNTS")

# Model call failures recorded per item, bounded (cost control §9)
MAX_EXTRACTION_RETRIES = 3
