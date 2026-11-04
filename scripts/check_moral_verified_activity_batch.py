#!/usr/bin/env python3
"""Read-only QA of 33 source-referenced Moral RPH (Years 2-6).
This validates the audit-to-RPH and DSKP crosswalk, not pedagogical
accuracy of pages that have not been visually checked.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/pendidikan_moral_y2_y6_units02_03_visual_30pdp_20261104.json"
ISSUES = []
def fail(msg: str) -> None:
    ISSUES.append(msg)

def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    records = data["records"]
    if len(records) != 11 or sum(len(u["phases"]) for u in records) != 33:
        fail("Evidence ledger must cover exactly 11 units / 33 lessons")
    verified = set()
    for unit in records:
        year, num = unit["year"], unit["unit"]
        toc = json.loads((ROOT / f"rpt_2027/pendidikan_moral/year{year}_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
        cross = json.loads((ROOT / f"rpt_2027/pendidikan_moral/year{year}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
        book = toc["units"][num - 1]
        expected = cross["units"][num - 1]["sp"]
        offset = toc["pdf_page_offset"]
        next_start = (toc["units"][num]["printed_start_page"] - 1) if num < 14 else toc["book_pdf_page_count"] - offset
        if (unit["printed"][0], unit["pdf"][0]) != (book["printed_start_page"], book["pdf_start_page"]):
            fail(f"Y{year} unit{num}: ledger starts differ from book map")
        if unit["sourceDriveId"] != toc["source_drive_file_id"]:
            fail(f"Y{year} unit{num}: wrong source book ID")
        if len(unit["phases"]) != 3:
            fail(f"Y{year} unit{num}: incomplete phases")
            continue
        for phase, entry in enumerate(unit["phases"]):
            number = (num - 1) * 3 + phase + 1
            if (year, number) in verified:
                fail("duplicate Year 6 lesson")
            rph = ROOT / f"rph_standalone/pendidikan_moral/year{year}/lesson_{number:03d}.md"
            source = rph.read_text(encoding="utf-8")
            page_first, page_last = entry["pages"]
            pdf_first, pdf_last = entry["pdf"]
            if not (book["printed_start_page"] <= page_first <= page_last <= next_start):
                fail(f"Y{year} L{number:03d}: printed activity page outside unit")
            if (pdf_first, pdf_last) != (page_first + offset, page_last + offset):
                fail(f"Y{year} L{number:03d}: printed/PDF page offset mismatch")
            if f"m/s {page_first}–{page_last}" not in source or f"PDF {pdf_first}–{pdf_last}" not in source:
                fail(f"Y{year} L{number:03d}: source pages not preserved")
            if entry["goal"] not in source or entry["a"] not in source or entry["b"] not in source or entry["e"] not in source:
                fail(f"Y{year} L{number:03d}: audited learning steps absent")
            if f"PdP {number:03d}" not in source:
                fail(f"Y{year} L{number:03d}: wrong lesson title")
            needed = expected[phase * 2:phase * 2 + 2] if phase < 2 else expected[4:5]
            if any(s["code"] not in source or s["text"] not in source for s in needed):
                fail(f"Y{year} L{number:03d}: DSKP SP not preserved")
            for name in ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Pengukuhan/Pentaksiran PBD", "Penutup"):
                if not re.search(r"^\\*\\*" + re.escape(name) + r"\\b", source, re.M):
                    fail(f"Y{year} L{number:03d}: missing {name}")
            if "Kriteria kejayaan:" not in source or "DRAF SEMAK" not in source:
                fail(f"Y{year} L{number:03d}: parser contract missing")
            if len(source) < 1800:
                fail(f"Y{year} L{number:03d}: content unexpectedly short")
            verified.add((year, number))
    if len(verified) != 33:
        fail("Expected 33 distinct RPH, got " + str(len(verified)))
    for issue in ISSUES[:50]:
        print("FAIL:", issue)
    print("SOURCE AUDIT:", "PASS" if not ISSUES else "FAIL",
          "| RPH:", len(verified), "| year groups:", len(set(y for y,_ in verified)),
          "| issues:", len(ISSUES))
    print("NOTE: Remaining 177 core RPH not visual-verified; 96h coverage, 2027 calendar and actual Telegram delivery remain unapproved.")
    return int(bool(ISSUES))

if __name__ == "__main__":
    raise SystemExit(main())
