"""Read-only standalone English RPH lookup for Years 1–3.

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


def load_english_rph(year, lesson_no):
    """Load an approved standalone lesson for English Years 1, 2 or 3."""
    year_number = _valid_number(year)
    number = _valid_number(lesson_no)
    if year_number not in (1, 2, 3) or number is None or not 1 <= number <= LESSON_COUNT:
        return None
    path = LESSON_ROOT / f"year{year_number}" / f"lesson_{number:03d}.md"
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not content.strip() or not re.search(r"(?im)^#{1,2}[^\n]*\blesson\s*0*" + str(number) + r"\b", content):
        return None
    return content


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
    """Prefer standalone English Years 1–3; otherwise preserve legacy behaviour."""
    if not callable(legacy_generator):
        raise TypeError("legacy_generator must be callable")
    standalone = get_english_rph(year, subject, lesson_no)
    if standalone is not None:
        return standalone
    return legacy_generator(*args, **kwargs)
