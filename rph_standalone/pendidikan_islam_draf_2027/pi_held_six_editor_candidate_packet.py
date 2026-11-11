"""Unify all six fully withheld Pendidikan Islam editor-only draft candidates.

This is a *reviewer packet*, not a teacher release. Source RPH held entries stay
empty, so the production catalog cannot accidentally publish unresolved texts.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json

from pi_quality_audit import ROOT, COUNT, HELD
from pi_editor_material_projection import preview_catalog

REQUIRED_KEYS=("set_induksi","aktiviti_utama","pengukuhan","pentaksiran","penutup","bahan")
EXPECTED_HELD=("T2-L035","T6-L006","T6-L014","T6-L018","T6-L060","T6-L117")


def audit(root=ROOT):
    root=Path(root)
    t2=json.loads((root/"pi_t2_l035_held_quran_editor_candidate.json").read_text(encoding="utf-8"))
    y6=json.loads((root/"pi_t6_held_quran_editor_candidates.json").read_text(encoding="utf-8"))
    l60=json.loads((root/"pi_t6_l060_amali_editor_candidate.json").read_text(encoding="utf-8"))
    assert t2["lesson_id"]=="T2-L035" and t2["publication"]=="HOLD"
    assert t2["verified_ready"] is False and t2["allowed_in_teacher_web_or_telegram"] is False
    assert t2["review_checks"]["original_catalog_year2_l035_still_wholly_withheld"] is True
    assert t2["source_provenance"]["source_exact_overlap_ayah"]==[224]
    assert t2["options_for_teacher"]["selected_option"] is None
    assert t2["options_for_teacher"]["teacher_approved"] is False

    proposals=[("T2-L035","source_overlap_ayah224",t2["editorial_draft"])]
    for row in y6["candidates"]:
        assert row["original_withheld_unmodified"] is True
        assert row["editor_preview_only"] is True and row["publication"]=="HOLD"
        assert row["reviewer_checks"]["can_publish"] is False
        proposals.append((row["lesson_id"],"quran_rpt_held",row["rph_editor_draft"]))
    assert y6["publish_to_web_or_telegram"] is False
    assert l60["lesson_id"]=="T6-L060" and l60["publication"]=="HOLD"
    assert l60["allowed_in_teacher_web_or_telegram"] is False
    assert l60["catalog_original_record_remains_withheld"] is True
    assert l60["release_checks"]["eligible_for_teacher_use"] is False
    proposals.append(("T6-L060","additional_amali_not_official_separate_pdp",l60["editorial_draft"]))
    found={name for name,_,_ in proposals}
    assert len(proposals)==len(found)==len(HELD)==6 and found==set(EXPECTED_HELD)

    rows=[]
    for year,total in COUNT.items():
        records=json.loads((root/f"year{year}.json").read_text(encoding="utf-8"))["records"]
        assert len(records)==total
        for record in records:
            if (year,record["lesson"]) in HELD:
                assert record["id"] in found
                assert record["withheld"] and "fields" not in record and "intro" not in record
                continue
            assert record["verified_ready"] is False
    for lesson_id,kind,draft in proposals:
        assert all(k in draft and draft[k] for k in REQUIRED_KEYS),lesson_id
        steps=draft["aktiviti_utama"]
        assert len(steps)==4 and all(step.startswith(f"{n}. ") for n,step in enumerate(steps,1)),lesson_id
        assert isinstance(draft["set_induksi"],str)
        assert isinstance(draft["pentaksiran"],str)
        assert isinstance(draft["penutup"],str)
        rows.append({
            "id":lesson_id,"editorial_kind":kind,"candidate":draft,
            "original_catalog_withheld":True,
            "expert_verified":False,"jawi_verified":False,
            "official_dskp_sp_assigned":False,
            "runtime_generation_tested":False,"teacher_publish":False,
            "release":"NO_GO"
        })
    rows.sort(key=lambda r:(int(r["id"].split("-")[0][1:]),
                            int(r["id"].split("-")[1][1:])))
    old=preview_catalog(root)
    assert old["all_records"]==696 and old["active_drafts"]==690
    assert len(old["rows"])==690
    assert not ({r["id"] for r in old["rows"]}&found)
    assert len({r["id"] for r in old["rows"]}|found)==696
    assert old["release"]=="NO_GO"
    return {
        "subject":"Pendidikan Islam",
        "scope":"YEAR2-6 EDITOR ONLY; not runtime/Telegram/Web",
        "total_catalog":696,
        "nonheld_existing_editor_drafts":690,
        "fully_held_editor_candidates":6,
        "proposed_editor_content_total":696,
        "teacher_ready":0,"content_expert_approved":0,
        "jawi_orthography_approved":0,"approved_word_pdf_runtime_generations":0,
        "actual_catalog_entries_released":0,"original_held_catalog_modified":False,
        "t2_l035_ayah224_source_overlap_expert_resolved":False,
        "year6_juz25_67_ayah_mapped_in_source_rpt":False,
        "publication":"HOLD","release":"NO_GO","rows":rows,
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    x=audit()
    Path(args.output).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in x.items() if k!="rows"},ensure_ascii=False,indent=2))
