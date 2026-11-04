#!/usr/bin/env python3
"""Read-only validation of Year 2–6 Pendidikan Moral draft RPH, BBM and RPT.
Run from repository root: python scripts/check_pendidikan_moral_y2_y6.py
No database, app.py, or runtime configuration is written.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = range(2, 7)
FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)


def check_year(year: int) -> dict:
    ydir = ROOT / "rph_standalone" / "pendidikan_moral" / f"year{year}"
    mdir = ROOT / "materials" / "pendidikan_moral" / f"year{year}"
    rdir = ROOT / "rpt_2027" / "pendidikan_moral"
    crosswalk = rdir / f"year{year}_crosswalk_DSKP.json"
    rpt = rdir / f"year{year}_sequence_DRAF.csv"
    if not crosswalk.exists() or not rpt.exists():
        fail(f"Year {year}: crosswalk/RPT missing")
        return {"year": year, "lessons_checked": 0, "materials_checked": 0}
    src = json.loads(crosswalk.read_text(encoding="utf-8"))
    units = src.get("units", [])
    if len(units) != 14:
        fail(f"Year {year}: {len(units)} units, expected 14")
    if src.get("status") != "DRAF_SEMAK":
        fail(f"Year {year}: unexpected crosswalk status")
    checked = 0
    for unit in units:
        n = int(unit.get("unit", 0))
        sp = unit.get("sp", [])
        if len(sp) != 5 or [s["code"] for s in sp] != [f"{n}.{i}" for i in range(1, 6)]:
            fail(f"Year {year} unit {n}: SP coverage mismatch")
            continue
        card = mdir / f"unit_{n:02d}_kad_aktiviti.md"
        if not card.exists():
            fail(f"Year {year} unit {n}: activity card missing")
        else:
            content = card.read_text(encoding="utf-8")
            if any(s["text"] not in content for s in sp):
                fail(f"Year {year} unit {n}: card missing source SP text")
            if "DRAF_SEMAK" not in content:
                fail(f"Year {year} unit {n}: card missing draft status")
        for phase in range(3):
            lnum = (n - 1) * 3 + phase + 1
            lesson = ydir / f"lesson_{lnum:03d}.md"
            if not lesson.exists():
                fail(f"Year {year}: lesson {lnum:03d} missing")
                continue
            content = lesson.read_text(encoding="utf-8")
            expected_sp = sp[phase * 2:phase * 2 + 2] if phase < 2 else sp[4:5]
            for entry in expected_sp:
                if entry["text"] not in content or entry["code"] not in content:
                    fail(f"Year {year} lesson {lnum:03d}: SP {entry['code']} missing")
            mandatory = (
                "Set induksi", "Aktiviti 1", "Aktiviti 2", "Penutup",
                "Pengukuhan/Pentaksiran PBD", "Kriteria kejayaan",
                "BELUM READY", "BBM", "DSKP SK",
            )
            if any(phrase not in content for phrase in mandatory):
                fail(f"Year {year} lesson {lnum:03d}: missing RPH section")
            if re.search(r"PBD:\*\* [A-Za-z] Guru", content):
                fail(f"Year {year} lesson {lnum:03d}: truncated PBD text")
            if len(content) < 1600:
                fail(f"Year {year} lesson {lnum:03d}: suspiciously short")
            checked += 1
    with rpt.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 42 or sorted(int(row["Lesson"]) for row in rows) != list(range(1, 43)):
        fail(f"Year {year}: expected 42 sequential RPT rows")
    for row in rows:
        lnum = int(row["Lesson"])
        unit = 1 + (lnum - 1) // 3
        if row["Status"] != "DRAF_SEMAK" or row["Unit"] != str(unit):
            fail(f"Year {year}: wrong unit/status in RPT {lnum}")
        if row.get("Minggu/Tarikh Kumpulan A") or row.get("Minggu/Tarikh Kumpulan B"):
            fail(f"Year {year}: date filled without final calendar verification")
        if not row.get("Evidens PBD") or len(row["Evidens PBD"]) < 40:
            fail(f"Year {year}: incomplete PBD evidence in RPT {lnum}")
        if not (ROOT / row["RPH"]).exists() or not (ROOT / row["BBM"]).exists():
            fail(f"Year {year}: RPT link points to missing file {lnum}")
    existing_lessons = list(ydir.glob("lesson_*.md"))
    if len(existing_lessons) != 42:
        fail(f"Year {year}: extra/missing RPH files in folder")
    return {"year": year, "lessons_checked": checked, "materials_checked": len(list(mdir.glob("unit_??_kad_aktiviti.md"))), "rpt_rows": len(rows)}


def main() -> int:
    totals = [check_year(year) for year in YEARS]
    for data in totals:
        print(f"Year {data['year']}: {data.get('lessons_checked')} RPH, "
              f"{data.get('materials_checked')} kits, {data.get('rpt_rows', 0)} RPT rows")
    if FAILURES:
        for message in FAILURES:
            print(f"FAIL: {message}")
        print(f"QA failed with {len(FAILURES)} issue(s). Still DRAFT.")
        return 1
    print("PASS: file structure and DSKP/RPT/SP links. DRAFT only; "
          "textbook pages, calendar, print A4 and Telegram remain unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
