#!/usr/bin/env python3
"""Read-only 30-draft Bahasa Arab Year 2–6 staging preflight. NOT a release test."""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = ROOT / "rph_standalone" / "bahasa_arab"
RPT = ROOT / "rpt_2027" / "bahasa_arab"
MANIFEST = SUBJECT / "source_manifest_20261105.json"
EXPECTED_SP = {
    2: ["1.1.1", "1.1.2", "1.2.1", "2.1.1", "2.2.1", "3.1.1"],
    3: ["1.1.1", "1.1.2", "1.2.1", "2.1.1", "2.2.1", "3.1.1"],
    4: ["1.1.1", "1.1.2", "1.2.1", "2.1.1", "2.2.1", "3.1.1"],
    5: ["1.1.1", "1.1.2", "1.2.1", "2.1.1", "2.2.1", "3.2.1"],
    6: ["1.1.1", "1.1.2", "1.2.1", "2.1.1", "2.2.1", "3.1.1"],
}
FOCUS_UNIT_1 = {
    2: "هيا نتعارف",
    3: "تفضل إلى الفصل",
    4: "الشهور الميلادية",
    5: "في المطبخ",
    6: "حياتنا أجمل بالنظافة",
}

def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))

def src_url_not_empty(content: str) -> bool:
    return "https://anyflip.com/" in content

def check() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["release_status"] == "DRAF_STAGING_SAHAJA"
    assert data["total_final_ready_rph"] == 0
    assert all(data[x] is False for x in ("production_db_touched", "telegram_live_touched", "web_live_touched"))
    assert sorted(data["years"]) == [str(y) for y in range(2, 7)]
    units = read_csv(RPT / "unit_sequence_DRAF_20261105.csv")
    assert len(units) == 20
    assert Counter(int(row["tahun"]) for row in units) == Counter({y: 4 for y in range(2, 7)})
    assert all(row["status"] == "DRAF_SEMAK" and row["pdp_ready"] == "FALSE" for row in units)
    assert {(int(row["tahun"]), int(row["unit"])) for row in units} == {(y,i) for y in range(2,7) for i in range(1,5)}
    assert next(row["tajuk_arab"] for row in units if row["tahun"]=="3" and row["unit"]=="4") == "الزمان"
    lessons = read_csv(RPT / "pdp_001_006_DRAF.csv")
    assert len(lessons) == 30
    assert all(row["status"] == "DRAF_SEMAK" and row["ready"] == "FALSE" and row["halaman_buku_disahkan"] == "FALSE" for row in lessons)
    lesson_map = {(int(row["tahun"]), int(row["pdp"])): row for row in lessons}
    assert len(lesson_map) == 30
    checked = 0
    for year in range(2, 7):
        info = data["years"][str(year)]
        assert info["provisional_rph_count"] == 6
        assert info["textbook"]["source_page_verified"] is False
        for lesson in range(1, 7):
            path = SUBJECT / f"year{year}" / f"lesson_{lesson:03d}.md"
            content = path.read_text(encoding="utf-8")
            record = lesson_map[(year, lesson)]
            assert record["sp"] == EXPECTED_SP[year][lesson-1]
            assert record["unit"] == "1"
            assert f"Bahasa Arab Tahun {year}" in content, path
            assert f"PdP {lesson:03d}" in content, path
            assert FOCUS_UNIT_1[year] in content, path
            for heading in ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Penutup", "BBM", "PBD", "Kriteria kejayaan", "Refleksi"):
                assert heading in content, (path, heading)
            assert "DRAF" in content and "BELUM READY" in content and "READY" in content
            assert record["sp"] in content and info["rpt_2026"] in content
            assert len(content) >= 1100, (path, "RPH too short")
            checked += 1
    bank_checked = 0
    for year in range(2, 7):
        for unit in range(2, 5):
            path = ROOT / "materials" / "bahasa_arab" / f"year{year}" / f"unit_{unit:02d}_activity_bank_DRAF.md"
            content = path.read_text(encoding="utf-8")
            assert f"Bahasa Arab Tahun {year}" in content
            assert "Bukti PBD" in content
            assert "DRAF_SEMAK" in content and "BELUM READY" in content
            assert src_url_not_empty(content)
            bank_checked += 1
    assert bank_checked == data["additional_unit_activity_bank_count"] == 15
    print(f"PASSED: {len(units)} unit placeholders, {len(lessons)} RPT-PdP rows, {checked} RPH drafts, {bank_checked} activity banks.")
    print("RELEASE BLOCKED: 0 FINAL READY; textbook-page, native render, manual approval pending.")

if __name__ == "__main__":
    check()
