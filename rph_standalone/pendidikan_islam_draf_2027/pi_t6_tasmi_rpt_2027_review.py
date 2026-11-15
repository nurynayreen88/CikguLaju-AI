"""Year 6 2027 Juz 30 tasmi' RPT source review; **not** DSKP SP accreditation.

Source RPT 2027 pages 48-49 identifies four surahs per PdP but does not
give explicit starting/ending verses. Original DSKP KSSR Year6 printed
p19 (PDF p31) instead specifies SK1.1 tilawah Surah al-Sharh.
Two Year6 tasmi' lessons are thus tagged as RPT-based editorial planning
rather than invented 3-level official DSKP standard.
All selected ayah ranges must be entered and checked by a teacher before use.

The book, RPT and DSKP PDFs live in the user's Drive; CI stores only
opaque source IDs/hashes, not source contents or a textbook scan.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from pi_quality_audit import ROOT

PLAN = {
    "T6-L137": (48, ["سورة عبس","سورة التكوير","سورة الإنفطار","سورة المطففين"]),
    "T6-L141": (49, ["سورة الطارق","سورة الأعلى","سورة الغاشية","سورة الفجر"]),
}
RPT_ID="1T380Ot_gG58JhxanELMM0z-gr6wmSJcL"
RPT_HASH="b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b"
DSKP_ID="1pasG1F0ThshBUNoyLtQCD867bIkhekTZ"
DSKP_HASH="fd12636abb8b220623ec8c33a0c12261c7f27adc44c02efc5ee2ac04b71fea45"
BOOK_ID="10eHX0E_yg3TOpGvaRTtwBevO90Nq-buf"
BOOK_HASH="d2f9de10d1e848afaa4c61cf1a8635079883966ebf5b05c3559459c37d050e74"
FIELD_NAMES=("id","rpt_pdf_page","surahs","four_activity_steps",
             "source_sk_sp_preserved","original_fields_preserved",
             "actual_ayah_range_verified","teacher_selection_required",
             "is_official_dskp_three_level_sp","jawi_approved",
             "content_expert_approved","runtime_pdf_verified","can_publish","release")


def audit(root=ROOT):
    d=json.loads((Path(root)/"year6.json").read_text(encoding="utf-8"))
    assert d["year"]==6 and d["ready"] is False and len(d["records"])==143
    rows=[]
    found=set()
    for r in d["records"]:
        meta=r.get("staging_tasmi_rpt_2027_review")
        if meta is None:
            continue
        identity=r["id"]
        assert identity in PLAN and identity not in found
        found.add(identity)
        source_page, expected_surahs=PLAN[identity]
        assert r["withheld"] is False and r["verified_ready"] is False
        assert r["staging_source_review_required"] is True
        assert meta["revision"]=="pi-t6-tasmi-rpt2027-juz30-two-lessons-20261107"
        assert meta["rpt_drive_file_id"]==RPT_ID and meta["rpt_sha256"]==RPT_HASH
        assert meta["dskp_drive_file_id"]==DSKP_ID and meta["dskp_sha256"]==DSKP_HASH
        assert meta["textbook_drive_file_id"]==BOOK_ID and meta["textbook_sha256"]==BOOK_HASH
        assert meta["textbook_is_scanned_no_text_layer"] is True
        assert meta["dskp_pdf_page_for_1_1"]=="31" and meta["dskp_printed_page_for_1_1"]==19
        assert meta["dskp_quran_1_1_specific_sura"]=="سورة الشرح"
        assert meta["rpt_pdf_page"]==source_page
        assert meta["source_surah_list"]==expected_surahs
        assert meta["rpt_2027_has_exact_ayah_ranges_for_this_pdp"] is False
        assert meta["dskp_1_1_covers_only_sharh_not_the_four_surah_list"] is True
        assert meta["teacher_must_select_and_record_exact_ayah_ranges_before_pdp"] is True
        assert meta["actual_ayah_range_verified"] is False
        assert meta["mushaf_page_or_verses_approved"] is False
        assert meta["no_three_level_dskp_sp_codes_assigned"] is True
        assert meta["curriculum_status"]=="RPT-2027-BASED_END_YEAR_TASMI_NOT_OFFICIAL_DSKP_SP"
        assert meta["original_four_surahs_preserved"] is True
        assert meta["original_source_sk_sp_unchanged"] is True
        fields=r["fields"];old=meta["original_fields_preserved"]
        assert fields["sk"]==old["sk"] and fields["sp"]==old["sp"]
        assert fields["bahan"]==old["bahan"] and fields["penutup"]==old["penutup"]
        assert fields["sp"].startswith("جزء 30 :")
        for surah in expected_surahs:
            assert surah in old["sp"] and surah in fields["sp"]
            assert surah in fields["objektif"]
        assert len(old["aktiviti_utama"].splitlines())==2
        steps=fields["aktiviti_utama"].splitlines()
        assert len(steps)==4
        assert all(step.startswith(f"{n}. ") for n,step in enumerate(steps,1))
        assert "RPT" in steps[0] and "جولتن اية" in steps[0]
        assert "تلقي" in steps[1] and "مشافهة" in steps[1]
        assert "تسميع" in steps[2] and "ممبتولكن" in steps[2]
        assert "كلنچرن" in steps[3] and "جولتن اية" in steps[3]
        assert "سناراي سمق" in fields["pentaksiran"]
        assert "جولتن اية" in fields["pentaksiran"]
        assert "سورة" in fields["objektif"]
        assert meta["selection_per_student_across_four_surahs_expert_approved"] is False
        assert meta["academic_expert_approved"] is False
        assert meta["jawi_orthography_approved"] is False
        assert meta["native_telegram_web_generator_verified"] is False
        assert meta["publication"]=="HOLD"
        rows.append({
            "id":identity,
            "rpt_pdf_page":source_page,
            "surahs":"|".join(expected_surahs),
            "four_activity_steps":len(steps),
            "source_sk_sp_preserved":True,
            "original_fields_preserved":True,
            "actual_ayah_range_verified":False,
            "teacher_selection_required":True,
            "is_official_dskp_three_level_sp":False,
            "jawi_approved":False,
            "content_expert_approved":False,
            "runtime_pdf_verified":False,
            "can_publish":False,
            "release":"NO_GO",
        })
    assert found==set(PLAN) and len(rows)==2
    assert all(not x["can_publish"] and x["release"]=="NO_GO" for x in rows)
    return {
        "purpose":"RPT-based Year6 tasmi' end-year staged enrichment, not DSKP code",
        "rpt_drive_id":RPT_ID,"rpt_sha256":RPT_HASH,
        "dskp_drive_id":DSKP_ID,"dskp_sha256":DSKP_HASH,
        "textbook_drive_id":BOOK_ID,"textbook_sha256":BOOK_HASH,
        "rpt_pages_checked":[48,49],
        "year6_tasmi_rph_activities_revised":2,
        "total_planned_surahs_referenced":8,
        "four_step_lesson_plans":2,
        "ayah_bounds_present_in_original_rpt":0,
        "fabricated_official_dskp_codes":0,
        "verse_ranges_teacher_verified":0,
        "rph_approved_for_teacher_use":0,
        "jawi_expert_approvals":0,
        "can_publish":False,
        "release":"NO_GO",
        "rows":rows,
    }


def write(json_path,csv_path,root=ROOT):
    result=audit(root)
    Path(json_path).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with Path(csv_path).open("w",encoding="utf-8-sig",newline="") as target:
        writer=csv.DictWriter(target,fieldnames=FIELD_NAMES)
        writer.writeheader();writer.writerows(result["rows"])
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json",required=True)
    p.add_argument("--csv",required=True)
    a=p.parse_args()
    write(a.json,a.csv)
