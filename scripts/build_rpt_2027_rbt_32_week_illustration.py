"""Optional RBT 2027 timetable illustration: 32 sessions with sourced week ranges.

This is not a school timetable or a KPM-approved allocation. No source CSV/DB
is edited; the canonical 21 draft PDFs keep RBT dates blank.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows
from scripts.build_rpt_2027_standard_preview import rbt_records

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "staging/rpt_2027_seragam_2026/rbt_32week_SIMULASI"


def rbt_32_week_scenario(year: int, *, start_week: int = 3):
    """Map source PdP 001..032 to 32 consecutive *example* weeks.

    Start week 3 is an editorial scenario, not sourced from a school's timetable
    or from RPT 2026. Caller must not publish this as actual timetable data.
    """
    if year not in (4, 5, 6):
        raise ValueError("Only RBT Years 4–6 supported")
    if not isinstance(start_week, int) or start_week < 1 or start_week + 31 > 44:
        raise ValueError("Example scenario exceeds source calendar's 44 teaching weeks")
    originals = rbt_records(year)
    if len(originals) != 32 or any(
        row.get("week") or any(row.get(field) for field in
        ("a_start", "a_end", "b_start", "b_end"))
        for row in originals
    ):
        raise ValueError("RBT source now has actual allocations: do not replace them with simulation")
    weeks = load_calendar_weeks()
    rows = deepcopy(originals)
    for offset, row in enumerate(rows):
        week = f"M{start_week + offset:02d}"
        a_start, a_end = weeks["A"][week]
        b_start, b_end = weeks["B"][week]
        source_note = row["note"]
        source_suffix = " Tarikh A/B belum dinyatakan dalam sumber; tidak diandaikan."
        if source_note.count(source_suffix) != 1:
            raise ValueError("RBT sourced date warning changed unexpectedly")
        row.update({
            "week": week + " (SIMULASI)",
            "a_start": a_start, "a_end": a_end,
            "b_start": b_start, "b_end": b_end,
            "schedule_status": "EDITORIAL_ILLUSTRATION_NOT_APPROVED",
            "schedule_basis": f"Assume 1 RBT period of 60 minutes per week, starting M{start_week:02d}.",
            "original_week": originals[offset]["week"],
            "original_a_start": originals[offset]["a_start"],
            "original_b_start": originals[offset]["b_start"],
            "source_note": source_note,
            "note": source_note.replace(source_suffix, "", 1) +
                    " SIMULASI SAHAJA: 1 PdP/minggu, hanya JULAT MINGGU;"
                    " bukan tarikh kelas sebenar."
                    " Semak jadual guru, cuti negeri dan tempoh projek."
        })
    validate_rows("rbt", year, rows)
    return rows


def build_all(destination=OUT, *, start_week=3):
    dest = Path(destination)
    produced = []
    for year in (4, 5, 6):
        rows = rbt_32_week_scenario(year, start_week=start_week)
        file = dest / (f"CIKGULAJU_RPT_RBT_TAHUN_{year}_2027_"
                       "32_PDP_MINGGU_SIMULASI_BUKAN_FINAL.pdf")
        build_preview("rbt", year, rows, file)
        produced.append((year, len(rows), file))
    return produced


if __name__ == "__main__":
    for year, count, file in build_all():
        print(f"RBT Year {year}: {count} sourced PdP in SIMULASI -> {file}")
