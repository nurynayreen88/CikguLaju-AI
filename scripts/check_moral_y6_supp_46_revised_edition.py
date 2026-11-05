#!/usr/bin/env python3
"""Year6 supplementary RPH: block old 2015 scanned book metadata in revised 2017 worksheets.
Only validates the revised edition chapter/page provenance, never activity-page accuracy.
"""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"rpt_2027/pendidikan_moral"

def main():
    revised=json.loads((ROOT/"audits/pendidikan_moral_y6_kssr2017_edition_migration_20261105.json").read_text(encoding="utf-8"))["revised_edition"]["units"]
    with (BASE/"year6_96h_coverage_SEMAKAN2017_REVIEW.csv").open(encoding="utf-8",newline="") as fp:
        rows=list(csv.DictReader(fp))
    checked=set()
    textual=set([24,25,26,27,45,46,47,48])
    for row in rows:
        if row["Modul"]!="PENGUKUHAN":continue
        sess=int(row["Sesi_1_96"])
        unit=revised[int(row["Unit"])-1]
        path=ROOT/row["Rujukan_RPH_Sedia_Ada"]
        txt=path.read_text(encoding="utf-8")
        assert path.is_file()
        assert row["Tajuk_Unit"]==unit["title"]
        assert "STATUS DALAMAN" in txt and "BELUM_VERIFIED" in txt
        assert "**Aktiviti 1" in txt and "**Aktiviti 2" in txt and "**Penutup" in txt
        assert "Pengukuhan/Pentaksiran PBD" in txt and "60 minit" in txt
        if sess in textual:
            assert "Bukti aktiviti Semakan 2017" in txt, (sess,path)
        else:
            assert "**Padanan edisi Semakan 2017 (2021):**" in txt, (sess,path)
            bbm=next(x for x in txt.splitlines() if x.startswith("**BBM:**"))
            assert unit["title"] in bbm, (sess,"wrong edition title")
            assert f"mula m/s {unit['printed_start']}" in bbm
            assert f"flipbook halaman {unit['printed_start']+10}" in bbm
            assert "PDF " not in bbm, (sess,"obsolete scanned source page")
            assert "halaman aktiviti terperinci" in txt.casefold()
        checked.add(sess)
    assert len(checked)==54 and len(checked-textual)==46 and len(checked & textual)==8
    print("PASS 54 Year6 supplementary RPH: 46 revised-2021 chapter/page references + 8 previously text-audited RPH")
    print("NOT FINAL READY: 46 new chapter matches are not individual activity-page verifications; actual teacher delivery pending")

if __name__=="__main__":
    main()
