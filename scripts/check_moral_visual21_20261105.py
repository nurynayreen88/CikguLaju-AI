#!/usr/bin/env python3
"""Read-only gate for 21 visually reviewed textbook-backed Moral RPH.

Checks the independent source evidence ledger, original drive document ID,
page offset, exact DSKP text and preservation of source-based RPH activities.
Does NOT claim these lessons have been assessed with actual students or made
FINAL READY.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RPT = ROOT / "rpt_2027/pendidikan_moral"
LEDGER = ROOT / "audits/pendidikan_moral_visual21_unit1_unit5_20261105.json"


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = ledger["records"]
    expected = {(y, n) for y in range(2, 7) for n in (1, 2, 3)}
    expected |= {(y, n) for y in (2, 3) for n in (13, 14, 15)}
    assert len(rows) == len(expected) == 21
    assert {(r["year"], r["lesson"]) for r in rows} == expected
    for row in rows:
        year, lesson, unit = row["year"], row["lesson"], row["unit"]
        cross = json.loads((RPT / f"year{year}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
        toc = json.loads((RPT / f"year{year}_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
        assert unit == (lesson - 1) // 3 + 1
        assert toc["source_drive_file_id"] == row["source_book_drive_id"]
        assert ledger["original_book_sha256"][str(year)] == row["book_sha256"]
        p0, p1 = row["printed"]
        f0, f1 = row["pdf"]
        assert [p0 + toc["pdf_page_offset"], p1 + toc["pdf_page_offset"]] == [f0, f1]
        u = toc["units"][unit - 1]
        assert u["printed_start_page"] <= p0 <= p1 < (toc["units"][unit]["printed_start_page"] if unit < 14 else 999), (year, unit)
        path = ROOT / f"rph_standalone/pendidikan_moral/year{year}/lesson_{lesson:03d}.md"
        source = path.read_text(encoding="utf-8")
        assert f"**Bukti visual buku teks (audit 2026-11-05):** Unit {unit}" in source, path
        for page_ref in (f"m/s {p0}–{p1}", f"PDF {f0}–{f1}"):
            assert page_ref in source, (path, page_ref)
        assert "olahan" in source or "diolah" in source, path
        assert "BELUM READY" in source and "DRAF SEMAK" in source, path
        assert "Kriteria kejayaan:" in source and "Pentaksiran PBD" in source, path
        assert "20 minit" in source and "Set induksi" in source and "Penutup" in source
        target = cross["units"][unit - 1]["sp"]
        needed = target[:2] if lesson % 3 == 1 else target[2:4] if lesson % 3 == 2 else target[4:]
        assert row["sp_codes"] == [x["code"] for x in needed], path
        for sp in needed:
            assert sp["code"] in source and sp["text"] in source, (path, sp["code"])
        activities = re.findall(r"^\*\*Aktiviti [12] \(\d+ minit\)[^\n]+", source, flags=re.M)
        assert len(activities) == 2 and all("Guru" in x and "Murid" in x for x in activities), path
        assert len(source) >= 1800, path
    print("PASS 21 Moral RPH: original scan page ranges, SP text, substantive activities and DRAF safety")
    print("REMAINING: 210 core minus 66 = 144 without a specific visual-book task ledger; 270 supplemental still pending task-page audit.")


if __name__ == "__main__":
    main()
