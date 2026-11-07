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
from pi_ba_match_queue import match_queue
from pi_review_catalog import counts as preview_counts


def readiness(root=ROOT):
    root = Path(root)
    qa = audit(root)
    jawi = jawi_candidates(root)
    toc = source_toc(root)
    direct = direct_sp_54(root)
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
            "short_activity_source_hold": counter["AKTIVITI_TERLALU_RINGKAS_PERLU_SEMAKAN"],
            "expert_approved_lesson_count": 0,
            "ready_for_teacher": 0,
        }
    assert sum(x["eligible_only_for_editor_preview"] for x in grouped.values()) == 687
    assert sum(x["closing_jawi_candidate_exists"] for x in grouped.values()) == 690
    # Evidence needed before a future release decision; no implicit approval.
    blockers = [
        {"code": "HELD_SOURCE_CONTENT", "affected_lessons": qa["held"],
         "action": "Complete verified source text before generating a teacher RPH"},
        {"code": "CRITICAL_HADIS_OR_QURAN_BOUNDARY", "affected_lessons": 3,
         "action": "Find full matan and surah/ayat bounds in authoritative texts"},
        {"code": "JAWI_EDITOR_CANDIDATES_NOT_APPROVED", "affected_lessons": 690,
         "action": "Verify Jawi orthography, terminology and suitability by named reviewers"},
        {"code": "PBD_REFINEMENTS_PENDING_EXPERT", "affected_lessons": 43,
         "action": "Check each new assessment criterion against original DSKP SP"},
        {"code": "BOOK_TEXT_OLD_PAGE_CLAIMS", "affected_lessons": 77,
         "action": "Verify each Lesson/SP match directly on actual printed book pages"},
        {"code": "BOOK_TEXT_LAST_PAGE_OVERRUN", "affected_lessons": 3,
         "action": "Check p133-138 proposed section for T2-L102,105,108"},
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
