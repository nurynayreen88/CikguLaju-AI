"""Source-anchored PI RPT2027/RPH contradiction register for human editors.

These are exact original/revised *RPH* field snapshots saved in staging
metadata; they are NOT a permission to automatically replace the RPT text.
An editor must visually compare the cited original RPT, KPM DSKP/textbook
and correct its source separately after approval. Never publish from here.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from pi_quality_audit import COUNT, ROOT
from pi_surah_pbd_alignment_audit import RPT_SOURCE_ERRORS


def audit(root=ROOT):
    root=Path(root)
    records={}
    for year, total in COUNT.items():
        payload=json.loads((root/f"year{year}.json").read_text(encoding="utf-8"))
        assert payload["year"]==year and payload["ready"] is False
        assert len(payload["records"])==total
        for row in payload["records"]:
            assert row["id"] not in records
            records[row["id"]]=row
    assert len(records)==696

    issues=[]
    for ident in sorted(RPT_SOURCE_ERRORS):
        row=records[ident]
        meta=row["staging_cross_field_source_correction"]
        assert meta["source_rpt_has_copy_error"] is True
        assert meta["publication"]=="HOLD"
        assert meta["content_expert_approved"] is False
        assert meta["jawi_orthography_approved"] is False
        assert meta["sk_sp_unchanged"] is True
        original=meta["original_fields"]
        revised=meta["revised_fields"]
        assert set(original)==set(revised)
        assert all(row["fields"][field]==new and original[field]!=new
                   for field,new in revised.items())
        issues.append({
            "id": ident, "year":row["tahun"], "lesson":row["lesson"],
            "source_issue":"SOURCE_RPT_SURAH_LABEL_OR_PBD_CONTRADICTION",
            "source_rpt_drive_id":meta["source_rpt_drive_id"],
            "review_reason":meta["change_reasons"],
            "original_rph_fields":original,
            "proposed_editor_rph_fields":revised,
            "textbook_source_page":None,
            "rpt_visual_comparison_pending":True,
            "source_rpt_modified":False,
            "teacher_or_expert_approved":False,
            "jawi_expert_approved":False,
            "can_auto_patch_rpt":False,
            "release":"NO_GO",
        })

    # Tahun 4: the original six-rukun claim contradicts textbook printed p130.
    fasting=records["T4-L107"]
    f=fasting["staging_fiqh_year4_puasa_two_pillars_source_correction"]
    assert f["rpt2027_original_objective_wrongly_claimed_six_rukun"] is True
    assert f["fiqh_expert_approved"] is False and f["publication"]=="HOLD"
    assert f["source_sp_unchanged"] is True and f["outside_source_rpt_modified"] is False
    assert f["textbook_printed_page"]==130
    assert all(fasting["fields"][k]==v and f["original_fields"][k]!=v
               for k,v in f["revised_fields"].items())
    issues.append({
        "id":"T4-L107","year":4,"lesson":107,
        "source_issue":"SOURCE_RPT_PUASA_SIX_RUKUN_CONTRADICTS_BOOK",
        "source_rpt_drive_id":f["rpt2027_drive_id"],
        "review_reason":["RPT objective states six rukun puasa; KPM textbook p130 lists two"],
        "original_rph_fields":f["original_fields"],
        "proposed_editor_rph_fields":f["revised_fields"],
        "textbook_source_page":130,"textbook_source_drive_id":f["textbook_drive_id"],
        "rpt_visual_comparison_pending":True,"source_rpt_modified":False,
        "teacher_or_expert_approved":False,"jawi_expert_approved":False,
        "can_auto_patch_rpt":False,"release":"NO_GO",
    })

    # Tahun 3: PdP051 1-6 -> PdP055 7-12 -> PdP059 13-18.
    solat=records["T3-L059"]
    m=solat["staging_t3_solat_18_case_objective_correction"]
    assert m["lesson51_range"]==[1,6] and m["lesson55_range"]==[7,12]
    assert m["lesson59_range"]==[13,18]
    assert m["rpt2027_original_objective_repeated_previous_pdp"] is True
    assert m["content_expert_approved"] is False
    assert m["jawi_orthography_approved"] is False and m["publication"]=="HOLD"
    assert solat["fields"]["objektif"]==m["revised_objective"]
    issues.append({
        "id":"T3-L059","year":3,"lesson":59,
        "source_issue":"SOURCE_RPT_SOLAT_OBJECTIVE_REPEATS_PRIOR_LESSON",
        "source_rpt_drive_id":m["rpt2027_source_drive_id"],
        "review_reason":["PdP059 repeats 7-12 in objective but 13-18 in activity; verify actual fiqh list"],
        "original_rph_fields":{"objektif":m["original_objective"]},
        "proposed_editor_rph_fields":{"objektif":m["revised_objective"]},
        "textbook_source_page":None,
        "rpt_visual_comparison_pending":True,"source_rpt_modified":False,
        "teacher_or_expert_approved":False,"jawi_expert_approved":False,
        "can_auto_patch_rpt":False,"release":"NO_GO",
    })

    issues.sort(key=lambda x:(x["year"],x["lesson"]))
    assert len(issues)==9
    assert len({x["id"] for x in issues})==9
    assert sum(len(x["proposed_editor_rph_fields"]) for x in issues)==13
    assert all(x["rpt_visual_comparison_pending"] and
               x["source_rpt_modified"] is False and
               x["teacher_or_expert_approved"] is False and
               x["jawi_expert_approved"] is False and
               x["can_auto_patch_rpt"] is False for x in issues)
    return {
        "scope":"PI RPH Years3-4 vs source RPT2027; reviewer handoff only",
        "original_catalog_total":696,
        "rpt_source_conflict_lessons":9,
        "field_level_editor_comparisons":13,
        "surah_conflict_lessons":7,
        "puasa_conflict_lessons":1,
        "solat_objective_conflict_lessons":1,
        "rpt_source_documents_modified":0,
        "approved_for_automatic_rpt_update":0,
        "teacher_ready":0,
        "academic_quality_percent":None,
        "release":"NO_GO",
        "issues":issues,
    }


def write(json_path, csv_path, root=ROOT):
    data=audit(root)
    Path(json_path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",
                               encoding="utf-8")
    columns=("id","year","lesson","source_issue","field","original_rph",
             "proposed_editor_rph","source_rpt_drive_id",
             "textbook_source_page","rpt_visual_comparison_pending",
             "teacher_or_expert_approved","source_rpt_modified","release")
    with Path(csv_path).open("w",encoding="utf-8-sig",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=columns)
        writer.writeheader()
        for issue in data["issues"]:
            for field,revised in issue["proposed_editor_rph_fields"].items():
                writer.writerow({
                    "id":issue["id"],"year":issue["year"],"lesson":issue["lesson"],
                    "source_issue":issue["source_issue"],"field":field,
                    "original_rph":issue["original_rph_fields"][field],
                    "proposed_editor_rph":revised,
                    "source_rpt_drive_id":issue["source_rpt_drive_id"],
                    "textbook_source_page":issue["textbook_source_page"],
                    "rpt_visual_comparison_pending":True,
                    "teacher_or_expert_approved":False,
                    "source_rpt_modified":False,"release":"NO_GO",
                })
    return data


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json",required=True)
    p.add_argument("--csv",required=True)
    args=p.parse_args()
    data=write(args.json,args.csv)
    print(json.dumps({k:v for k,v in data.items() if k!="issues"},
                     ensure_ascii=False,indent=2))
