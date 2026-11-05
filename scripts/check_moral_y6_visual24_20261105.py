#!/usr/bin/env python3
"""Historical-only verification of 24 Year6 old-edition scanned-book evidence records."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RPT=ROOT/"rpt_2027"/"pendidikan_moral"
LEDGER=ROOT/"audits"/"pendidikan_moral_y6_visual24_units05_13_20261105.json"

def main():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    cross=json.loads((RPT/"year6_crosswalk_DSKP.json").read_text(encoding="utf-8"))
    toc=json.loads((RPT/"year6_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
    assert len(data["records"])==24
    assert toc["source_drive_file_id"]==data["source_book_drive_id"]
    assert cross["source_dskp_id"]==data["source_dskp_drive_id"]
    assert toc["pdf_page_offset"]==data["pdf_page_offset"]==9
    expected={(u-1)*3+p for u in (5,6,8,9,10,11,12,13) for p in (1,2,3)}
    assert {r["lesson"] for r in data["records"]}==expected
    for row in data["records"]:
        y,u,n=row["year"],row["unit"],row["lesson"]
        assert y==6 and u==(n-1)//3+1
        from_p,to_p=row["printed"];from_f,to_f=row["pdf"]
        assert [from_f,to_f]==[from_p+9,to_p+9]
        book=toc["units"][u-1]
        assert book["printed_start_page"]<=from_p<=to_p<toc["units"][u]["printed_start_page"]
        file=ROOT/f"rph_standalone/pendidikan_moral/year6/lesson_{n:03d}.md"
        s=file.read_text(encoding="utf-8")
        assert f"**Rekod audit sejarah — buku edisi lama, bukan bukti Semakan 2017 (2026-11-05):** Unit {u}" in s,file
        assert "**Bukti buku teks disemak (2026-11-05):**" not in s,file
        assert "tidak boleh digunakan sebagai bukti aktiviti buku teks DBP 2021" in s,file
        assert "Padanan bab edisi Semakan 2017" in s,file
        assert f"m/s {from_p}–{to_p}" in s and f"PDF {from_f}–{to_f}" in s,file
        assert "DRAF SEMAK" in s and "BELUM READY" in s,file
        assert len(s)>=1800
        for phase in ("Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan/Pentaksiran PBD","Penutup","Kriteria kejayaan"):
            assert phase in s,(file,phase)
        activity=[line for line in s.splitlines() if line.startswith(("**Aktiviti 1 (20 minit)","**Aktiviti 2 (20 minit)"))]
        assert len(activity)==2 and all("Guru" in a and "Murid" in a for a in activity),file
        # SP text is taken from the KPM-DSKP checked source crosswalk, not the book.
        expected_sp=cross["units"][u-1]["sp"]
        phase=(n-1)%3
        needed=expected_sp[phase*2:phase*2+2] if phase<2 else expected_sp[4:]
        assert row["sp_codes"]==[e["code"] for e in needed]
        for sp in needed:
            assert sp["code"] in s and sp["text"] in s,(file,sp["code"])
    assert not any(r["unit"] in (4,7) for r in data["records"])
    print("PASS 24 Year6 old-edition source records are labelled HISTORICAL ONLY and cannot count as 2021 textbook activity verification")
    print("NOTE: individual A4 Word layout and live Telegram delivery remain separate gates.")
if __name__=="__main__":
    main()
