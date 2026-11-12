"""Staging-only RBT 2027 PDF title guard: repair sourced 99-character cuts.

Some RPT/RPH CSV titles stop mid-word at a legacy 99-character boundary.
Replace *only their PDF display titles* with exact full official SK-aligned
first SP wording already loaded into the sourced DSKP crosswalk.
Never edit source CSV, RPH, SK, SP, dates, or release status.
"""
from __future__ import annotations

import re

EXPECTED_INCOMPLETE = {
    4: {3, 17, 19, 21, 28, 30},
    5: {5, 10, 14, 29},
    6: {18, 22},
}


def expand_rbt_display_titles(year, source_rows, display_rows):
    if year not in EXPECTED_INCOMPLETE or len(source_rows) != 32 or len(display_rows) != 32:
        raise ValueError("Unrecognized RBT year/source count")
    fixed = set()
    for n, (source, row) in enumerate(zip(source_rows, display_rows), 1):
        if int(source["PdP"]) != n or row["id"] != f"{n:03d}":
            raise ValueError("RBT source/display PdP order mismatch")
        raw = source["Tajuk PdP"]
        stripped = re.sub(r"^PdP\s+0*" + str(n) + r"\s*[:：—–-]\s*", "", raw, flags=re.I)
        if stripped != row["topic"]:
            raise ValueError(f"RBT T{year} PdP {n:03d}: source topic altered before repair")
        sp_code = source["SP"].split("/")[0].strip()
        head = row["sp_display"].split("\n")[0]
        prefix = sp_code + " — "
        if not head.startswith(prefix):
            raise ValueError("RBT official DSKP SP display absent")
        official = head[len(prefix):].strip()
        raw_check = stripped.rstrip(" .:").casefold()
        official_check = official.rstrip(" .:").casefold()
        incomplete = (
            len(raw) == 99 and
            ((official_check.startswith(raw_check) and len(official_check) > len(raw_check))
             or (raw_check.startswith(official_check) and len(raw_check) > len(official_check)))
        )
        if incomplete:
            row["source_topic"] = stripped
            row["topic"] = official
            row["topic_display_status"] = "FULL_DSKP_SP_EXACT_STAGING_ONLY"
            fixed.add(n)
    if fixed != EXPECTED_INCOMPLETE[year]:
        raise ValueError(f"RBT T{year} title regression: found {sorted(fixed)}, "
                         f"expected {sorted(EXPECTED_INCOMPLETE[year])}")
    return display_rows
