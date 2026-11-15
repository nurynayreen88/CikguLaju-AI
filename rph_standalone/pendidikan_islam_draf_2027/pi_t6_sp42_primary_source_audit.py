"""Source-bounded Year6 SK4.2 inspection, non-destructive editor draft only.

Original official DSKP PI Year6:
 PDF page 46, printed page 34, codes 4.2.3/4.2.4/4.2.5.
RPT CikguLaju 2027 PDF page 21:
 PdP059 uses these codes; PdP060 is explicitly a *CikguLaju proposal*.
The official existence of SP codes does NOT make PdP060 an official separate
Lesson, confirm specific prayer-posture fiqh, or approve unreviewed Jawi.

Year6 L060 in source catalog remains WITHHELD. The additional candidate
JSON file is review-only, separate from runtime, and cannot be published.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pi_quality_audit import ROOT

CANDIDATE="pi_t6_l060_amali_editor_candidate.json"
DSKP_ID="1pasG1F0ThshBUNoyLtQCD867bIkhekTZ"
DSKP_SHA="fd12636abb8b220623ec8c33a0c12261c7f27adc44c02efc5ee2ac04b71fea45"
RPT_ID="1T380Ot_gG58JhxanELMM0z-gr6wmSJcL"
RPT_SHA="b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b"
SP=("4.2.3","4.2.4","4.2.5")
OLD_KBAT="اڤاكه ڤربيذاءن تاتاچارا صلاة دڠن اݢام لاءين؟"
NEW_KBAT="باݢايمان چارا منونايكن صلاة كتيك ساكيت مڠيكوت كممڤوان؟"


def audit(root=ROOT):
    root=Path(root)
    d=json.loads((root/"year6.json").read_text(encoding="utf-8"))
    assert d["year"]==6 and d["ready"] is False and len(d["records"])==143
    prev=d["records"][58]
    held=d["records"][59]
    assert prev["id"]=="T6-L059" and not prev["withheld"]
    assert held["id"]=="T6-L060" and held["withheld"] is True
    assert held["verified_ready"] is False and held["state"]=="TAHAN_SEMAKAN_KANDUNGAN"
    assert "fields" not in held and "intro" not in held
    meta=prev["staging_dskp_42_source_editorial_review"]
    assert meta["revision"]=="pi-t6-sp42-dskp-p34-rpt-p21-20261107"
    assert meta["dskp_file_id"]==DSKP_ID and meta["dskp_sha256"]==DSKP_SHA
    assert meta["dskp_pdf_page"]==46 and meta["dskp_printed_page"]==34
    assert meta["sp_codes_visually_observed"]==list(SP)
    assert meta["rpt_file_id"]==RPT_ID and meta["rpt_sha256"]==RPT_SHA
    assert meta["rpt_pdf_page"]==21 and meta["rpt_pdp_index"]==59
    assert OLD_KBAT in meta["original_pentaksiran"]
    assert meta["original_kbat_question"]==OLD_KBAT
    assert NEW_KBAT==meta["revised_kbat_question"]
    assert NEW_KBAT in prev["fields"]["pentaksiran"]
    assert OLD_KBAT not in prev["fields"]["pentaksiran"]
    assert prev["fields"]["pentaksiran"]==meta["original_pentaksiran"].replace(OLD_KBAT,NEW_KBAT)
    for c in SP:
        assert c in prev["fields"]["sp"]
    for k in ("original_sk_sp_unchanged","all_other_fields_unchanged",
              "unrelated_religion_comparison_removed","dskp_code_presence_verified"):
        assert meta[k] is True,(k,meta[k])
    for k in ("full_jawi_sp_wording_verified","fiqh_practice_expert_approved",
              "jawi_orthography_approved","pbd_expert_approved",
              "native_word_pdf_verified"):
        assert meta[k] is False
    assert meta["publication"]=="HOLD"
    candidate=json.loads((root/CANDIDATE).read_text(encoding="utf-8"))
    assert candidate["schema"]=="cikgulaju_pi_editor_only_candidate_v1"
    assert candidate["lesson_id"]=="T6-L060" and candidate["lesson"]==60
    assert candidate["catalog_original_record_remains_withheld"] is True
    assert candidate["candidate_kind"]=="ADDITIONAL_CIKGULAJU_PRACTICE_LESSON_NOT_OFFICIAL_DSKP_SEPARATE_LESSON"
    assert candidate["publication"]=="HOLD" and candidate["verified_ready"] is False
    assert candidate["allowed_in_teacher_web_or_telegram"] is False
    ev=candidate["evidence"]
    assert ev["dskp_source_drive_id"]==DSKP_ID and ev["dskp_pdf_sha256"]==DSKP_SHA
    assert ev["dskp_pdf_page"]==46 and ev["dskp_printed_page"]==34
    assert ev["dskp_sk_code"]=="4.2" and ev["dskp_sp_codes"]==list(SP)
    assert ev["dskp_sp_codes_visually_confirmed"] is True
    assert ev["dskp_full_jawi_wording_signed_off"] is False
    assert ev["rpt_drive_id"]==RPT_ID and ev["rpt_pdf_sha256"]==RPT_SHA
    assert ev["rpt_pdf_page"]==21 and ev["rpt_pdp_index"]==60
    assert ev["rpt_declares_cikgulaju_suggestion"] is True
    assert ev["prior_pdp_index"]==59
    c=candidate["editorial_draft"]
    assert c["sp_codes"]==list(SP) and c["sk"].startswith("4.2")
    assert c["bidang"]=="عبادة"
    assert len(c["objective"])==3
    assert len(c["aktiviti_utama"])==4
    assert all(x.startswith(str(i)+". ") for i,x in enumerate(c["aktiviti_utama"],1))
    for key in ("set_induksi","pengukuhan","pentaksiran","penutup","bahan"):
        assert c[key].strip()
    flags=candidate["release_checks"]
    assert flags["source_code_exists_in_official_dskp"] is True
    assert flags["original_year6_l060_record_modified"] is False
    for key in ("official_independent_pdp_no","full_fiqh_and_dskp_wording_verified",
                "prayer_posture_examples_checked_by_teacher","jawi_orthography_approved",
                "content_expert_approved","actual_runtime_word_pdf_approved",
                "eligible_for_teacher_use"):
        assert flags[key] is False,(key,flags[key])
    return {
        "purpose":"Original DSKP source verifies SP codes, not suggested CikguLaju PdP release",
        "source_dskp_file_id":DSKP_ID,
        "source_dskp_pdf_page":46,
        "source_dskp_printed_page":34,
        "sp_codes_visually_present":list(SP),
        "rpt_pdf_page":21,
        "rpt_additional_pdp_declared_as_cikgulaju_suggestion":True,
        "l059_kbat_off_topic_question_replaced":1,
        "l059_original_assessment_preserved":True,
        "l060_editor_candidate_created":1,
        "l060_original_year6_record_still_wholly_held":True,
        "l060_editor_candidate_main_activity_steps":4,
        "independent_official_dskp_lesson_numbers_claimed":0,
        "expert_fiqh_approvals":0,
        "expert_jawi_approvals":0,
        "eligible_teacher_lessons":0,
        "can_publish":False,
        "release":"NO_GO"
    }


def write(path,root=ROOT):
    result=audit(root)
    Path(path).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    a=p.parse_args()
    write(a.output)
