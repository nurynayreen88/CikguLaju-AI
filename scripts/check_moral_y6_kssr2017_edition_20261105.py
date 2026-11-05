#!/usr/bin/env python3
"""Guard against treating a KSSR 2015 Year6 textbook as KSSR Semakan 2017.

Verifies reviewed textual activity links + existing official DSKP SP wording.
The 14 source conversions do not certify full current-edition Year6 coverage,
teacher-specific 2027 dates, Word layout or live Telegram delivery.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"audits/pendidikan_moral_y6_kssr2017_edition_migration_20261105.json"
RPT=ROOT/"rpt_2027/pendidikan_moral"

def main():
    source=json.loads(AUDIT.read_text(encoding="utf-8"))
    revised=source["revised_edition"]
    legacy=source["legacy_edition"]
    cross=json.loads((RPT/"year6_crosswalk_DSKP.json").read_text(encoding="utf-8"))
    toc=json.loads((RPT/"year6_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
    assert revised["curriculum"]=="KSSR Semakan 2017"
    assert revised["publication_year"]==2021
    assert revised["source_url"]=="https://fliphtml5.com/sbinx/haph/"
    assert len(revised["units"])==14
    starts=[x["printed_start"] for x in revised["units"]]
    assert starts==list(range(2,133,10)),starts
    assert [u["title"] for u in revised["units"]]==["Kepercayaan kepada Tuhan Menjamin Kesejahteraan Negara","Bantuan dan Sokongan Moral kepada Negara","Tanggungjawab sebagai Warganegara","Hargai Keunikan Negara","Amalan Hemah Tinggi Meningkatkan Imej Negara","Hormati Identiti Negara","Cinta akan Negara","Amalan Adil Demi Kesejahteraan Negara","Berani Mempertahankan Maruah Negara","Kejujuran Demi Kesejahteraan Negara","Rajin Demi Kemajuan Negara","Kerjasama Demi Keharmonian Negara","Amalan Kesederhanaan Demi Kesejahteraan Negara","Amalan Toleransi Menjamin Perpaduan Negara"]
    assert toc["source_drive_file_id"]==legacy["source_drive_file_id"]
    assert toc["pdf_page_offset"]==legacy["pdf_printed_offset"]==9
    assert toc["units"][3]["printed_heading_original"]=="Jasa Tokoh Negara Dikenang"
    assert toc["units"][6]["printed_heading_original"]=="Sayangilah Alam, Hargai Kehidupan"
    assert cross["source_dskp_id"]=="1lE4-LxIbHQu1-oe-CgI_6sHBU54FYKUA"
    assert len(legacy["historical_y6_core_source_ledger_lessons"])==36
    assert len(set(legacy["historical_y6_core_source_ledger_lessons"]))==36
    assert len(source["reviewed_revised"])==14
    assert sum(x["module"]=="TERAS" for x in source["reviewed_revised"])==6
    assert sum(x["module"]=="PENGUKUHAN" for x in source["reviewed_revised"])==8
    expected_core={10,11,12,19,20,21}
    expected_extra={24,25,26,27,45,46,47,48}
    assert {r["lesson_or_session"] for r in source["reviewed_revised"] if r["module"]=="TERAS"}==expected_core
    assert {r["lesson_or_session"] for r in source["reviewed_revised"] if r["module"]=="PENGUKUHAN"}==expected_extra
    assert not (set(legacy["historical_y6_core_source_ledger_lessons"]) & expected_core)
    for row in source["reviewed_revised"]:
        mod,n,unit=row["module"],row["lesson_or_session"],row["unit"]
        assert unit in (4,7)
        start,end=row["printed_pages"]
        assert start>=revised["units"][unit-1]["printed_start"]
        assert end<revised["units"][unit]["printed_start"]
        assert row["flipbook_pages"]==[start+10,end+10]
        if mod=="TERAS":
            p=ROOT/f"rph_standalone/pendidikan_moral/year6/lesson_{n:03d}.md"
            marker=f"**Pengesahan sumber Semakan 2017 (2026-11-05):** Unit {unit}, m/s {start}–{end} (halaman flipbook {start+10}–{end+10})"
            old_edition_marker="**Catatan perbezaan edisi:**"
        else:
            p=ROOT/f"rph_standalone/pendidikan_moral/pengukuhan/year6/sesi_{n:03d}.md"
            marker=f"**Bukti aktiviti Semakan 2017 (2026-11-05):** Unit {unit}, m/s {start}–{end} (halaman flipbook {start+10}–{end+10})"
            old_edition_marker="**Batasan sumber:**"
        s=p.read_text(encoding="utf-8")
        assert marker in s,p
        assert old_edition_marker in s,p
        assert revised["source_url"] in s,p
        if mod=="TERAS":
            assert "DRAF SEMAK" in s and "BELUM READY" in s,p
        else:
            assert "STATUS DALAMAN" in s and "BELUM_FINAL_READY" in s,p
        assert "Objektif dan kriteria kejayaan" in s and "PBD" in s
        assert "Set induksi" in s and "Penutup" in s
        activities=[x for x in s.splitlines() if x.startswith(("**Aktiviti 1 (20 minit)","**Aktiviti 2 (20 minit)"))]
        assert len(activities)==2 and all("Guru" in x and "Murid" in x for x in activities),p
        if mod=="TERAS":
            expected=cross["units"][unit-1]["sp"]
            phase=(n-1)%3
            target=expected[:2] if phase==0 else expected[2:4] if phase==1 else expected[4:]
        else:
            target=[x for x in cross["units"][unit-1]["sp"] if x["code"] in row["sp_codes"]]
        assert row["sp_codes"]==[x["code"] for x in target],p
        assert all(x["code"] in s and x["text"] in s for x in target),p
    assert source["remaining"]=={
      "y6_core_old_edition_historical_review":36,
      "y6_core_not_in_prior_visual_ledger":[],
      "y6_supplement_not_individually_revised":46,
      "years2_to5_core_correct_edition_visual_ledger":168,
    }
    print("PASS Year6: 14 KSSR Semakan 2017 source-text/DSKP-aligned RPH (6 core, 8 supplementary)")
    print("REQUIRED REMAINING: 36 other Year6 core current-book checks; 46 other Year6 supplementary source checks.")
    print("Historical 33 old-edition Year6 'verified' entries are NOT approved for revised-edition teaching.")
    print("NOT FINAL READY: 2027 class dates, real Telegram delivery and source-wide pedagogy still require checks.")

if __name__=="__main__":
    main()
