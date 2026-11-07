"""Fail-closed review of four Year6 Quran RPH proposals, isolated from runtime.

The teaching materials are RUMI reviewer drafts only. CikguLaju's actual
Jawi RPH must not adopt these drafts without source-specific checks,
the teacher's verse-allocation signoff and a native Word/PDF test.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pi_quality_audit import ROOT
from pi_t6_juz25_sequence_gap_audit import audit as juz25_audit,ASSIGNED
from pi_t6_juz29_l117_continuity_review import audit as juz29_audit,LESSONS

FILE="pi_t6_held_quran_editor_candidates.json"
EXPECTED={
    "T6-L006":[[42,33,51]],
    "T6-L014":[[43,34,73]],
    "T6-L018":[[44,40,59]],
    "T6-L117":[[70,40,44],[71,1,28],[72,1,13]],
}


def audit(root=ROOT):
    root=Path(root)
    source=json.loads((root/"year6.json").read_text(encoding="utf-8"))
    data=json.loads((root/FILE).read_text(encoding="utf-8"))
    assert len(source["records"])==143 and source["ready"] is False
    assert data["schema"]=="pi_editor_only_quran_rph_proposals_v1"
    assert data["status"]=="HOLD" and data["publish_to_web_or_telegram"] is False
    assert data["native_dskp_three_level_sp_assigned"] is False
    assert data["teacher_use_approved"] is False
    assert data["reference_rpt"]["drive_id"]=="1T380Ot_gG58JhxanELMM0z-gr6wmSJcL"
    juz25=juz25_audit(root)
    juz29=juz29_audit(root)
    summary=data["verified_sequence"]
    assert summary["juz25_rpt_ayah_mapped"]==juz25["juz25_ayah_assigned_in_rpt"]==179
    assert summary["juz25_rpt_ayah_expected"]==juz25["juz25_expected_ayah_count"]==246
    assert summary["juz25_rpt_ayah_missing"]==juz25["juz25_ayah_missing_in_rpt"]==67
    assert summary["juz29_70_71_72_neighboring_pdp_ayah_mapped"]==juz29["three_surahs_mapped_ayat"]==100
    assert summary["juz29_70_71_72_missing"]==0
    blocks=data["missing_juz25_not_assigned_to_any_existing_pdp"]
    assert [(x["surah"],x["ayah"],x["count"]) for x in blocks]==[
        (41,[47,54],8),(43,[74,89],16),(44,[1,39],39),(45,[34,37],4)]
    assert len(data["candidates"])==4
    seen=set()
    rows=[]
    for candidate in data["candidates"]:
        id_=candidate["lesson_id"]
        assert id_ in EXPECTED and id_ not in seen
        seen.add(id_)
        original=source["records"][int(id_[-3:])-1]
        assert original["id"]==id_ and original["withheld"] is True
        assert original["verified_ready"] is False
        assert original["state"]=="TAHAN_SEMAKAN_KANDUNGAN"
        assert "fields" not in original and "intro" not in original
        assert candidate["original_withheld_unmodified"] is True
        assert candidate["source_verse_ranges"]==EXPECTED[id_]
        assert candidate["source_juz"]==(29 if id_=="T6-L117" else 25)
        assert candidate["publication"]=="HOLD"
        assert candidate["editor_preview_only"] is True
        assert candidate["draft_language"]=="RUMI_EDITOR_PENDING_JAWI"
        assert "bukan kod SP rasmi DSKP" in candidate["curriculum_label"]
        if id_=="T6-L117":
            assert id_ in LESSONS
            assert candidate["source_rpt_pdf_page"]==41
        else:
            assert id_ in ASSIGNED
            assert candidate["source_rpt_pdf_page"]=={"T6-L006":3,"T6-L014":5,"T6-L018":7}[id_]
        draft=candidate["rph_editor_draft"]
        assert len(draft["learning_outcomes"])==2
        assert len(draft["aktiviti_utama"])==4
        for n,item in enumerate(draft["aktiviti_utama"],1):
            assert item.startswith(str(n)+". ")
        assert all(draft[x].strip() for x in ("set_induksi","pengukuhan","pentaksiran","penutup","bahan"))
        assert "jul" in draft["pentaksiran"].lower()
        assert draft["editor_warning"]
        checks=candidate["reviewer_checks"]
        assert checks["original_rpt_range_copied_as_reference"] is True
        assert checks["source_quran_chapter_verse_bounds_validated"] is True
        for key in ("teaching_assignment_suitability_verified",
                    "source_omission_allocation_resolved",
                    "original_dskp_specific_sp_claimed",
                    "literal_quran_text_transcribed",
                    "content_expert_approved","jawi_orthography_approved",
                    "pedagogy_and_pbd_approved",
                    "actual_live_pdf_word_generator_verified","can_publish"):
            assert checks[key] is False,(id_,key)
        rows.append({"id":id_,"original_source_held":True,
                     "rpt_verse_ranges":candidate["source_verse_ranges"],
                     "steps":4,"draft_language":candidate["draft_language"],
                     "jawi_checked":False,"academic_approved":False,
                     "release":"NO_GO"})
    assert seen==set(EXPECTED)
    return {
        "purpose":"Four editor-only Quran proposals, none added to published Year6 catalog",
        "source_held_originals_untouched":4,
        "editor_candidates_created":4,
        "year6_juz25_ayah_omitted":67,
        "juz29_l117_local_three_surah_gap":0,
        "actual_teacher_ayah_assignments_approved":0,
        "jawi_expert_approvals":0,
        "curriculum_sp_codes_fabricated":0,
        "public_teacher_rph_added":0,
        "release":"NO_GO",
        "rows":rows,
    }


def write(path,root=ROOT):
    r=audit(root)
    Path(path).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    a=p.parse_args();write(a.output)
