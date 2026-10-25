"""Read-only standalone English RPH lookup for Year 1 and Year 2."""
from pathlib import Path
import re

LESSON_ROOT = Path(__file__).resolve().parent / "rph_standalone" / "english"
LESSON_COUNT = 160


def load_english_rph(year, lesson_no):
    """Read a stored lesson; return None for invalid identifiers or missing files."""
    if isinstance(year, bool) or not str(year).strip().isascii() or not str(year).strip().isdigit():
        return None
    year_number = int(str(year).strip())
    if year_number not in (1, 2):
        return None
    if isinstance(lesson_no, bool) or not str(lesson_no).strip().isascii() or not str(lesson_no).strip().isdigit():
        return None
    number = int(str(lesson_no).strip())
    if not 1 <= number <= LESSON_COUNT:
        return None
    path = LESSON_ROOT / f"year{year_number}" / f"lesson_{number:03d}.md"
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    heading = re.search(r"(?im)^#{1,2}[^\\n]*\\blesson\\s*0*" + str(number) + r"\\b", content)
    metadata = re.search(r"(?im)^\\*\\*Lesson:\\*\\*\\s*0*" + str(number) + r"\\b", content)
    if not content.strip() or not (heading or metadata):
        return None
    return content


def load_english_y1_rph(lesson_no):
    """Retain the original Year 1 API."""
    return load_english_rph(1, lesson_no)


def get_english_rph(year, subject, lesson_no):
    """Only route English Year 1/2 lessons to the stored RPH bank."""
    if isinstance(year, bool) or not str(year).strip().isascii() or not str(year).strip().isdigit():
        return None
    subject_key = re.sub(r"[^a-z]", "", str(subject).casefold())
    if subject_key not in {"english", "bahasainggeris", "bi"}:
        return None
    return load_english_rph(year, lesson_no)


def get_english_y1_rph(year, subject, lesson_no):
    """Retain the original Year 1-only subject API."""
    if str(year).strip() != "1" or isinstance(year, bool):
        return None
    return get_english_rph(year, subject, lesson_no)


def resolve_rph_with_fallback(year, subject, lesson_no, legacy_generator, *args, **kwargs):
    """Return a stored English RPH, otherwise preserve the legacy generator."""
    if not callable(legacy_generator):
        raise TypeError("legacy_generator must be callable")
    standalone = get_english_rph(year, subject, lesson_no)
    if standalone is not None:
        return standalone
    return legacy_generator(*args, **kwargs)
