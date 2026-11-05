#!/usr/bin/env python3
"""Verify 30 Year4 Moral RPH against independently sighted scanned-book page ledger."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/pendidikan_moral_visual30_y4_u05_u14_20261105.json"
RPT = ROOT / "rpt_2027/pendidikan_moral"

def main():
    x = json.loads(LEDGER.read_text(encoding="utf-8"))
    toc = json.loads((RPT / "year4_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
    cross = json.loads((RPT / "year4_crosswalk_DSKP.json").read_text(encoding="utf-8"))
    assert x["source_book_file_id"] == toc["source_drive_file_id"]
    assert x["source_pdf_sha256"] == "87a388b739d8a7c7b99c4bfbfc25d3f5dd9e3d1a6016973806db806d2f4b2e11"
    assert len(x["records"]) == 30
    assert {r["lesson"] for r in x["records"]} == set(range(13,43))
    for r in x["records"]:
        n,u = r["lesson"],r["unit"]
        assert u == (n-1)//3+1
        p0,p1 = r["printed"]
        f0,f1 = r["pdf"]
        assert [f0,f1] == [p0+toc["pdf_page_offset"],p1+toc["pdf_page_offset"]]
        assert toc["units"][u-1]["printed_start_page"] <= p0 <= p1
        if u < 14:
            assert p1 < toc["units"][u]["printed_start_page"]
        source=(ROOT/f"rph_standalone/pendidikan_moral/year4/lesson_{n:03d}.md").read_text(encoding="utf-8")
        assert f"m/s {p0}–{p1}" in source and f"PDF {f0}–{f1}" in source, n
        assert "Bukti visual buku teks (audit 2026-11-05)" in source,n
        assert "halaman belum dipadankan" not in source and "halaman aktiviti khusus belum dipadankan" not in source,n
        assert "DRAF SEMAK" in source and "BELUM READY" in source, n
        for section in ("Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan/Pentaksiran PBD","Penutup"):
            assert f"**{section}" in source,(n,section)
        lines=source.splitlines()
        activities=[l for l in lines if l.startswith("**Aktiviti 1 (") or l.startswith("**Aktiviti 2 (")]
        assert len(activities)==2 and all("guru" in a.casefold() and "murid" in a.casefold() for a in activities),n
        assert all(len(a)>230 for a in activities),n
        for e in cross["units"][u-1]["sp"]:
            if e["code"] in r["sp_codes"]:
                assert e["code"] in source and e["text"] in source, (n,e["code"])
        assert len(source)>1800,n
    print("PASS Year4 textbook page-level/source-specific evidence: 30/30 RPH, Unit5–14; Year4 total 42/42 with earlier 12")
    print("REMINDER: Verifies aligned source activity and DSKP; classroom delivery, teacher judgment and A4 Word remain separate gates.")

if __name__=="__main__":
    main()
