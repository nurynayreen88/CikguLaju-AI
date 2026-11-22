"""Teacher-authored reflection for the native RPH document renderer."""

import re
import unicodedata

# Auto/Manual selects the Web input mode; it must never appear on printed RPH labels.
_REFLEKSI_MODE_SUFFIX = re.compile(
    r"^\s*refleksi\s*\(\s*auto(?:matik)?\s*/\s*manual\s*\)\s*$", re.IGNORECASE
)


def normalize_reflection_row_labels(rows):
    """Remove a UI-only suffix from the native RPH row key; preserve its text."""
    if not isinstance(rows, dict):
        return rows
    variants = [key for key in rows if isinstance(key, str) and _REFLEKSI_MODE_SUFFIX.fullmatch(key)]
    if not variants:
        return rows
    corrected = dict(rows)
    canonical = corrected.get("REFLEKSI", "")
    for key in variants:
        candidate = corrected.pop(key)
        if not canonical:
            canonical = candidate
    corrected["REFLEKSI"] = canonical
    return corrected


MAX_REFLECTION_LENGTH = 500
MAX_REFLECTION_LINES = 6
TEACHER_FIELDS = {"class", "date", "time", "students"}


def clean_reflection(value):
    if not isinstance(value, str) or len(value) > MAX_REFLECTION_LENGTH:
        raise ValueError("Invalid reflection length")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    if any(c not in "\n\t" and unicodedata.category(c) in {"Cc", "Cs"} for c in value):
        raise ValueError("Invalid reflection characters")
    value = value.strip()
    if value.count("\n") >= MAX_REFLECTION_LINES:
        raise ValueError("Too many reflection lines")
    return value


def valid_teacher_fields(teacher, *, legacy=False):
    if not isinstance(teacher, dict):
        return False
    keys = set(teacher) - {"reflection"}
    return keys == TEACHER_FIELDS or (legacy and keys == TEACHER_FIELDS - {"students"})


def install(runtime):
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False

    def rows(state, *args, **kwargs):
        result = normalize_reflection_row_labels(previous(state, *args, **kwargs))
        reflection = state.get("rph_teacher_reflection")
        if reflection:
            return {**result, "REFLEKSI": reflection}
        return result

    runtime._rph_rows = rows
    return True
