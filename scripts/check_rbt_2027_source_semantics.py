#!/usr/bin/env python3
"""RBT 2027: SP-to-activity semantic drift guards (not human approval).

Protects all 96 PdP against specific previously found defects:
- non-programming subjects referencing algorithms/flowcharts incorrectly,
- truncated menu labels,
- presentation SP with unrelated classification activities,
- hardware/planting steps replaced by generic cost/algorithm templates.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROGRAM_UNITS={4:6,5:3,6:2}
EXPECTED_EDITORIAL={4:32,5:16,6:12}
BAD_TITLE_SUFFIXES={
    " per"," dan a"," dihasilka"," bahar"," ses"," menggun"," kaedah p",
    " dibuat men"," yang "
}


def run():
    total=0
    revised=0
    for year in (4,5,6):
        path=ROOT/f"rph_standalone/rbt/tahun_{year}/RPH_RBT_T{year}_2027_DRAF.json"
        d=json.loads(path.read_text(encoding="utf-8"))
        assert d["status"]=="DRAF_STAGING"
        lessons=d["pelajaran"]
        assert len(lessons)==32
        with (ROOT/f"rpt_2027/rbt/RPT_RBT_T{year}_2027_DRAF.csv").open(
                encoding="utf-8-sig",newline="") as handle:
            rpt=list(csv.DictReader(handle))
        assert len(rpt)==32
        changed=0
        for n,(l,row) in enumerate(zip(lessons,rpt),1):
            assert l["pdp"]==n and l["id"]==row["ID"]
            assert l["tajuk"].startswith(f"PdP {n:03d}: ")
            assert l["tajuk"]==row["Tajuk PdP"] and l["unit_label"]==row["Unit"]
            assert not any(l["tajuk"].endswith(s) for s in BAD_TITLE_SUFFIXES)
            assert l["review"]["release_ready"] is False
            assert l["review"]["halaman_buku_disahkan"] is False
            assert l["rujukan_buku_teks"]["muka_surat"] is None
            actions=" ".join(l["langkah"][k]["aktiviti"] for k in
                             ("aktiviti_1","aktiviti_2"))
            curriculum=" ".join((l["objektif"],l["kriteria_kejayaan"],l["artefak_khusus"],actions))
            if (year==4 and l["unit"]!=6 or
                year==5 and l["unit"]!=3 or
                year==6 and l["unit"]==1):
                assert not any(t in curriculum.lower() for t in
                               ("pseudokod","carta alir","algoritma","atur cara")),(
                    year,n,l["unit"])
            assert "Guru memberikan model kerja SP " not in actions if year==4 else True
            assert len(l["langkah"]["aktiviti_1"]["aktiviti"])>100
            assert len(l["langkah"]["aktiviti_2"]["aktiviti"])>100
            assert l["pbd_evidens"]==l["langkah"]["pengukuhan_penilaian"]["aktiviti"]
            assert l["langkah"]["aktiviti_1"]["aktiviti"]!=l["langkah"]["aktiviti_2"]["aktiviti"]
            if l.get("audit_pemurnian_20261106",{}).get("editorial_specific_activities") or (
                    year==4 and l.get("audit_pemurnian_20261106",{}).get("jenis")):
                changed+=1
            total+=1
        assert changed==EXPECTED_EDITORIAL[year],(year,changed)
        revised+=changed
        print(f"PASS RBT Tahun {year}: 32/32 activities, {changed} newly rewritten lessons.")
        # Reproduce known high-impact corrections as positive expectations.
        def text(n):
            l=lessons[n-1]
            return " ".join(x["aktiviti"] for x in l["langkah"].values()).lower()
        if year==4:
            assert all(l.get("audit_pemurnian_20261106",{}).get(
                "objective_success_criteria_induction_aligned_to_activity") is True
                for l in lessons)
            assert "pembentang" in lessons[9]["objektif"].lower()
            assert "membuat penerangan" in lessons[9]["kriteria_kejayaan"].lower()
            assert "pengelasan" not in lessons[9]["objektif"].lower()
            assert "senario bergambar" in text(2)
            assert "sesi galeri" in text(10)
            assert "jenis garisan" in text(6)
            assert "carta alir" in text(27) and "scratch" in text(30)
            assert "pseudokod" not in text(17)
        if year==5:
            assert "papan uji" in text(21)
            assert "medium" in text(29) and "alatan" in lessons[28]["tajuk"].lower()
            assert "struktur kawalan" in text(14) or "algoritma" in text(14)
        if year==6:
            assert "carta alir" in text(16)
            assert "atur cara" in text(17)
            assert "memasang" in text(18)
            assert "memuat naik" in text(19)
            assert "sensor" in text(21)
    assert total==96 and revised==60
    print("PASS 96 RBT semantic checks; 60 newly rewritten; 0 public approvals granted.")


if __name__=="__main__":
    run()
