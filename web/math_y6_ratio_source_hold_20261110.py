"""Protect native Web Mathematics Year 6 downloads from known false SK/SP.

Exact legacy Telegram source identities were audited against the September
2021 KPM KSSR DSKP Mathematics Year 6 p.56: 7.2 Nisbah, 7.3 Kadaran,
7.4 Penyelesaian masalah. 8.x covers data/probability, not ratio.

This module does NOT correct SK/SP by guess, edit the primary database,
affect Telegram's direct bot flow, touch credits, or release academic drafts.
Only the six already-audited sequence IDs are held until explicit academic
signoff. Changing the codes alone does NOT automatically release an RPH:
objectives, worked exercises and book references must also be verified.
"""
from __future__ import annotations

# Expected old wrong SPs, sourced from
# audits/matematik_y6_semantic_scope_review_expanded_20261108.json
# PR #460 (academic HOLD). Six exact native PdP identities, not a guessed
# lesson/week number.
_BAD_SP_SETS = {
    "MT6-PDP-079": frozenset({"8.1.1"}),                  # Nisbah
    "MT6-PDP-080": frozenset({"8.2.1"}),                  # Kadaran
    "MT6-PDP-081": frozenset({"8.3.1"}),                  # Penyelesaian masalah
    "MT6-PDP-082": frozenset({"8.1.1", "8.2.1", "8.3.1"}),  # Pengukuhan
    "MT6-PDP-083": frozenset({"8.1.1", "8.2.1"}),          # Aplikasi
    "MT6-PDP-084": frozenset({"8.3.1"}),                  # Bukan rutin
}
def held_math_y6_ratio_source(year, subject, pdp_code, rows):
    """True for the six confirmed problematic Year 6 lesson identities.

    Existing bad source SPs are documented in _BAD_SP_SETS as audit evidence.
    Never auto-approve an RPH solely because someone edits its source code:
    content, objective, activities, PBD and textbook must pass signoff.
    Explicitly un-hold a code only in a reviewed future PR.
    """
    if type(year) is not int or year != 6 or subject != "MATH":
        return False
    if pdp_code not in _BAD_SP_SETS or not isinstance(rows, list) or not rows:
        return False
    return all(
        isinstance(row, dict)
        and str(row.get("pdp_sequence_code") or "").strip() == pdp_code
        for row in rows
    )
