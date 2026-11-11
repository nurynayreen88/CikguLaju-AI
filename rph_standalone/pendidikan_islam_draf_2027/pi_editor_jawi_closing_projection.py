"""Stage 690 Jawi penutup candidate texts inside isolated editor RPH previews.

This is a reversible VIEW transformation, not an edit to the 690 original RPH,
not a linguist approval, and never a teacher-facing runtime switch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pi_quality_audit import ROOT
from pi_editor_material_projection import preview_catalog
from pi_closing_jawi_candidates_complete import generate


def preview(root=ROOT):
    original=preview_catalog(root)
    candidates=generate(root)
    assert original["active_drafts"]==690
    assert candidates["candidate_groups"]==78
    assert candidates["candidate_covered_lesson_occurrences"]==690
    mappings={}
    for group in candidates["records"]:
        assert group["approved"] is False and group["can_publish"] is False
        assert group["jawi_spelling_verified"] is False
        ids=group["lesson_ids"].split("|")
        assert len(ids)==group["lesson_count"]
        assert group["candidate_jawi_text"].strip()
        for ident in ids:
            assert ident not in mappings,ident
            mappings[ident]=group
    assert len(mappings)==690
    rows=[]
    for item in original["rows"]:
        ident=item["id"]
        group=mappings[ident]
        before=item["display_fields"]["penutup"]
        assert before==group["original_closing_rumi"],ident
        assert hashlib.sha256(before.encode("utf-8")).hexdigest()==group["original_text_sha256"],ident
        displayed=dict(item["display_fields"])
        displayed["penutup"]=group["candidate_jawi_text"]
        assert displayed["penutup"]!=before
        rows.append({
            "id":ident,"year":item["year"],
            "source_status":item["source_state"],
            "display_fields":displayed,
            "original_penutup_rumi":before,
            "penutup_original_sha256":group["original_text_sha256"],
            "jawi_candidate_group_id":group["group_id"],
            "source_material_sha256":item["source_material_sha256"],
            "editor_only_material_notes":item["editor_only_material_notes"],
            "jawi_spelling_approved":False,
            "sp_content_expert_approved":False,
            "word_pdf_visual_approved":False,
            "can_publish":False,"preview_only":True,
            "release":"NO_GO"
        })
    assert len(rows)==690 and len({r["id"] for r in rows})==690
    assert all(not x["can_publish"] for x in rows)
    return {
        "subject":"Pendidikan Islam","scope":"690 NONHELD EDITOR DRAFTS ONLY",
        "jawi_closing_candidates_injected_in_reversible_preview":690,
        "original_rph_fields_modified":0,
        "unique_reviewable_jawi_closing_groups":78,
        "all_original_rumi_closings_preserved":True,
        "academic_and_jawi_approved":0,
        "ready_for_teacher":0,"source_year1_included":False,
        "academic_quality_percent":None,
        "publication":"HOLD","release":"NO_GO",
        "rows":rows
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    result=preview()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
