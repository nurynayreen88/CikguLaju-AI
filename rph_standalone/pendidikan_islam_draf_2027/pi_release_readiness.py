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
from pi_t6_juz25_sequence_gap_audit import audit as sequence_juz25
from pi_t6_juz29_l117_continuity_review import audit as sequence_juz29
from pi_t6_held_quran_editor_candidate_review import audit as held_quran_proposals
from pi_t6_juz25_rpt2026_source_provenance import audit as juz25_legacy_provenance
from pi_ba_match_queue import match_queue
from pi_review_catalog import counts as preview_counts
# These audits cover newly corrected source-content errors, not just layout.
from pi_quran_114_surah_range_audit import audit as quran_114_audit
from pi_surah_pbd_alignment_audit import audit as surah_pbd_audit
from pi_primary_source_fiqh_copyedit_audit import audit as fiqh_source_audit
from pi_t3_solat_case_sequence_audit import audit as solat_sequence_audit
from pi_tasmi_continuity_quality_guard import audit as tasmi_continuity_audit
from pi_rpt_source_errata_editor_register import audit as rpt_errata_audit
from pi_heavy_tasmi_editor_overlay import generate as heavy_tasmi_editor
from pi_y5_khat_nasakh_source_audit import audit as year5_khat_source_audit
from pi_y5_khat_nasakh_editor_overlay import generate as year5_khat_editor
from pi_tajwid_crossfield_mad_audit import audit as tajwid_mad_crossfield


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
    juz25 = sequence_juz25(root)
    juz29 = sequence_juz29(root)
    held_quran = held_quran_proposals(root)
    legacy = juz25_legacy_provenance(root)
    ba = match_queue(root)
    preview = preview_counts(root=root)
    # Fail closed when a new academic-source regression occurs: a passing
    # older release report must never bypass these newer audit modules.
    quran_114 = quran_114_audit(root)
    surah_pbd = surah_pbd_audit(root)
    fiqh_source = fiqh_source_audit(root)
    solat_sequence = solat_sequence_audit(root)
    tasmi_continuity = tasmi_continuity_audit(root)
    rpt_errata = rpt_errata_audit(root)
    heavy_tasmi = heavy_tasmi_editor(root)
    year5_khat_source = year5_khat_source_audit(root)
    year5_khat_preview = year5_khat_editor(root)
    mad_crossfield = tajwid_mad_crossfield(root)
    assert mad_crossfield["single_named_mad_source_lessons_checked"] == 30
    assert mad_crossfield["conflicting_mad_labels_remaining"] == 0
    assert mad_crossfield["source_corrected_year5_lessons"] == 3
    assert mad_crossfield["source_corrected_fields"] == 7
    assert mad_crossfield["expert_tajwid_approvals"] == 0
    assert mad_crossfield["release"] == "NO_GO"
    assert year5_khat_source["four_corrected_ayat_and_tekal_sp_records"] == 4
    assert year5_khat_source["source_printed_pages"] == [43,44]
    assert year5_khat_source["academic_expert_approvals"] == 0
    assert year5_khat_source["release"] == "NO_GO"
    assert year5_khat_preview["editor_proposed_improvements"] == 13
    assert year5_khat_preview["editor_changed_field_count"] == 30
    assert year5_khat_preview["preview_unsupported_official_activity_book_mentions"] == 0
    assert year5_khat_preview["new_source_verified_workbook_pages"] == 0
    assert year5_khat_preview["jawi_expert_approvals"] == 0
    assert year5_khat_preview["release"] == "NO_GO"
    assert heavy_tasmi["candidate_rph_activity_and_pbd_overlays"] == 14
    assert heavy_tasmi["original_catalog_files_overwritten"] == 0
    assert heavy_tasmi["official_ayah_boundaries_reassigned"] == 0
    assert heavy_tasmi["teacher_exact_subranges_assigned"] == 0
    assert heavy_tasmi["claim_to_have_completed_full_sp"] is False
    assert heavy_tasmi["teacher_ready"] == 0
    assert heavy_tasmi["release"] == "NO_GO"
    assert rpt_errata["rpt_source_conflict_lessons"] == 9
    assert rpt_errata["field_level_editor_comparisons"] == 13
    assert rpt_errata["approved_for_automatic_rpt_update"] == 0
    assert rpt_errata["teacher_ready"] == 0
    assert rpt_errata["release"] == "NO_GO"
    assert quran_114["unheld_drafts_examined"] == 690
    assert quran_114["invalid_chapter_verse_ranges"] == 0
    assert quran_114["crossfield_surah_verse_mismatches"] == 0
    assert quran_114["specialist_approved"] == quran_114["teacher_ready"] == 0
    assert surah_pbd["named_surah_or_pbd_range_remaining_mismatches"] == 0
    assert surah_pbd["lessons_with_precise_corrections"] == 11
    assert surah_pbd["curriculum_RPT2027_copy_errors_flagged"] == 7
    assert surah_pbd["teacher_publishable"] == 0
    assert fiqh_source["two_rukun_puasa_correction_applied_in_staging"] is True
    assert fiqh_source["original_rpt_year4_pdp107_six_rukun_incorrect"] is True
    assert fiqh_source["other_exact_word_duplicate_fixes"] == 3
    assert fiqh_source["expert_fiqh_approved"] is False
    assert fiqh_source["teacher_release"] is False
    assert solat_sequence["listed_case_numbers_covered_once"] == 18
    assert solat_sequence["rpt_2027_l059_original_objective_incorrect"] is True
    assert solat_sequence["expert_fiqh_approved"] is False
    assert solat_sequence["teacher_ready"] == 0
    assert tasmi_continuity["years_reviewed"] == 5
    assert tasmi_continuity["source_gaps_year2_l035_held_ayat225_to245"] == 21
    assert tasmi_continuity["source_juz25_original_year6_missing_ayah"] == 67
    assert tasmi_continuity["high_volume_60plus_ayah_source_lessons_for_teacher_review"] >= 10
    assert tasmi_continuity["expert_approved"] == tasmi_continuity["teacher_ready"] == 0
    assert all(result["release"] == "NO_GO" for result in
               (quran_114, surah_pbd, fiqh_source, solat_sequence, tasmi_continuity))
    assert qa["total"] == 696 and qa["drafts"] == 690 and qa["held"] == 6
    assert qa["critical_source_review_count"] == 3
    assert qa["unverified_year4_to6_activity_book_wording_count"] == 13
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
    assert juz25["juz25_ayah_missing_in_rpt"] == 67
    assert juz25["juz25_missing_non_overlapping_blocks"] == 4
    assert juz25["automatic_verse_reassignments"] == 0
    assert juz29["three_surahs_mapped_ayat"] == 100
    assert juz29["three_surahs_missing_ayat"] == 0
    assert juz29["original_l117_withheld"] is True
    assert held_quran["editor_candidates_created"] == 4
    assert held_quran["public_teacher_rph_added"] == 0
    assert legacy["legacy_out_of_bounds_shura_ayah_count"] == 24
    assert legacy["legacy_duplicated_shura_ayat_count"] == 2
    assert legacy["legacy_inherited_juz25_missing_ayat"] == 67
    assert legacy["newer_2027_juz25_missing_ayat"] == 67
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
            "year6_juz25_unmapped_ayah_in_rpt": 67 if year == 6 else 0,
            "year6_juz25_unmapped_ayah_spans": 4 if year == 6 else 0,
            "year6_2026_rpt_bad_shura_ayah_out_of_bounds": 24 if year == 6 else 0,
            "year6_2026_rpt_shura_duplicate_ayah": 2 if year == 6 else 0,
            "year6_juz29_l117_local_70_72_ayat_mapped": 100 if year == 6 else 0,
            "year6_held_quran_separate_editor_candidates": 4 if year == 6 else 0,
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
        {"code":"YEAR5_TAJWID_MAD_BADAL_IWAD_THREE_SOURCE_COPY_ERRORS_PENDING_EXPERT",
         "affected_lessons":mad_crossfield["source_corrected_year5_lessons"],
         "action":"Year5 L041/L045/L049 inherited RPH content wrongly referred to mad badal although SP targeted mad iwad. Original fields retained in staging; 30 single-mad source RPH checked with zero remaining cross-field mixups; expert tajwid/Jawi verification and textbook verse examples still required"},
        {"code":"YEAR5_KHAT_NASAKH_4_SOURCE_SP_CORRECTIONS_PENDING_EXPERT",
         "affected_lessons": year5_khat_source["four_corrected_ayat_and_tekal_sp_records"],
         "action":"Four Year5 khat PdP staged SP7.2.5 ayat and SP7.2.6 tekal from KPM DSKP p43-44; original text preserved, Jawi/lesson academic signoff and RPT source check pending"},
        {"code":"YEAR5_KHAT_NASAKH_13_EDITOR_PBD_AND_WORKSHEET_PENDING",
         "affected_lessons": year5_khat_preview["editor_proposed_improvements"],
         "action":"13 source RPH mention unverified Buku Aktiviti in PBD/activity. Restricted editor Word/PDF shows SP-specific huruf, perkataan, ayat PBD using teacher-made worksheets. No official Year5 workbook edition/page/exercise verified or linked; expert/Jawi approval pending"},
        {"code": "HEAVY_TASMI_14_EDITOR_ACTIVITIES_REQUIRE_TEACHER_SELECTION",
         "affected_lessons": heavy_tasmi["candidate_rph_activity_and_pbd_overlays"],
         "action": "14 Year5/6 lessons list 61-106 Quran ayat; editor Word/PDF now uses realistic individual selected passages, talaqqi and PBD but exact student verse range, Jawi accuracy, completion timing and full-SP mastery are unapproved"},
        {"code": "RPT_SOURCE_7_SURAH_COPIES_REQUIRE_CORRECTION",
         "affected_lessons": surah_pbd["curriculum_RPT2027_copy_errors_flagged"],
         "action": "Seven Year3/4 RPT2027 source entries retained wrong surah labels; staging RPH corrected them, but source RPT and final Jawi/Quran signoff are pending"},
        {"code": "YEAR4_RPT_PUASA_SIX_RUKUN_SOURCE_ERROR",
         "affected_lessons": 1,
         "action": "T4-L107 staging objective now says two rukun puasa as verified against textbook p130; original RPT still says six. Correct RPT separately and verify fiqh/Jawi before teacher use"},
        {"code": "YEAR3_RPT_SOLAT_L059_DUPLICATE_OBJECTIVE",
         "affected_lessons": 1,
         "action": "T3-L059 original RPT objective repeats cases 7-12. Staging RPH has cases 13-18 consistent with PdP051/055; source RPT correction and case-list fiqh signoff still pending"},
        {"code": "QURAN_TASMI_HIGH_VOLUME_TEACHER_TIMING",
         "affected_lessons": tasmi_continuity["high_volume_60plus_ayah_source_lessons_for_teacher_review"],
         "action": "More than 60 source Quran ayat in each flagged lesson require individual timing/tasmi selection, source validation and teacher approval; do not reassign ayat automatically"},
        {"code": "YEAR6_JUZ25_67_UNMAPPED_QURAN_AYAT", "affected_lessons": 7,
         "action": "RPT Year6 Juz25 maps 179/246 ayat across PdP002/006/010/014/018/022/026, missing Fussilat 41:47-54, Zukhruf 43:74-89, Dukhan 44:1-39 and Jathiyah 45:34-37 (67 ayat). RPT editor/teacher must map them; never invent a lesson or code"},
        {"code": "YEAR6_FOUR_QURAN_EDITOR_CANDIDATES_ONLY", "affected_lessons": 4,
         "action": "T6-L006/L014/L018/L117 now have separate Rumi reviewer drafts, NOT inserted into original withheld catalog; Quran ayat allocation, full Juz25 coverage, Jawi and tajwid signoff remain pending"},
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
        {"code": "YEAR5_JAWI_BUKU_AKTIVITI_WORDING_SOURCE_UNVERIFIED", "affected_lessons": 13,
         "action": "Nine Year5 Jawi PBD texts and four teaching-activity texts mention Buku Aktiviti, but its specific edition/page/exercise is not verified. Decide official workbook versus generic exercise book; retain original source, do not invent a workbook link"},
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
        "year6_juz25_verses_total": 246,
        "year6_juz25_verses_mapped_original_rpt": 179,
        "year6_juz25_verses_missing_original_rpt": 67,
        "year6_juz25_legacy_2026_verses_invalid": 24,
        "year6_juz25_legacy_2026_verses_duplicated": 2,
        "year6_juz25_legacy_2026_missing_verses_inherited": 67,
        "year6_juz25_missing_source_blocks": 4,
        "year6_juz29_l117_neighbour_chapters_70_to_72_ayat_verified": 100,
        "year6_quran_held_rumi_editor_candidates": 4,
        "year6_quran_candidate_expert_or_jawi_approved": 0,
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
        "year5_ambiguous_activity_book_source_mentions": qa["unverified_year4_to6_activity_book_wording_count"],
        "year5_khat_source_sp_code_and_objective_corrections": year5_khat_source["four_corrected_ayat_and_tekal_sp_records"],
        "single_mad_source_lessons_checked": mad_crossfield["single_named_mad_source_lessons_checked"],
        "tajwid_crossfield_mad_conflicts_remaining": mad_crossfield["conflicting_mad_labels_remaining"],
        "year5_mad_iwad_copyedit_lessons": mad_crossfield["source_corrected_year5_lessons"],
        "year5_mad_iwad_copyedit_fields": mad_crossfield["source_corrected_fields"],
        "year5_khat_editor_pbd_and_worksheet_overlays": year5_khat_preview["editor_proposed_improvements"],
        "year5_khat_editor_fields_changed": year5_khat_preview["editor_changed_field_count"],
        "year5_khat_official_activity_book_pages_verified": year5_khat_preview["new_source_verified_workbook_pages"],
        "quran_verse_range_occurrences_screened": quran_114["verse_range_occurrences_evaluated"],
        "quran_invalid_verse_ranges_in_staging": quran_114["invalid_chapter_verse_ranges"],
        "quran_sp_objective_pbd_range_mismatches_in_staging": quran_114["crossfield_surah_verse_mismatches"],
        "surah_crossfield_editor_corrections": surah_pbd["lessons_with_precise_corrections"],
        "surah_source_rpt_errors_pending": surah_pbd["curriculum_RPT2027_copy_errors_flagged"],
        "source_rpt_editor_errata_lesson_count": rpt_errata["rpt_source_conflict_lessons"],
        "source_rpt_editor_field_comparisons": rpt_errata["field_level_editor_comparisons"],
        "year4_rpt_puasa_six_rukun_error_pending": fiqh_source["original_rpt_year4_pdp107_six_rukun_incorrect"],
        "year3_rpt_solat_l059_copy_error_pending": solat_sequence["rpt_2027_l059_original_objective_incorrect"],
        "tasmi_source_high_volume_lessons_review_pending": tasmi_continuity["high_volume_60plus_ayah_source_lessons_for_teacher_review"],
        "heavy_tasmi_editor_rph_activity_pbd_overlays": heavy_tasmi["candidate_rph_activity_and_pbd_overlays"],
        "heavy_tasmi_student_ayah_allocations_verified": heavy_tasmi["teacher_exact_subranges_assigned"],
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
