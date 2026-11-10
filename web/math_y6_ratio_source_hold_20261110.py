"""Protect native Web Mathematics Year 6 downloads from known false SK/SP.

Exact legacy Telegram source identities were audited against the September
2021 KPM KSSR DSKP Mathematics Year 6 p.56: 7.2 Nisbah, 7.3 Kadaran,
7.4 Penyelesaian masalah. 8.x covers data/probability, not ratio.

This module does NOT correct SK/SP by guess, edit the primary database,
affect Telegram's direct bot flow, touch credits, or release academic drafts.
Only the six already-audited sequence IDs with their original wrong 8.x
source codes are held. If the authoritative source is later corrected, the
same lesson is automatically released by this guard without a database edit.
"""
from __future__ import annotations

import re

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
_SP = re.compile(r"(?<![\d.])\d{1,2}\.\d{1,2}\.\d{1,2}(?![\d.])")


def held_math_y6_ratio_source(year, subject, pdp_code, rows):
    """True only for an exact known bad source identity and bad SP set.

    The runtime source and the currently selected PdP must both match.
    No release is inferred for an incomplete or unparseable group: the
    existing native bridge's SK/SP validation handles such cases.
    """
    if type(year) is not int or year != 6 or subject != "MATH":
        return False
    bad = _BAD_SP_SETS.get(pdp_code)
    if bad is None or not isinstance(rows, list) or not rows:
        return False
    if not all(isinstance(row, dict) and
               str(row.get("pdp_sequence_code") or "").strip() == pdp_code
               for row in rows):
        return False
    codes = set()
    for row in rows:
        raw = str(row.get("sp_code") or "")
        codes.update(_SP.findall(raw))
    return bool(codes) and frozenset(codes) == bad
