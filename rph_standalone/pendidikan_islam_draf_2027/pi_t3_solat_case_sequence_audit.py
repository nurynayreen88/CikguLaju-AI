"""Year3 Year2027 three-step source sequence for solat invalidating cases.

L051 covers 1-6, L055 covers 7-12, L059 covers 13-18. The original
RPT2027 L059 objective accidentally repeats 7-12, while its activity covers
13-18. Fixing the draft objective is not a validation of exact fiqh cases or
an edit to the original RPT.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pi_quality_audit import ROOT

SEQUENCE={51:(1,6),55:(7,12),59:(13,18)}
SOURCE_RPT="1ceqdKRKYP2MHpkPe4KbIOVpCooq37NVE"


def audit(root=ROOT):
    data=json.loads((Path(root)/"year3.json").read_text(encoding="utf-8"))
    assert data["year"]==3 and data["ready"] is False and len(data["records"])==147
    rows=[]
    for n,(a,b) in SEQUENCE.items():
        r=data["records"][n-1]
        assert r["id"]==f"T3-L{n:03d}" and r["verified_ready"] is False
        target=f"سناراي {a}-{b} درڤد يڠ ممبطلكن صلاة"
        assert target in r["fields"]["objektif"],r["id"]
        assert target in r["fields"]["aktiviti_utama"],r["id"]
        assert "4.2.1" in r["fields"]["sp"]
        rows.append({"id":r["id"],"range_start":a,"range_end":b,
                     "objective_activities_consistent":True,
                     "teacher_fiqh_verified":False,"can_publish":False})
    assert [x for item in rows for x in range(item["range_start"],item["range_end"]+1)]==list(range(1,19))
    r=data["records"][58]
    m=r["staging_t3_solat_18_case_objective_correction"]
    assert m["revision"]=="pi-t3-l059-case-sequence-source-20261108"
    assert "سناراي 7-12" in m["original_objective"]
    assert "سناراي 13-18" in m["revised_objective"]
    assert r["fields"]["objektif"]==m["revised_objective"]
    assert m["rpt2027_source_drive_id"]==SOURCE_RPT
    assert m["dskp_sp_codes_unchanged"] is True
    assert m["content_expert_approved"] is False
    assert m["actual_fiqh_case_list_from_book_visually_approved"] is False
    assert m["publication"]=="HOLD"
    return {
        "subject":"Pendidikan Islam","year":3,
        "original_rpt2027_drive_id":SOURCE_RPT,
        "t3_pdp_051_055_059_ranges_sequential":True,
        "reviewed_range_count":3,"listed_case_numbers_covered_once":18,
        "rpt_2027_l059_original_objective_incorrect":True,
        "rpt_2027_source_modified":False,
        "catalog_year3_l059_objective_repaired":True,
        "source_sp_unchanged":True,
        "expert_fiqh_approved":False,
        "teacher_ready":0,
        "release":"NO_GO","rows":rows
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    r=audit()
    Path(args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},ensure_ascii=False,indent=2))
