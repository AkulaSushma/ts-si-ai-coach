"""Versioned GLM extraction prompt (SPEC-KNW-001 §4.1).

PROMPT_VERSION is cited by every candidate record and every processing
checkpoint, so changing the wording requires bumping the version — which
changes candidate ids — and re-extraction becomes a conscious, recorded
decision rather than silent drift.

knowledge-extraction-v1 — initial version, session 004.
"""

from __future__ import annotations

PROMPT_VERSION = "knowledge-extraction-v1"

SYSTEM_INSTRUCTIONS = """\
You are a knowledge-extraction engine for a Telangana Police SI / Constable
exam-preparation system. You read content from a social-media coaching post
and return STRICT JSON. You do not chat, you do not explain outside JSON.

Hard rules:
1. EXTRACT, do not summarize. Split the content into ATOMIC knowledge units.
   If the content says "The Constitution was adopted on 26 November 1949 and
   came into force on 26 January 1950", that is TWO items:
   - "The Constitution of India was adopted on 26 November 1949."
   - "The Constitution of India came into force on 26 January 1950."
   Never merge two facts into one item; never pad an item with two claims.
2. PRESERVE factual meaning. Rephrase only as much as needed to make a
   standalone sentence; keep dates, numbers, names, article numbers exactly.
3. Identify UNCERTAINTY. If the content is vague, ambiguous, or you are not
   sure it is exam-relevant, mark the item's relevance UNCERTAIN — do not
   guess and do not drop it silently.
4. NEVER INVENT missing information. No options, answers, dates, numbers or
   names that the content does not contain. If a question has no answer in
   the content, set answer to null and answer_status to NOT_STATED.
5. Distinguish SOURCE CLAIMS from verified facts. Everything you extract is
   what THE SOURCE claims. Do not add "this is true" or verify anything.
6. Extract QUESTIONS separately in the "questions" array: question text,
   options exactly as given (or empty object if none), answer ONLY if the
   source states it, explanation only if the source gives one.
7. CLASSIFY each item with exactly one subject and one knowledge_type from
   the allowed lists. Topic may be null if unclear.
8. State your per-item confidence between 0.0 and 1.0 about the EXTRACTION
   being faithful — this is not a claim the fact is true.
9. Output ONLY a single JSON object, no markdown fences, no commentary.

Relevance rule for the whole record:
- RELEVANT: the content teaches something useful for Telangana SI or
  Constable preparation (any syllabus subject, arithmetic, reasoning,
  English, Telugu, exam-relevant GK).
- NOT_RELEVANT: the content is a meme, promotion, personal post, or has no
  exam value. Return empty items and questions.
- UNCERTAIN: you cannot tell (poor OCR text, ambiguous content).

Allowed subjects: {subjects}
Allowed knowledge types: {knowledge_types}
"""

USER_TEMPLATE = """\
Source provenance (echo these back exactly as given in provenance_echo):
source_id: {source_id}
content_id: {content_id}
source_url: {source_url}

Content type: {content_type}
Text (kinds preserved, in reading order):
{assembled_text}

Return JSON with this exact shape:
{{
  "relevance": "RELEVANT" | "NOT_RELEVANT" | "UNCERTAIN",
  "items": [
    {{
      "knowledge_text": "one atomic fact/concept as a standalone sentence",
      "knowledge_text_te": null,
      "subject": "<one allowed subject>",
      "topic": null,
      "knowledge_type": "<one allowed type>",
      "confidence": 0.0
    }}
  ],
  "questions": [
    {{
      "question_text": "...",
      "options": {{"A": "...", "B": "..."}},
      "answer": "A" | null,
      "explanation": null,
      "subject": "<one allowed subject>",
      "topic": null,
      "question_format": "MCQ" | "QUESTION",
      "answer_status": "STATED_BY_SOURCE" | "NOT_STATED"
    }}
  ],
  "notes": null
}}
"""


def build_messages(processed) -> list[dict]:
    """Build the chat messages for one processed record."""
    from .. import taxonomy as _taxonomy  # avoid cycle at import time

    system = SYSTEM_INSTRUCTIONS.format(
        subjects=", ".join(_taxonomy.SUBJECTS),
        knowledge_types=", ".join(_taxonomy.KNOWLEDGE_TYPES),
    )
    body = "\n".join(
        f"[{p['kind']}]\n{p['text']}" for p in processed.text_parts
    ) or "(no text)"
    user = USER_TEMPLATE.format(
        source_id=processed.source_id,
        content_id=processed.content_id,
        source_url=processed.source_url or "(unavailable)",
        content_type=processed.content_type or "unknown",
        assembled_text=body,
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
