"""Read-only source coverage audit for 342 historical Sains RPT 2027 PdP.

Only answers whether Unit 1/2 entries appear in *this particular 342-PdP
candidate*, not whether the official DSKP curriculum or other project sources
contain those units. Never synthesize lessons or mark candidate as READY.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import re

from scripts.build_rpt_2027_sains_342_actual_source_staging import source_records

COUNTS = {2: 51, 3: 45, 4: 79, 5: 83, 6: 84}
UNIT_PATTERN = re.compile(r"(?i)\bunit\s+(\d{1,2})\b")


def coverage_report():
    years = source_records()
    if set(years) != set(COUNTS):
        raise ValueError("Sains 2027 source cohort changed; re-audit manually")
    report = {
        "scope": "342 historical Sains PdP staging candidate ONLY",
        "release_ready": False,
        "source_unit_coverage_not_equivalent_to_official_dskp_completeness": True,
        "full_academic_verification_required": True,
        "year1_transition_unchanged": True,
        "years": {},
    }
    for year, rows in sorted(years.items()):
        if len(rows) != COUNTS[year]:
            raise ValueError(f"Tahun {year} source count changed; re-audit")
        units = []
        for row in rows:
            match = UNIT_PATTERN.search(str(row.get("unit") or ""))
            if not match:
                raise ValueError(f"Tahun {year} PdP{row['id']} has no unit label")
            units.append(int(match.group(1)))
        numbered = [int(row["id"]) for row in rows]
        if numbered != list(range(1, COUNTS[year] + 1)):
            raise ValueError(f"Tahun {year} lesson ID sequence unexpected")
        tally = Counter(units)
        first = min(tally)
        absent_early = list(range(1, first))
        unverified = sum(not bool(row.get("curriculum_text_matched")) or
                         not bool(row.get("academic_release_approved"))
                         for row in rows)
        report["years"][str(year)] = {
            "pdp_count": len(rows),
            "first_source_pdp": rows[0]["id"],
            "first_unit": units[0],
            "observed_units": sorted(tally),
            "pdp_per_unit": {str(k): tally[k] for k in sorted(tally)},
            "early_unit_labels_absent_from_342_source": absent_early,
            "unverified_source_pdp_count": unverified,
            "source_m01_pdp_count": sum(row.get("week") == "M01" for row in rows),
            "academic_release_ready": False,
            "reason": ("The 342-PdP source lacks early unit rows and has no "
                       "independent academic SP-to-PdP signoff. This does NOT "
                       "prove those units are absent from other Sains sources."),
        }
    if sum(entry["pdp_count"] for entry in report["years"].values()) != 342:
        raise ValueError("Historical science 342-PdP total changed")
    if not all(entry["early_unit_labels_absent_from_342_source"] and
               not entry["academic_release_ready"]
               for entry in report["years"].values()):
        raise ValueError("Historical science release guard needs fresh audit")
    return report


if __name__ == "__main__":
    output = Path("staging/rpt_2027_seragam_2026/sains_342_front_unit_coverage_20261110.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    report = coverage_report()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "release_ready": report["release_ready"],
        "total_source_pdp": 342,
        "missing_unit_labels_by_year": {
            year: entry["early_unit_labels_absent_from_342_source"]
            for year, entry in report["years"].items()},
        "output": str(output),
    }, ensure_ascii=False))
