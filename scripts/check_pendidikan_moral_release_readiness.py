#!/usr/bin/env python3
"""Conservative release audit for Pendidikan Moral Year 2-6.
This does not change databases, menus, or READY flags.
A pass is necessary, not sufficient, for a live Telegram deployment.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSUES = []

def check_year(year):
    base = ROOT / "rph_standalone" / "pendidikan_moral" / f"year{year}"
    rptroot = ROOT / "rpt_2027" / "pendidikan_moral"
    with (rptroot / f"year{year}_sequence_DRAF.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    toc = json.loads((rptroot / f"year{year}_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
    if len(rows) != 42 or len(toc.get("units", [])) != 14:
        ISSUES.append(f"Y{year}: curriculum sequence incomplete")
    if toc.get("status") == "VERIFIED_TOC_START_ONLY":
        ISSUES.append(f"Y{year}: textbook only unit-start mapped, not SP activity pages")
    for lesson in range(1, 43):
        path = base / f"lesson_{lesson:03d}.md"
        if not path.is_file():
            ISSUES.append(f"Y{year} L{lesson:03}: RPH missing")
            continue
        text = path.read_text(encoding="utf-8")
        label = f"Y{year} L{lesson:03}"
        if "DRAF SEMAK" in text or "BELUM READY" in text:
            ISSUES.append(f"{label}: content still marked DRAFT")
        if "Guru membantu murid menggunakan kata tugas asal seperti" in text:
            ISSUES.append(f"{label}: generic activity not an explicit SP task")
        if "halaman aktiviti khusus SP belum dipadankan" in text or "halaman belum dipadankan" in text:
            ISSUES.append(f"{label}: exact textbook activity not verified")
        if "Masa/Kelas/Tarikh:" in text and not all(f"{i} minit" in text for i in (10,15)):
            ISSUES.append(f"{label}: duration not verified against one teaching period")
        if lesson <= len(rows):
            r = rows[lesson-1]
            if r.get("Status") != "READY":
                ISSUES.append(f"{label}: RPT not READY")
            if not (r.get("Minggu/Tarikh Kumpulan A") and r.get("Minggu/Tarikh Kumpulan B")):
                ISSUES.append(f"{label}: 2027 A/B dates missing")

def main():
    for year in range(2,7):
        check_year(year)
    tpath=ROOT/"rpt_2027"/"pendidikan_moral"/"telegram_downloads.py"
    if not tpath.exists():
        ISSUES.append("Telegram paid RPT delivery module missing")
    if not list((ROOT/"rpt_2027"/"pendidikan_moral").glob("*.pdf")):
        ISSUES.append("Teacher-facing 2027 RPT PDF files missing")
    for issue in ISSUES[:45]:
        print("BLOCKER:",issue)
    if len(ISSUES)>45:
        print(f"... {len(ISSUES)-45} more issues")
    print(f"RELEASE GATE: {len(ISSUES)} outstanding issues")
    if ISSUES:
        print("NOT READY: do not merge or deploy to Telegram")
        return 1
    print("Source release gate PASS; separately verify Word/PDF A4 and Telegram end-to-end")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
