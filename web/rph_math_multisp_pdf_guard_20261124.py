"""Restore all verified subclauses in native Math PDF without changing Word/DB.

Legacy PDF Paragraph() deduplicates the numeric core of 1.1.1(i),
1.1.1(ii), 1.1.1(iii) as though they were repeated identical standards.
The codes are different standard *subclauses*. Bypass that old formatter
ONLY for the four complete source-verified combined strings in this release.
All PI Jawi, science, other PDFs and unsupported content keep their prior path.
"""
from __future__ import annotations

import re
from web.rph_verified_standard_labels_20261124 import _VERIFIED, _EXTRA_SPS

_FLAG = "_CIKGULAJU_VERIFIED_MATH_SUBCLAUSE_PDF_GUARD_20261124"


def _approved_compounds():
    approved = set()
    for year in (2, 3, 4, 5):
        sk, sk_name, first_code, first_text = _VERIFIED["Matematik", year]
        entries = {first_code: first_text, **_EXTRA_SPS["Matematik", year]}
        # Year 3 starts with (ii); the remaining years begin (i).
        ordered = (
            ("1.1.1(ii)", "1.1.1(iii)") if year == 3
            else ("1.1.1(i)", "1.1.1(ii)", "1.1.1(iii)") if year == 5
            else ("1.1.1(i)", "1.1.1(ii)")
        )
        approved.add("; ".join(f"{code} {entries[code]}" for code in ordered))
    return frozenset(approved)


_VERIFIED_COMPOUNDS = _approved_compounds()


def preserve_math_subclauses(original, previous):
    if not isinstance(original, str):
        return previous(original)
    normalized = " ".join(original.split())
    if normalized in _VERIFIED_COMPOUNDS:
        return normalized
    return previous(original)


def install(runtime):
    if getattr(runtime, _FLAG, False):
        return False
    previous = getattr(runtime, "_dedup_standard_lines_v25216", None)
    if not callable(previous):
        return False

    def guarded_dedup(value):
        return preserve_math_subclauses(value, previous)

    runtime._dedup_standard_lines_v25216 = guarded_dedup
    setattr(runtime, _FLAG, True)
    return True
