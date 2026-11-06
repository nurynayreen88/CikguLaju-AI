"""Non-destructive display-week relabeling from KPM-aligned A/B date pairs.

The source's original week stays in the record for audit. No dates, PdP IDs
or curriculum data are touched.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "rpt_2027/common/calendar_week_2027_a_b_snapshot_20261107_DRAF.json"


def load_calendar_weeks():
    source = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    if source.get("status") != "DRAF_REFERENCE_NOT_RELEASE_SIGNOFF":
        raise ValueError("Unsupported calendar week snapshot")
    weeks = {}
    for group in ("A", "B"):
        data = source["weeks"][group]
        weeks[group] = {x["week"]: (x["start"], x["end"]) for x in data
                        if re.fullmatch(r"M\d{2}", x["week"])}
        if len(weeks[group]) != 44:
            raise ValueError("Central school week data incomplete")
    return weeks


def matching_master_weeks(row, master):
    return [
        week for week, a in master["A"].items()
        if week in master["B"]
        and a == (row.get("a_start"), row.get("a_end"))
        and master["B"][week] == (row.get("b_start"), row.get("b_end"))
    ]


def reconcile_psv_weeks(rows):
    """Use verified A/B date pairs to correct *display* week labels only.

    Raises on unknown or ambiguous dates rather than inventing week numbers.
    Source row order and all four A/B dates remain invariant.
    """
    master = load_calendar_weeks()
    for row in rows:
        original = row.get("week", "").strip()
        matches = matching_master_weeks(row, master)
        if len(matches) != 1 or not re.fullmatch(r"M\d{2}", original):
            raise ValueError(f"PSV PdP {row['id']} has unsupported calendar dates/week")
        mapped = matches[0]
        if original != mapped:
            row["source_week"] = original
            row["week"] = mapped
            row["week_reconciliation"] = "DISPLAY_WEEK_FROM_KPM_MASTER; SOURCE_UNCHANGED"
    return rows
