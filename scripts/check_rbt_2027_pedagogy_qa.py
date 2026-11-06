#!/usr/bin/env python3
"""RBT Year 4–6 per-PdP editorial and curriculum source QA.

Staging only. These are automated guards, NOT textbook-image verification,
teacher individual pedagogical approval, or production-user QA.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_SP={4:57,5:34,6:23}
EXPECTED_REPEATS={
  4:{},
  5:{"6.4.6":2,"7.1.6":3},
  6:{"5.2.3":2,"5.2.4":2,"5.2.5":3,"8.1.3":2,
     "8.1.6":4,"8.1.7":2},
}
KEYS=("set_induksi","aktiviti_1","aktiviti_2","pengukuhan_penilaian","penutup")
DRAFT="DRAF_STAGING"


def read_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))


def review_year(year,dskp):
    doc=read_json(f"rph_standalone/rbt/tahun_{year}/RPH_RBT_T{year}_2027_DRAF.json")
    lessons=doc["pelajaran"]
    assert doc["status"]==DRAFT and doc["bukan_modul_pengguna"] is True
    assert len(lessons)==32
    assert sum(m["pdp_cadangan"] for m in doc["modul"])==32
    assert len({m["unit"] for m in doc["modul"]})==len(doc["modul"])
    with (ROOT/f"rpt_2027/rbt/RPT_RBT_T{year}_2027_DRAF.csv").open(
         encoding="utf-8-sig",newline="") as f:
        rpt=list(csv.DictReader(f))
    assert len(rpt)==32
    source_verified={
      x["sp"] for x in dskp["per_year"][str(year)]["sp_evidence"]
      if x["focus_exact_text_in_dskp"] is True
    }
    assert len(source_verified)==EXPECTED_SP[year]
    all_sp=set()
    seen=defaultdict(list)
    unit_numbers=[]
    for n,(l,r) in enumerate(zip(lessons,rpt),1):
        code=f"RBT-T{year}-PDP-{n:03d}"
        assert l["id"]==r["ID"]==code
        assert l["pdp"]==n==int(r["PdP"])
        assert l["tajuk"].startswith(f"PdP {n:03d}: ")
        assert r["Tajuk PdP"]==l["tajuk"], code
        assert r["Unit"]==l["unit_label"]==(
            f"Unit {l['unit']}: "+doc["modul"][l["unit"]-1]["tajuk"]),code
        assert r["SK"]==" / ".join(l["sk"])
        assert r["SP"]==" / ".join(l["sp_codes"])
        assert r["Status"]=="DRAF"
        assert l["review"]["release_ready"] is False
        assert l["review"]["pedagogi_disahkan_individu"] is False
        assert l["review"]["halaman_buku_disahkan"] is False
        assert l["rujukan_buku_teks"]["muka_surat"] is None
        assert l["status_cadangan_projek"]=="CADANGAN_PDP_CIKGULAJU_BUKAN_AKTIVITI_BUKU_DISAHKAN"
        assert l["objektif"] and l["kriteria_kejayaan"] and l["artefak_khusus"]
        assert l["rubrik_pbd_khusus"] and l["pbd_evidens"]
        assert list(l["langkah"])==list(KEYS)
        assert sum(l["langkah"][x]["minit"] for x in KEYS)==60
        assert l["langkah"]["aktiviti_1"]["minit"]==15
        assert l["langkah"]["aktiviti_2"]["minit"]==25
        assert l["langkah"]["pengukuhan_penilaian"]["minit"]==10
        assert l["langkah"]["set_induksi"]["minit"]==5
        assert l["langkah"]["penutup"]["minit"]==5
        assert l["langkah"]["aktiviti_1"]["aktiviti"]!=l["langkah"]["aktiviti_2"]["aktiviti"]
        assert len(l["langkah"]["penutup"]["aktiviti"])>=85
        assert "bukan keputusan akhir projek yang belum dilaksanakan" not in l["langkah"]["penutup"]["aktiviti"]
        assert len(l["langkah"]["aktiviti_1"]["aktiviti"])>=85
        assert len(l["langkah"]["aktiviti_2"]["aktiviti"])>=85
        assert l["keselamatan"] in l["langkah"]["aktiviti_2"]["aktiviti"]
        assert l["pbd_evidens"]==l["langkah"]["pengukuhan_penilaian"]["aktiviti"]
        assert [x["kod"] for x in l["sp_fokus_ringkas"]]==l["sp_codes"]
        assert set(l["sp_codes"])<=source_verified
        unit_numbers.append(l["unit"])
        for sp in l["sp_codes"]:
            all_sp.add(sp)
            assert sp in (l["langkah"]["aktiviti_1"]["aktiviti"]+
                          l["langkah"]["aktiviti_2"]["aktiviti"])
        seen["+".join(l["sp_codes"])].append(l)
    assert len(all_sp)==EXPECTED_SP[year]
    assert unit_numbers==sorted(unit_numbers)
    assert Counter(unit_numbers)==Counter({
        m["unit"]:m["pdp_cadangan"] for m in doc["modul"]
    })
    repeated={sp:rows for sp,rows in seen.items() if len(rows)>1}
    assert {code:len(rows) for code,rows in repeated.items()}==EXPECTED_REPEATS[year]
    for sp,rows in repeated.items():
        for field in ("tajuk","objektif","kriteria_kejayaan","artefak_khusus","pbd_evidens"):
            assert len({r[field] for r in rows})==len(rows),(year,sp,field)
        for phase in ("aktiviti_1","aktiviti_2","penutup"):
            assert len({r["langkah"][phase]["aktiviti"] for r in rows})==len(rows),(year,sp,phase)
        for n,r in enumerate(rows,1):
            assert r["audit_pemurnian_pdp"]["tahap"]==f"{n}/{len(rows)}",(year,sp)
            assert r["audit_pemurnian_pdp"]["aktiviti_visual_buku_disahkan"] is False
    print(f"PASS RBT T{year}: 32/32 lesson audit, {len(all_sp)} exact DSKP codes, "
          f"{sum(len(rows) for rows in repeated.values())} distinct repeated-SP stages.")
    return len(lessons),len(all_sp)


def main():
    dskp=read_json("audits/rbt_2027_114_dskp_exact_text_evidence_20261106.json")
    assert dskp["total_pdp"]==96 and dskp["total_unique_sp"]==114
    assert dskp["visual_book_approvals"]==dskp["teacher_individual_approvals"]==0
    lesson_count=sp_count=0
    for year in (4,5,6):
        a,b=review_year(year,dskp)
        lesson_count+=a;sp_count+=b
    assert lesson_count==96 and sp_count==114
    approval=read_json("audits/rbt_t4_t6_manual_release_approval_manifest_20261106.json")
    assert len(approval["individual_review"])==96
    assert approval["approvals_granted"]==approval["release_ready_count"]==0
    assert all(not x["release_ready"] for x in approval["individual_review"])
    assert all(x["automated_dskp_sp_focus_exact_match"] is True
               and x["automated_rpt_rph_title_unit_code_parity"] is True
               and x["automated_rph_conclusion_not_generic"] is True
               and x["automated_progression_distinct_check"] is True
               and x["semakan_individu_guru"] is False
               and x["aktiviti_dalam_buku_diluluskan"] is False
               for x in approval["individual_review"])
    assert approval["automated_content_audit"]["rph_individually_structurally_tested"]==96
    assert approval["automated_content_audit"]["unique_dskp_sp_exact_match"]==114
    print("PASS: 96/96 source-linked editorial checks; 114/114 DSKP SP text-match evidence.")
    print("RELEASE REMAINS BLOCKED: textbook activity visuals/teacher approval = 0/96.")


if __name__=="__main__":
    main()
