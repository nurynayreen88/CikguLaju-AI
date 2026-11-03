"""Read-only standalone English RPH lookup for Years 1–4.

The bot must explicitly call resolve_rph_with_fallback to opt in.
Missing lessons retain the legacy fallback; other subjects are unaffected.
"""
from pathlib import Path
import re

LESSON_ROOT = Path(__file__).resolve().parent / "rph_standalone" / "english"
LESSON_COUNT = 160


def _valid_number(value):
    if isinstance(value, bool):
        return None
    raw = str(value).strip()
    if not raw.isascii() or not raw.isdigit():
        return None
    return int(raw)


def _strip_internal_review_notes(content):
    """Keep audit notes in source files, not in teacher-facing lesson output."""
    lines = content.splitlines(keepends=True)
    cleaned = []
    skipping = False
    for line in lines:
        if re.match(r"(?i)^\s*(?:\*\*)?(?:QA(?: status)?|Status|Internal review):(?:\*\*)?", line):
            skipping = True
            continue
        if skipping and re.match(r"^#{1,3}\s+", line):
            skipping = False
        if not skipping:
            cleaned.append(line)
    return "".join(cleaned).rstrip() + "\n"


def load_english_rph(year, lesson_no):
    """Load a standalone lesson for English Years 1, 2, 3 or 4. Approval is separate."""
    year_number = _valid_number(year)
    number = _valid_number(lesson_no)
    if year_number not in (1, 2, 3, 4) or number is None or not 1 <= number <= LESSON_COUNT:
        return None
    path = LESSON_ROOT / f"year{year_number}" / f"lesson_{number:03d}.md"
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not content.strip() or not re.search(r"(?im)^#{1,2}[^\n]*\blesson\s*0*" + str(number) + r"\b", content):
        return None
    return _strip_internal_review_notes(content)


def load_english_y1_rph(lesson_no):
    return load_english_rph(1, lesson_no)


def get_english_rph(year, subject, lesson_no):
    subject_key = re.sub(r"[^a-z]", "", str(subject).casefold())
    if subject_key not in {"english", "bahasainggeris", "bi"}:
        return None
    return load_english_rph(year, lesson_no)


def get_english_y1_rph(year, subject, lesson_no):
    if _valid_number(year) != 1:
        return None
    return get_english_rph(year, subject, lesson_no)


def resolve_rph_with_fallback(year, subject, lesson_no, legacy_generator, *args, **kwargs):
    """Prefer standalone English Years 1–4; otherwise preserve legacy behaviour."""
    if not callable(legacy_generator):
        raise TypeError("legacy_generator must be callable")
    standalone = get_english_rph(year, subject, lesson_no)
    if standalone is not None:
        return standalone
    return legacy_generator(*args, **kwargs)
