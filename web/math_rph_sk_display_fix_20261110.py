"""Presentation-only repair for exact duplicate Mathematics SK prefixes.

The native grouped SP resolver already retains authoritative SK/SP identities.
Its legacy text construction can display the same SK twice (e.g. "4.4 4.4
Darab wang"). Fix only the rendered RPH field, never its curriculum source,
lesson title, time allocation, objectives, user state, or other subjects.
"""
from __future__ import annotations

import re

# Only a complete repeated SK at the BEGINNING of a semicolon-delimited
# standard is redundant. Never equate 4.4 with SP 4.4.1 or remove numbers
# appearing in the actual curricular description.
_DUPLICATE_SK_PREFIX = re.compile(
    r"^(\s*)(\d{1,2}\.\d{1,2})([ \t]+)\2(?=[ \t]|$)"
)
_FLAG = "_CIKGULAJU_MATH_SK_DISPLAY_20261110"


def clean_duplicate_sk_prefixes(value):
    """Return source text with only adjacent identical SK labels collapsed."""
    if not isinstance(value, str) or not value:
        return value
    chunks = re.split(r"(;)", value)
    for index, chunk in enumerate(chunks):
        if chunk == ";":
            continue
        chunks[index] = _DUPLICATE_SK_PREFIX.sub(
            lambda match: match.group(1) + match.group(2), chunk, count=1
        )
    return "".join(chunks)


def install(runtime):
    """Patch the shared Word/PDF RPH row boundary for Mathematics only."""
    if getattr(runtime, _FLAG, False):
        return False
    original = getattr(runtime, "_rph_rows", None)
    if not callable(original):
        raise TypeError("Native RPH row constructor unavailable")

    def math_rows_with_clean_sk(state, *args, **kwargs):
        rows = original(state, *args, **kwargs)
        if not isinstance(state, dict):
            return rows
        if str(state.get("subject") or "").strip().casefold() != "matematik":
            return rows
        if not isinstance(rows, dict):
            return rows
        raw = rows.get("STANDARD KANDUNGAN")
        cleaned = clean_duplicate_sk_prefixes(raw)
        if raw == cleaned:
            return rows
        result = dict(rows)
        result["STANDARD KANDUNGAN"] = cleaned
        return result

    runtime._rph_rows = math_rows_with_clean_sk
    setattr(runtime, _FLAG, True)
    return True
