"""Fail-closed per-year release-readiness report for PI 2027 staging drafts.

The source catalog is not installed in Telegram/Web; no row is publishable.
Format coverage, an editor's TOC check and draft Jawi candidates are never
counted as academic quality or expert approval. This report is NOT a release.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

from pi_quality_audit import ROOT, COUNT, audit
from pi_closing_jawi_candidates_complete import generate as jawi_candidates
from pi_t2_textbook_toc_review import audit as source_toc
from pi_t2_54_direct_source_review import audit as direct_sp_54
from pi_t2_dskp_code_presence import audit as dskp_code_index
from pi_t3_awalan_book_review import audit as awalan_t3
from pi_t3_book_footer_code_audit import audit as book_footer_t3
from pi_t4_hadith_source_audit import audit as hadith_t4
from pi_t6_tasmi_rpt_2027_review import audit as tasmi_t6
from pi_y6_held_rpt_2027_source_review import audit as held_y6
from pi_t6_sp42_primary_source_audit import audit as sp42_y6
from pi_t2_l035_rpt_2026_2027_overlap_audit import audit as l035_t2
from pi_ba_match_queue import match_queue
from pi_review_catalog import counts as preview_counts


def readiness(root=ROOT):
    root = Path(root)
    qa = audit(root)
    jawi = jawi_candidates(root)
    toc = source_toc(root)
    direct = direct_sp_54(root)
    code_index = dskp_code_index(root)
    awalan = awalan_t3(root)
    book3 = book_footer_t3(root)
    hadith = hadith_t4(root)
    tasmi = tasmi_t6(root)
    held_source = held_y6(root)
    sp42 = sp42_y6(root)
    overlap = l035_t2(root)
    ba = match_queue(root)
    preview = preview_counts(root=root)
    assert qa["total"] == 696 and qa["drafts"] == 690 and qa["held"] == 6
    assert qa["critical_source_review_count"] == 3
    assert preview == {
        "total": 696, "draf": 690, "held": 6,
        "critical_source_hold": 3, "preview_eligible": 687, "ready": 0,
    }
    assert jawi["candidate_covered_lesson_occurrences"] == 690
    assert jawi["approved"] == 0 and jawi["jawi_spelling_verified"] == 0
    assert toc["notes_checked"] == 77
    assert toc["out_of_book_end_page_claims"] == 3
    assert toc["specific_lesson_page_verified"] == 0
    assert direct["directly_cross_checked_lesson_count"] == 3
    assert direct["sp_543_jawi_wording_corrections"] == 2
    assert direct["lesson_specific_activity_approvals"] == 0
    assert code_index["indexed_dskp_sp_codes"] == 83
    assert code_index["coded_lessons_with_all_codes_present"] == 81
    assert code_index["tasmi_verse_range_lessons_without_official_3_level_sp"] == 30
    assert awalan["year3_awalan_lessons_with_direct_book_unit_reference"] == 12
    assert awalan["legacy_pdf_page34_hints_wrong_next_unit"] == 6
    assert awalan["specific_lesson_prefix_examples_approved"] == 0
    assert book3["year3_lessons_with_book_footer_code_present"] == 109
    assert book3["year3_lessons_with_book_footer_code_not_observed"] == 1
    assert book3["dskp_6433_visually_confirmed"] is True
    assert book3["tasmi_verse_based_lessons_without_three_level_sp"] == 37
    assert qa["dskp_l146_alignment_editorial_review_count"] == 1
    assert qa["t4_hadith_source_excerpt_editorial_review_count"] == 1
    assert hadith["staging_source_excerpt_recovered"] == 1
    assert hadith["expert_hadith_approvals"] == 0
    assert hadith["source_missing_critical_flag_still_holds"] is True
    assert tasmi["year6_tasmi_rph_activities_revised"] == 2
    assert held_source["year6_held_lessons_checked"] == 5
    assert held_source["generated_held_rph"] == 0
    assert sp42["l060_editor_candidate_created"] == 1
    assert overlap["original_year2_l035_record_still_wholly_held"] is True
    assert overlap["overlap_present_in_original_2026_rpt"] is True
    assert overlap["intentional_revision_vs_source_typo_resolved"] is False
    assert sp42["l060_original_year6_record_still_wholly_held"] is True
    assert sp42["independent_official_dskp_lesson_numbers_claimed"] == 0
    assert qa["t6_sp42_edited_kbat_review_count"] == 1
    assert tasmi["ayah_bounds_present_in_original_rpt"] == 0
    assert tasmi["verse_ranges_teacher_verified"] == 0
    assert qa["t6_tasmi_rpt_editorial_range_review_count"] == 2
    assert book3["objective_and_pbd_drafted_to_dskp_643_645"] == 1
    assert book3["objective_and_pbd_expert_approvals"] == 0
    assert ba["refined_page_review_candidates"] == 174
    assert ba["oral_and_tasmi_no_forced_book"] == 84
    assert ba["confirmed_exercise_pages"] == 0

    grouped = {}
    rows = qa["records"]
    for year, expected in COUNT.items():
        block = [r for r in rows if r["id"].startswith(f"T{year}-")]
        assert len(block) == expected
        counter = Counter(x for r in block for x in r["flags"])
        notes_pending = counter["RUJUKAN_HALAMAN_BELUM_DISAHKAN"]
        grouped[str(year)] = {
            "year": year,
            "total_lessons": expected,
            "draft_lessons": expected-counter["TAHAN_KANDUNGAN"],
            "full_source_held": counter["TAHAN_KANDUNGAN"],
            "critical_source_hold": counter["SUMBER_KRITIKAL_BELUM_LENGKAP"],
            "eligible_only_for_editor_preview": expected-counter["TAHAN_KANDUNGAN"]-
                                                counter["SUMBER_KRITIKAL_BELUM_LENGKAP"],
            "closing_jawi_candidate_exists": expected-counter["TAHAN_KANDUNGAN"],
            "closing_jawi_approved": 0,
            "pbd_focused_rewrites_pending_expert": counter["PBD_SP_SASARAN_BELUM_DISAH_PAKAR"],
            "outdated_page_notes_pending_sp_match": notes_pending,
            "page_claims_past_book_end": counter["HALAMAN_BUKU_T2_MELEBIHI_MUKA_TERAKHIR"],
            "direct_dskp_textbook_sp_footer_crosschecked": 3 if year == 2 else 0,
            "exact_lesson_activity_approvals": 0,
            "source_dskp_code_presence_verified_only": 81 if year == 2 else 0,
            "tasmi_lessons_not_assigned_official_3_level_sp": 30 if year == 2 else 0,
            "source_textbook_awalan_unit_refs": 12 if year == 3 else 0,
            "old_pdf34_cross_topic_page_hints": 6 if year == 3 else 0,
            "book_footer_sp_code_present_only": 109 if year == 3 else 0,
            "book_footer_missing_but_dskp_manually_seen": 1 if year == 3 else 0,
            "l146_objective_activity_pbd_revised_pending_expert": counter["DSKP_T3_L146_OBJECTIVE_PBD_REVISED_EXPERT_PENDING"],
            "hadith_excerpt_from_original_source_pending_expert": counter["HADIS_T4_PETIKAN_BUKU_DSKP_DRAF_SEMAK_PAKAR"],
            "year6_tasmi_rpt_ayah_ranges_teacher_pending": counter["TASMI_T6_RPT_AYAT_BELUM_DITETAPKAN_GURU"],
            "year6_wholly_held_source_triaged_no_release": 5 if year == 6 else 0,
            "source_dskp_sp42_kbat_rewritten_pending_expert": counter["T6_SP42_KBAT_DIPERBETUL_SEMAK_PAKAR"],
            "tasmi_verse_descriptions_without_3_level_sp": 37 if year == 3 else 0,
            "short_activity_source_hold": counter["AKTIVITI_TERLALU_RINGKAS_PERLU_SEMAKAN"],
            "expert_approved_lesson_count": 0,
            "ready_for_teacher": 0,
        }
    assert sum(x["eligible_only_for_editor_preview"] for x in grouped.values()) == 687
    assert sum(x["closing_jawi_candidate_exists"] for x in grouped.values()) == 690
    # Evidence needed before a future release decision; no implicit approval.
    blockers = [
        {"code": "YEAR2_L035_SOURCE_INHERITED_AYAH224_OVERLAP", "affected_lessons": 1,
         "action": "RPT Year2 2026 already assigns al-Baqarah 216-224 then 224-245; 2027 flags the overlap. An editor/teacher must decide explicit repetition vs source error; do not fabricate a new verse boundary"},
        {"code": "HELD_SOURCE_CONTENT", "affected_lessons": qa["held"],
         "action": "Complete verified source text before generating a teacher RPH"},
        {"code": "CRITICAL_HADIS_OR_QURAN_BOUNDARY", "affected_lessons": 3,
         "action": "T4-L083 sourced excerpt from textbook p51/DSKP p27 needs expert/Jawi review. T6-L137/141 RPT2027 gives four surahs but no ayah limits; teacher must assign exact verse bounds in mushaf before use"},
        {"code": "Y6_SP42_OPTIONAL_AMALI_TEACHER_HOLD", "affected_lessons": 1,
         "action": "T6-L060 remains withheld. DSKP p34 confirms 4.2.3–4.2.5 as official codes; RPT p21 calls PdP60 optional CikguLaju practical. Review candidate fiqh/Jawi/PBD before any curriculum publication"},
        {"code": "JAWI_EDITOR_CANDIDATES_NOT_APPROVED", "affected_lessons": 690,
         "action": "Verify Jawi orthography, terminology and suitability by named reviewers"},
        {"code": "PBD_REFINEMENTS_PENDING_EXPERT", "affected_lessons": 43,
         "action": "Check each new assessment criterion against original DSKP SP"},
        {"code": "BOOK_TEXT_OLD_PAGE_CLAIMS", "affected_lessons": 77,
         "action": "Verify each Lesson/SP match directly on actual printed book pages"},
        {"code": "BOOK_TEXT_LAST_PAGE_OVERRUN", "affected_lessons": 3,
         "action": "Original notes 133-140 are beyond textbook end; verify activity/PBD per Lesson against observed p134-136, then approve an edited note separately"},
        {"code": "YEAR3_6433_DSKP_BOOK_FOOTER_AND_L146_OBJECTIVE_REVIEW",
         "affected_lessons": 1,
         "action": "T3-L146: official DSKP SP6.4.3 is retained; objective 2 'merumus', objective 3 'mengamalkan', 4 steps and revised PBD are DRAFT only; verify Jawi, SP alignment and book-footer omission with academic reviewer"},
        {"code": "ACTIVITY_BOOK_MATCHES_UNVERIFIED", "affected_lessons": 174,
         "action": "Check BA exercise and printed page on original Year 2/3 editions"},
        {"code": "CONTENT_EXPERT_PER_LESSON_APPROVAL", "affected_lessons": 690,
         "action": "Review SK, SP, activities, learning objectives and assessment"},
        {"code": "RUNTIME_WORD_PDF_VISUAL_TEST", "affected_lessons": 687,
         "action": "Verify actual Telegram/Web generator, Arabic joins and A4 print"},
        {"code": "YEAR1_KP2027_OUT_OF_SCOPE", "affected_lessons": None,
         "action": "Audit Year 1 KP2027 independently of old KSSR Year 2-6 catalogue"},
    ]
    assert sum(x["expert_approved_lesson_count"] for x in grouped.values()) == 0
    return {
        "subject": "Pendidikan Islam",
        "scope": "KSSR 2027 staging Tahun 2–6; Tahun 1 excluded",
        "catalog_total": 696,
        "drafts": 690,
        "held": 6,
        "critical_source_review": 3,
        "editor_preview_eligible": 687,
        "prepared_closing_jawi_candidates": 690,
        "expert_approved_jawi_candidates": 0,
        "reviewed_textbook_toc_ranges": 77,
        "toc_ranges_consistent_with_book": 74,
        "invalid_book_end_page_claims": 3,
        "direct_dskp_textbook_sp_footer_lesson_crosschecks": 3,
        "source_supported_sp543_jawi_wording_fixes": 2,
        "year2_dskp_codes_indexed": 83,
        "year2_lessons_with_existing_dskp_sp_codes": 81,
        "year2_tasmi_lessons_without_invented_sp": 30,
        "year2_full_sp_text_accuracy_verified": 0,
        "year3_awalan_direct_book_unit_references": 12,
        "year3_legacy_pdf34_hints_next_unit": 6,
        "year3_awalan_prefix_examples_expert_approved": 0,
        "year3_book_footer_code_present_lesson_count": 109,
        "year3_book_footer_exception_dskp_confirmed": 1,
        "year3_l146_dskp_643_645_objective_activity_pbd_revised_draft": 1,
        "year3_l146_expert_approved": 0,
        "year4_l083_original_hadith_excerpt_cited_in_draft": 1,
        "year4_l083_hadith_expert_approved": 0,
        "year6_tasmi_four_step_rph_drafts": 2,
        "year6_tasmi_rpt_ayah_ranges_teacher_verified": 0,
        "year6_tasmi_official_dskp_codes_invented": 0,
        "year6_full_source_hold_records_reviewed_against_rpt": 5,
        "year6_full_source_hold_records_generated": 0,
        "year6_sp42_official_dskp_sp_codes_confirmed": 3,
        "year6_l059_offtopic_kbat_repaired_editorially": 1,
        "year6_l060_optional_amali_candidate_created_held": 1,
        "year6_l060_original_catalog_still_held": True,
        "year6_l060_official_separate_lesson_claims": 0,
        "year2_l035_ayah224_overlap_inherited_from_2026_rpt": 1,
        "year2_l035_ayah224_overlap_academically_resolved": 0,
        "year3_tasmi_verse_lessons_not_given_fake_sp": 37,
        "teacher_approved_page_specific_exercises": 0,
        "book_activity_page_candidates": 174,
        "book_activity_exercises_verified": 0,
        "individual_expert_approvals": 0,
        "native_telegram_web_rph_pdf_verified": 0,
        "mechanical_three_step_coverage_percent": qa["mechanical_three_step_coverage_percent"],
        "academic_quality_percent": None,
        "academic_quality_80_certified": False,
        "ready_count": 0,
        "status": "HOLD",
        "can_merge_or_publish": False,
        "decision": "NO_GO",
        "by_year": grouped,
        "release_blockers": blockers,
    }


def write(path, root=ROOT):
    result = readiness(root)
    Path(path).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "by_year" and k != "release_blockers"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    a = p.parse_args()
    write(a.output)
