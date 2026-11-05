#!/usr/bin/env python3
"""Read-only exact source-text check against the 5 original Moral DSKP PDFs.

Fingerprint fixture was computed once from the original PDF text, not from
GitHub's crosswalk. No user database, app runtime or DRAF flag is changed.
This verifies SP language, NOT textbook activity-page / calendar approval.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "audits/pendidikan_moral_official_dskp_350sp_fingerprints_20261105.json"
RPT = ROOT / "rpt_2027/pendidikan_moral"


def normalize(value: str) -> str:
    return re.sub(r"[^\w]+", " ", value.lower().strip()).strip().replace("_", " ")


def run() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(data["years"]) == {str(y) for y in range(2, 7)}
    counts = {"year": 0, "units": 0, "sp": 0, "book_heading": 0}
    for year in range(2, 7):
        expected = data["years"][str(year)]
        mapping = json.loads((RPT / f"year{year}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
        toc = json.loads((RPT / f"year{year}_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
        assert mapping["source_dskp_id"] == expected["original_dskp_drive_id"], year
        assert mapping["status"] == "DRAF_SEMAK", year
        assert toc["source_drive_file_id"] == mapping["source_book_id"], year
        assert toc["status"] == "VERIFIED_TOC_START_ONLY", year
        assert len(mapping["units"]) == len(toc["units"]) == 14, year
        assert len(expected["unit_sp_sha256_prefix_24"]) == 14, year
        first_page = expected["pdf_first_unit_page_1based"]
        for i, (unit, book) in enumerate(zip(mapping["units"], toc["units"]), 1):
            assert unit["unit"] == book["unit"] == i, (year, i)
            codes = [f"{i}.{s}" for s in range(1, 6)]
            assert [row["code"] for row in unit["sp"]] == codes, (year, i)
            src = "|".join(normalize(row["text"]) for row in unit["sp"])
            digest = hashlib.sha256(src.encode("utf-8")).hexdigest()[:24]
            assert digest == expected["unit_sp_sha256_prefix_24"][i - 1], (
                year, i, "SP text drift from original DSKP", codes,
            )
            assert first_page + i - 1 >= first_page
            assert book["printed_start_page"] + toc["pdf_page_offset"] == book["pdf_start_page"], (year, i)
            assert book["printed_heading_original"], (year, i, "book opener heading not sighted")
            assert book["heading_verification_scope"] == "BOOK_OPENING_PAGE_VISUAL_ONLY", (year, i)
            assert 1 <= book["pdf_start_page"] <= toc["book_pdf_page_count"], (year, i)
            counts["units"] += 1
            counts["sp"] += 5
            counts["book_heading"] += 1
        counts["year"] += 1
        print(f"PASS Tahun {year}: 14 DSKP source-text units, 70 SP and 14 scanned-book unit headings")
    assert counts == {"year": 5, "units": 70, "sp": 350, "book_heading": 70}, counts
    print("PASS ORIGINAL KPM DSKP FINGERPRINT AUDIT:", counts)
    print("BOOK CAVEAT: an opening-page heading is not evidence of exact SP-linked textbook activities")


if __name__ == "__main__":
    run()
