"""Read-only RPT 2027 week/date audit against CikguLaju's central A/B master.

Makes NO guessed date changes. It explicitly reports unknown and conflicting
allocations; a correct PDF renderer is not evidence of a verified calendar.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from scripts.build_rpt_2027_standard_preview import moral_records, psv_records, rbt_records
from scripts.build_rpt_2027_second_batch_preview import sejarah_records, pjpk_records

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "rpt_2027/common/calendar_week_2027_a_b_snapshot_20261107_DRAF.json"
OUTPUT = ROOT / "staging/rpt_2027_seragam_2026/audit_calendar_week_alignment.json"


def read_master():
    obj = json.loads(MASTER.read_text(encoding="utf-8"))
    if obj.get("status") != "DRAF_REFERENCE_NOT_RELEASE_SIGNOFF":
        raise ValueError("Calendar release status unexpected")
    result = {}
    for group in ("A", "B"):
        rows = obj["weeks"][group]
        by_week = {row["week"]: row for row in rows if re.fullmatch(r"M\d{2}", row["week"])}
        if len(rows) != 48 or len(by_week) != 44:
            raise ValueError(f"Invalid master week calendar for {group}")
        if by_week["M01"]["start"] != "2027-01-04" or by_week["M44"]["end"] != (
            "2027-12-02" if group == "A" else "2027-12-03"
        ):
            raise ValueError("Calendar master does not align with confirmed KPM boundaries")
        result[group] = by_week
    return result


def audit_rows(subject, year, rows, master):
    report = {"subject": subject, "year": year, "total_pdp": len(rows),
              "status_counts": {}, "examples": []}
    tally = Counter()
    for row in rows:
        raw_week = row.get("week") or ""
        found = re.match(r"^(M\d{2})(?!\d)", raw_week.strip())
        dates = {g: (row.get(g.lower() + "_start") or "",
                     row.get(g.lower() + "_end") or "") for g in ("A", "B")}
        if not found:
            category = "no_week_with_candidate_dates" if any(any(x) for x in dates.values()) else "no_week_no_dates"
        else:
            week = found.group(1)
            if any(week not in master[g] for g in ("A", "B")):
                category = "unrecognized_week"
            elif any(not all(pair) for pair in dates.values()):
                category = "week_known_but_missing_group_dates"
            elif (subject == "sejarah" and row.get("calendar_alignment") ==
                  "GROUP_A_FIRST_DAY_KPM_HOLIDAY_INDEXED" and
                  dates["B"] == (master["B"][week]["start"], master["B"][week]["end"]) and
                  dates["A"][1] == master["A"][week]["end"] and
                  (date.fromisoformat(dates["A"][0]) -
                   date.fromisoformat(master["A"][week]["start"])).days == 1):
                category = "sejarah_group_a_kpm_holiday_indexed"
            elif any(dates[g] != (master[g][week]["start"], master[g][week]["end"])
                     for g in ("A", "B")):
                # A source may label the Nth taught lesson as MNN, even when
                # the central school week skips a cuti. Suggest RELABEL ONLY
                # if both A and B date pairs match one unique official week.
                matched = [
                    candidate for candidate in master["A"]
                    if candidate in master["B"] and
                    all(dates[g] == (master[g][candidate]["start"],
                                     master[g][candidate]["end"])
                        for g in ("A", "B"))
                ]
                category = ("source_week_label_conflicts_with_master"
                            if len(matched) == 1 else "week_and_date_mismatch")
            else:
                if subject == "sejarah" and row.get("calendar_alignment") == "EXACT_SOURCE_DATE_PAIR":
                    category = "sejarah_week_derived_from_candidate_dates"
                elif row.get("source_week") and row["source_week"] != week:
                    category = "week_label_reconciled_from_master"
                else:
                    category = "aligned_to_master_week"
        tally[category] += 1
        if category != "aligned_to_master_week" and len(report["examples"]) < 12:
            example = {
                "pdp": row.get("display_id") or row["id"],
                "week": raw_week, "category": category,
                "a_start": dates["A"][0], "a_end": dates["A"][1],
                "b_start": dates["B"][0], "b_end": dates["B"][1],
            }
            if category == "source_week_label_conflicts_with_master":
                example["suggested_master_week_label_only"] = matched[0]
            if category == "week_label_reconciled_from_master":
                example["source_original_week"] = row["source_week"]
                example["display_week"] = row["week"]
            if subject == "sejarah" and row.get("calendar_alignment"):
                example["source_calendar_alignment"] = row["calendar_alignment"]
            report["examples"].append(example)
    report["status_counts"] = dict(sorted(tally.items()))
    report["requires_review"] = any(category != "aligned_to_master_week" for category in tally)
    return report


def audit_all():
    master = read_master()
    result = []
    for subject, years, loader in (
        ("psv", range(2, 7), psv_records),
        ("rbt", range(4, 7), rbt_records),
        ("moral", range(2, 7), moral_records),
        ("sejarah", range(4, 7), sejarah_records),
        ("pjpk", range(2, 7), pjpk_records),
    ):
        for year in years:
            result.append(audit_rows(subject, year, loader(year), master))
    if len(result) != 21:
        raise ValueError("Missing year/subject coverage in master calendar audit")
    overall = Counter()
    for record in result:
        overall.update(record["status_counts"])
    return {
        "year": 2027,
        "status": "AUDIT_ONLY_NOT_FINAL_RELEASE",
        "master_source": str(MASTER.relative_to(ROOT)),
        "total_pdfs": len(result),
        "total_pdp": sum(row["total_pdp"] for row in result),
        "overall_counts": dict(sorted(overall.items())),
        "release_gate": "BLOCKED" if any(row["requires_review"] for row in result) else
                        "CALENDAR_WEEK_ALIGNED_ONLY_NOT_CURRICULUM_APPROVAL",
        "by_pdf": result,
    }


if __name__ == "__main__":
    result = audit_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print("RPT date audit:", result["overall_counts"])
    print("Release gate:", result["release_gate"])
    for item in result["by_pdf"]:
        print(f"{item['subject'].upper()} T{item['year']}: {item['status_counts']}")
