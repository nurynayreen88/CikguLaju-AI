#!/usr/bin/env python3
"""Read-only curricular source classification for all 480 Moral RPH sessions.

A verified source is not the same as a teacher sign-off or a verified A4 print.
Avoid relabelling Year6 units4/7 as textbook-backed: their topics differ from DSKP.
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RPT=ROOT/"rpt_2027"/"pendidikan_moral"
from audit_moral_480_individual_evidence import book_verified_pairs

def main():
    visual,_=book_verified_pairs()
    assert len(visual)==204, len(visual)
    metrics=Counter()
    for y in range(2,7):
        cross=json.loads((RPT/f"year{y}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
        toc=json.loads((RPT/f"year{y}_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
        with (RPT/f"year{y}_96h_coverage_PLANNING.csv").open(encoding="utf-8",newline="") as f:
            rows=list(csv.DictReader(f))
        assert len(rows)==96,(y,len(rows))
        assert len([r for r in rows if r["Modul"]=="TERAS"])==42,y
        assert len([r for r in rows if r["Modul"]=="PENGUKUHAN"])==54,y
        for row in rows:
            n=int(row["Sesi_1_96"]); unit=int(row["Unit"])
            rph=ROOT/row["Rujukan_RPH_Sedia_Ada"]
            source=rph.read_text(encoding="utf-8")
            assert row["SK"]==cross["units"][unit-1]["sk"],(y,n)
            sp=row["SP"].split("; ")
            assert all(code in [x["code"] for x in cross["units"][unit-1]["sp"]] for code in sp),(y,n)
            for code in sp:
                ref=next(x for x in cross["units"][unit-1]["sp"] if x["code"]==code)
                assert ref["text"] in source,(y,n,code,"SP text missing")
            assert all(label in source for label in ("Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan/Pentaksiran PBD","Penutup")),(y,n)
            assert "60 minit" in source and "PBD" in source,(y,n)
            if row["Modul"]=="PENGUKUHAN":
                metrics["DSKP_SUPPLEMENT_270"]+=1
                if y==6 and unit in (4,7):
                    assert row["Tahap_Semakan_Buku"]==f"HOLD_SOURCE_MISMATCH_UNIT{unit}_Y6"
                    assert "tidak mendakwa rujukan halaman buku teks" in source
                else:
                    assert row["Tahap_Semakan_Buku"]=="VERIFIED_TOC_START_ONLY"
                assert "DRAF" in source
            else:
                core=int(row["PdP_Teras_Asal"])
                if (y,core) in visual:
                    assert not (y==6 and unit in (4,7)),(y,core,"source conflict wrongly marked visual book activity")
                    metrics["BOOK_ACTIVITY_VISUAL_204"]+=1
                else:
                    assert (y,unit) in ((6,4),(6,7)),(y,core,"unaccounted core")
                    assert row["Tahap_Semakan_Buku"]==f"HOLD_SOURCE_MISMATCH_UNIT{unit}_Y6"
                    assert "buku teks" in source.lower() and "DSKP" in source
                    assert ("tidak sepadan" in source.lower() or "tajuk berbeza" in source.lower() or
                            "bukan padanan" in source.lower()),(y,core)
                    metrics["DSKP_ONLY_BOOK_CONFLICT_6"]+=1
                assert "DRAF SEMAK" in source and "BELUM READY" in source
        print(f"Year {y}: 42 core and 54 supplementary RPH reviewed against DSKP source")
    expected={"BOOK_ACTIVITY_VISUAL_204":204,"DSKP_ONLY_BOOK_CONFLICT_6":6,"DSKP_SUPPLEMENT_270":270}
    assert dict(metrics)==expected,(metrics,expected)
    print("PASS SOURCE CLASSIFICATION:",dict(metrics),"TOTAL",sum(metrics.values()))
    print("CAUTION: six Year6 RPH use DSKP rather than mismatched textbook activities.")
    print("CAUTION: 270 extra lessons are DSKP-verified supplements, not individual textbook activity matches.")
    print("CAUTION: live Telegram delivery, teacher pedagogical sign-off and A4 Word physical pages are separate release gates.")
if __name__=="__main__":
    main()
