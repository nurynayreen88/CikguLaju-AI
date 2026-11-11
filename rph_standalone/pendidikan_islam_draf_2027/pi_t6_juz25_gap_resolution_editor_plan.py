"""Editor decision register for the 67 Quran ayat absent from Year-6 RPT Juz 25.

This does not assign extra lessons, alter the source RPT, or replace any
tasmi' target. A Quran/DSKP expert and teacher must decide the duration and
precise lesson allocations before any RPT/RPH redistribution.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from pi_quality_audit import ROOT
from pi_t6_juz25_sequence_gap_audit import audit as source_audit

EXPECTED = (
    (41, 47, 54, 8, "BEFORE_T6_L002",
     "Dahului PdP002 asy-Syura 42:1–32 dengan semakan penutup Fussilat; jangan anggap PdP002 sudah merangkumi lompang ini."),
    (43, 74, 89, 16, "BETWEEN_T6_L014_AND_L018",
     "Tempatkan baki az-Zukhruf selepas PdP014 43:34–73 dan sebelum PdP018 ad-Dukhan 44:40–59, tertakluk kapasiti masa."),
    (44, 1, 39, 39, "BETWEEN_T6_L014_AND_L018",
     "Tempatkan awal ad-Dukhan sebelum PdP018 44:40–59; satu slot sahaja tidak diasumsikan mencukupi untuk 39 ayat."),
    (45, 34, 37, 4, "INSIDE_T6_L026_BOUNDARY",
     "PdP026 melompat daripada al-Jathiyah 45:23–33 terus ke al-Ahqaf 46:1–14 (Juz 26); semak pecahan RPT dan batas juzuk terlebih dahulu."),
)
CSV_FIELDS = (
    "surah", "ayah_first", "ayah_last", "ayah_count", "editor_location_hint",
    "editor_action", "teacher_allocated_lesson", "exact_student_ayah_assignment",
    "teacher_quran_sequence_approved", "content_expert_approved",
    "rpt_changed", "rph_changed", "release"
)


def build(root=ROOT):
    source = source_audit(root)
    rows = []
    observed = source["rows"]
    assert len(observed) == len(EXPECTED) == 4
    for gap, expected in zip(observed, EXPECTED):
        surah, first, last, count, placement, action = expected
        assert (gap["surah_number"], gap["missing_first_ayah"],
                gap["missing_last_ayah"], gap["missing_ayah_count"]) == (
                    surah, first, last, count
                )
        rows.append({
            "surah": surah,
            "ayah_first": first,
            "ayah_last": last,
            "ayah_count": count,
            "editor_location_hint": placement,
            "editor_action": action,
            "teacher_allocated_lesson": None,
            "exact_student_ayah_assignment": None,
            "teacher_quran_sequence_approved": False,
            "content_expert_approved": False,
            "rpt_changed": False,
            "rph_changed": False,
            "release": "NO_GO",
        })
    assert sum(r["ayah_count"] for r in rows) == 67
    assert source["juz25_ayah_assigned_in_rpt"] == 179
    assert source["juz25_expected_ayah_count"] == 246
    assert source["automatic_verse_reassignments"] == 0
    return {
        "subject": "Pendidikan Islam Tahun 6",
        "source_rpt_drive_id": source["rpt_drive_id"],
        "source_rpt_sha256": source["rpt_sha256"],
        "verified_juz25_verse_total": 246,
        "source_rpt_verses_already_referenced": 179,
        "remaining_unassigned_verses": 67,
        "editor_decision_rows": 4,
        "teacher_exact_allocations_approved": 0,
        "new_official_dskp_codes_claimed": 0,
        "source_rpt_modified": False,
        "held_source_rph_modified": False,
        "academic_quality_percent": None,
        "publication": "HOLD",
        "release": "NO_GO",
        "rows": rows,
    }


def write_json_and_csv(output_json, output_csv, root=ROOT):
    result = build(root)
    Path(output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with Path(output_csv).open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(result["rows"])
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()
    write_json_and_csv(args.json, args.csv)
