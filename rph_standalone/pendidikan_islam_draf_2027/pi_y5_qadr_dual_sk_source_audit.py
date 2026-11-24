"""Source-grounded Year5 Surah al-Qadr combined tilawah/hafazan SP audit.

Official mainstream KSSR Year5 PI DSKP printed p19: SP1.1.2 is continuous
Quran reading, not al-Qadr memorization. Printed p21: SP1.3.1 is al-Qadr
memorization. L069 and L073 combine SK1.1 tilawah and SK1.3 hafazan.
Keep original metadata + source files, no approval/teacher publication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pi_quality_audit import ROOT, COUNT

DRIVE="1P6ClIlwU1OFd3tEUdoKt3VnAAGGbpja6"
LESSONS={"T5-L069","T5-L073"}
WRONG="1.1.2 مڠحفظ  سورة القدر دڠن بتول دان برتجويد."
RIGHT="1.3.1 مڠحفظ  سورة القدر دڠن بتول دان برتجويد."

def audit(root=ROOT):
    root=Path(root)
    data=json.loads((root/"year5.json").read_text(encoding="utf-8"))
    assert data["year"]==5 and data["ready"] is False
    assert len(data["records"])==COUNT[5]
    idx={x["id"]:x for x in data["records"]}
    assert len(idx)==143
    reports=[]
    for ident in sorted(LESSONS):
        r=idx[ident]
        assert r["verified_ready"] is False and not r["withheld"]
        meta=r["staging_y5_surah_qadr_11_13_source_correction"]
        assert meta["revision"]=="pi-y5-l069-l073-hafazan-sp-131-20261108"
        assert meta["source_dskp_drive_id"]==DRIVE
        assert meta["source_dskp_printed_pages"]==[19,21]
        assert meta["original_sk_unchanged"] is True
        assert meta["original_objective_unchanged"] is True
        assert meta["original_source_sha256_preserved"] is True
        assert meta["rpt_source_modified"] is False
        assert meta["academic_expert_approved"] is False
        assert meta["jawi_orthography_approved"] is False
        assert meta["teacher_ready"] is False
        assert meta["publication"]=="HOLD"
        old=meta["original_fields"]
        revised=meta["revised_fields"]
        assert WRONG in old["sp"] and RIGHT in revised["sp"]
        assert r["fields"]["sp"]==revised["sp"]
        assert WRONG not in r["fields"]["sp"]
        assert "1.1.1 ممباچ" in r["fields"]["sp"]
        assert "1.1" in r["fields"]["sk"] and "1.3" in r["fields"]["sk"]
        assert "مڠحفظ" in r["fields"]["objektif"]
        assert meta["source_1_1_2"].startswith("Membaca al-Quran")
        assert meta["source_1_3_1"].startswith("Menghafaz Surah al-Qadr")
        assert set(old)==set(revised)
        assert all(r["fields"][k]==revised[k] and old[k]!=revised[k] for k in revised)
        if ident=="T5-L073":
            assert "set_induksi" in revised
            assert "سورة ا القدر" in old["set_induksi"]
            assert "سورة ا القدر" not in revised["set_induksi"]
        else:
            assert set(revised)=={"sp"}
        reports.append({"id":ident,"correction_fields":sorted(revised),
                        "combined_sk_preserved":True,"sp_131_matches_memorization":True,
                        "expert_approved":False,"ready":False})
    for r in data["records"]:
        if r["withheld"]:continue
        assert WRONG not in r["fields"]["sp"],r["id"]
    assert len(reports)==2
    return {
        "scope":"KSSR mainstream PI Y5 Surah al-Qadr dual SK source correction",
        "original_year5_catalog_size":143,
        "fixed_combined_sk_lessons":len(reports),
        "source_field_replacements":sum(len(x["correction_fields"]) for x in reports),
        "original_sk_and_objectives_unchanged":True,
        "source_dskp_drive_id":DRIVE,"source_dskp_printed_pages":[19,21],
        "source_rpt_modified":False,
        "academic_expert_approved":0,"ready_for_teacher":0,
        "release":"NO_GO",
        "rows":reports,
    }

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--output",required=True)
    args=a.parse_args()
    data=audit()
    Path(args.output).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k!="rows"},ensure_ascii=False,indent=2))
