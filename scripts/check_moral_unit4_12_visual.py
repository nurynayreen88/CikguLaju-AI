#!/usr/bin/env python3
"""Read-only check: 12 visually book-aligned Moral RPH Y2–5, Unit 4."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/pendidikan_moral_unit4_y2_y5_12_visual_20261104.json"

def main():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = data["entries"]
    assert len(entries) == 12
    expected_set = {(y, n) for y in range(2,6) for n in (10,11,12)}
    assert {(e["year"], e["lesson"]) for e in entries} == expected_set
    for item in entries:
        y, n = item["year"], item["lesson"]
        toc = json.loads((ROOT / f"rpt_2027/pendidikan_moral/year{y}_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
        cross = json.loads((ROOT / f"rpt_2027/pendidikan_moral/year{y}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
        assert toc["source_drive_file_id"] == item["book_file_id"]
        f, t = item["printed"]
        offset = toc["pdf_page_offset"]
        assert item["pdf"] == [f + offset, t + offset]
        assert toc["units"][3]["printed_start_page"] <= f <= t < toc["units"][4]["printed_start_page"]
        need = cross["units"][3]["sp"]
        need = need[:2] if n == 10 else need[2:4] if n == 11 else need[4:]
        assert [s["code"] for s in need] == item["sp_codes"]
        path = ROOT / f"rph_standalone/pendidikan_moral/year{y}/lesson_{n:03d}.md"
        s = path.read_text(encoding="utf-8")
        assert f"m/s {f}–{t} (PDF {f+offset}–{t+offset})" in s, path
        for sp in need:
            assert sp["code"] in s and sp["text"] in s, (path, sp)
        for part in ("Set induksi", "Aktiviti 1", "Aktiviti 2",
                     "Pengukuhan/Pentaksiran PBD", "Penutup"):
            assert f"**{part}" in s, (path, part)
        for duration in (5, 10, 20):
            assert f"({duration} minit)" in s, (path, duration)
        for unwanted in ("halaman aktiviti khusus belum", "halaman aktiviti belum disahkan",
                         "halaman aktiviti khusus SP belum dipadankan"):
            assert unwanted.lower() not in s.lower(), (path, unwanted)
    issues = data["source_issues"]
    assert len(issues) == 1 and issues[0]["year"] == 6
    assert issues[0]["status"] == "HOLD_SOURCE_MISMATCH" and issues[0]["lessons"] == [10,11,12]
    print("PASS 12 Moral RPH Years 2–5 Unit 4: DSKP SP, pages, five phases and Year 6 hold")

if __name__ == "__main__":
    main()
