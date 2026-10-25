"""Read-only adapter for English Year 1 standalone lesson plans.

Call load_english_y1_rph(lesson_no) before the legacy generator.
Returns None when unavailable, so callers can keep their existing fallback.
No database, deployment or bot routing is changed by this module.
"""
from pathlib import Path
import re

LESSON_DIR = Path(__file__).resolve().parent / "rph_standalone" / "english" / "year1"
LESSON_COUNT = 160


def load_english_y1_rph(lesson_no):
    """Return a complete Markdown lesson or None for an invalid/missing lesson."""
    if isinstance(lesson_no, bool) or not str(lesson_no).strip().isascii() or not str(lesson_no).strip().isdigit():
        return None
    number = int(str(lesson_no).strip())
    if not 1 <= number <= LESSON_COUNT:
        return None
    path = LESSON_DIR / f"lesson_{number:03d}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    markers = (
        rf"(?im)^#{{1,2}}\s+[^\n]*\blesson\s*0*{number}\b",
        rf"(?im)^\*\*Lesson:\*\*\s*0*{number}\b",
    )
    if not text.strip() or not any(re.search(pattern, text) for pattern in markers):
        return None
    return text


def get_english_y1_rph(year, subject, lesson_no):
    """Guarded subject/year lookup; never intercepts other subjects or years."""
    if isinstance(year, bool) or not str(year).strip().isascii() or not str(year).strip().isdigit():
        return None
    year_number = int(str(year).strip())
    subject_key = re.sub(r"[^a-z]", "", str(subject).casefold())
    if year_number != 1 or subject_key not in {"english", "bahasainggeris", "bi"}:
        return None
    return load_english_y1_rph(lesson_no)


def resolve_rph_with_fallback(year, subject, lesson_no, legacy_generator, *args, **kwargs):
    """Prefer the stored Year 1 English RPH, otherwise call the legacy generator.

    This is an explicit opt-in integration point for the existing bot handler.
    The handler must pass its original generator callable and arguments unchanged.
    No fallback is invoked when a valid standalone lesson is available.
    """
    if not callable(legacy_generator):
        raise TypeError("legacy_generator must be callable")
    standalone = get_english_y1_rph(year, subject, lesson_no)
    if standalone is not None:
        return standalone
    return legacy_generator(*args, **kwargs)
