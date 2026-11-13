"""Teacher-authored reflection for the native RPH document renderer."""

import unicodedata

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
    previous = runtime._rph_rows

    def rows(state, *args, **kwargs):
        result = previous(state, *args, **kwargs)
        reflection = state.get("rph_teacher_reflection")
        if reflection:
            return {**result, "REFLEKSI": reflection}
        return result

    runtime._rph_rows = rows
