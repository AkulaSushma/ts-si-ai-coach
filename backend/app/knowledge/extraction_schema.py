"""Strict validation of GLM extraction output (SPEC-KNW-001 §4.2).

Malformed output raises ExtractionSchemaError with a field path — the item is
recorded failed and retried; values are never silently coerced into validity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import taxonomy

MAX_KNOWLEDGE_TEXT_CHARS = 2000


class ExtractionSchemaError(ValueError):
    """Malformed model output. `.path` names the offending field."""


@dataclass
class ExtractionItem:
    knowledge_text: str
    subject: str
    knowledge_type: str
    knowledge_text_te: str | None = None
    topic: str | None = None
    confidence: float | None = None


@dataclass
class ExtractionQuestion:
    question_text: str
    subject: str
    question_format: str
    answer_status: str
    options: dict = field(default_factory=dict)
    answer: str | None = None
    explanation: str | None = None
    topic: str | None = None


@dataclass
class ExtractionResult:
    relevance: str
    items: list[ExtractionItem] = field(default_factory=list)
    questions: list[ExtractionQuestion] = field(default_factory=list)
    notes: str | None = None


def _err(path: str, message: str):
    raise ExtractionSchemaError(f"{path}: {message}")


def _check_str(path: str, value, *, allow_none=False, max_len=None) -> str | None:
    if value is None:
        if allow_none:
            return None
        _err(path, "is null")
    if not isinstance(value, str):
        _err(path, f"is {type(value).__name__}, expected string")
    if not value.strip() and not allow_none:
        _err(path, "is empty")
    if max_len and len(value) > max_len:
        _err(path, f"exceeds {max_len} chars")
    return value


def _check_confidence(path: str, value) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        _err(path, f"is {type(value).__name__}, expected number")
    c = float(value)
    if not 0.0 <= c <= 1.0:
        _err(path, f"is {c}, outside [0,1]")
    return c


def validate_extraction(payload) -> ExtractionResult:
    """Validate one model-output payload. Raises ExtractionSchemaError."""
    if not isinstance(payload, dict):
        _err("$", f"is {type(payload).__name__}, expected object")

    relevance = payload.get("relevance")
    if relevance not in taxonomy.RELEVANCE:
        _err("$.relevance", f"is {relevance!r}, expected one of {taxonomy.RELEVANCE}")
    if relevance == "NOT_RELEVANT":
        # A NOT_RELEVANT record must not smuggle items through.
        items = payload.get("items") or []
        questions = payload.get("questions") or []
        if items or questions:
            _err("$.items", "NOT_RELEVANT output must hold no items or questions")
        return ExtractionResult(relevance="NOT_RELEVANT")

    raw_items = payload.get("items")
    if raw_items is None:
        raw_items = []
    if not isinstance(raw_items, list):
        _err("$.items", f"is {type(raw_items).__name__}, expected list")

    items: list[ExtractionItem] = []
    for i, it in enumerate(raw_items):
        base = f"$.items[{i}]"
        if not isinstance(it, dict):
            _err(base, f"is {type(it).__name__}, expected object")
        text = _check_str(base + ".knowledge_text", it.get("knowledge_text"),
                          max_len=MAX_KNOWLEDGE_TEXT_CHARS)
        subject = it.get("subject")
        if subject not in taxonomy.SUBJECTS:
            _err(base + ".subject",
                 f"is {subject!r}, not in the subject taxonomy")
        ktype = it.get("knowledge_type")
        if ktype not in taxonomy.KNOWLEDGE_TYPES:
            _err(base + ".knowledge_type",
                 f"is {ktype!r}, not in the knowledge-type taxonomy")
        items.append(ExtractionItem(
            knowledge_text=text,
            subject=subject,
            knowledge_type=ktype,
            knowledge_text_te=_check_str(base + ".knowledge_text_te",
                                         it.get("knowledge_text_te"),
                                         allow_none=True),
            topic=_check_str(base + ".topic", it.get("topic"), allow_none=True),
            confidence=_check_confidence(base + ".confidence",
                                         it.get("confidence")),
        ))

    raw_questions = payload.get("questions")
    if raw_questions is None:
        raw_questions = []
    if not isinstance(raw_questions, list):
        _err("$.questions", f"is {type(raw_questions).__name__}, expected list")

    questions: list[ExtractionQuestion] = []
    for i, q in enumerate(raw_questions):
        base = f"$.questions[{i}]"
        if not isinstance(q, dict):
            _err(base, f"is {type(q).__name__}, expected object")
        qtext = _check_str(base + ".question_text", q.get("question_text"),
                           max_len=MAX_KNOWLEDGE_TEXT_CHARS)
        subject = q.get("subject")
        if subject not in taxonomy.SUBJECTS:
            _err(base + ".subject", f"is {subject!r}, not in the subject taxonomy")
        fmt = q.get("question_format")
        if fmt not in taxonomy.QUESTION_FORMATS:
            _err(base + ".question_format",
                 f"is {fmt!r}, expected one of {taxonomy.QUESTION_FORMATS}")
        ans_status = q.get("answer_status")
        if ans_status not in taxonomy.ANSWER_STATUSES:
            _err(base + ".answer_status",
                 f"is {ans_status!r}, expected one of {taxonomy.ANSWER_STATUSES}")
        options = q.get("options")
        if options is None:
            options = {}
        if not isinstance(options, dict):
            _err(base + ".options",
                 f"is {type(options).__name__}, expected object or null")
        for k, v in options.items():
            if not isinstance(v, str):
                _err(base + f".options.{k}",
                     f"is {type(v).__name__}, expected string")
        answer = q.get("answer")
        if ans_status == "STATED_BY_SOURCE":
            if answer is None or not str(answer).strip():
                _err(base + ".answer",
                     "is null while answer_status is STATED_BY_SOURCE — "
                     "never claim a stated answer that does not exist")
            if isinstance(options, dict) and options and str(answer) not in options:
                _err(base + ".answer",
                     f"{answer!r} is not one of the stated options")
        else:  # NOT_STATED
            if answer is not None:
                _err(base + ".answer",
                     "is non-null while answer_status is NOT_STATED — "
                     "an unstated answer must be null, never invented")
        questions.append(ExtractionQuestion(
            question_text=qtext,
            subject=subject,
            question_format=fmt,
            answer_status=ans_status,
            options=options,
            answer=answer,
            explanation=_check_str(base + ".explanation", q.get("explanation"),
                                   allow_none=True),
            topic=_check_str(base + ".topic", q.get("topic"), allow_none=True),
        ))

    notes = payload.get("notes")
    if notes is not None and not isinstance(notes, str):
        _err("$.notes", f"is {type(notes).__name__}, expected string or null")

    return ExtractionResult(
        relevance=relevance, items=items, questions=questions, notes=notes
    )
