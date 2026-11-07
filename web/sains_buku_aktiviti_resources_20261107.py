"""Staging-only download-card metadata for Science Year2/3 activity books.

For future Web and Telegram materials dropdowns AFTER curriculum signoff.
A book is one shared PDF per year, not 51/45 fabricated per-PdP PDFs.
Return only verified source links, never silently substitute a year/book or
serve copyrighted binary as app-owned media.
"""
from __future__ import annotations
from tools.sains_buku_aktiviti_mapping_20261107 import activity_for, is_direct_sp_match

def proposed_material(subject,year,pdp_code,sp):
    if str(subject).strip().casefold() not in ("sains","science") or year not in (2,3):
        return None
    e=activity_for(year,pdp_code,sp)
    return {
        "material_type":"BUKU_AKTIVITI",
        "name":f"Buku Aktiviti Sains Tahun {year}",
        "source_url":e["workbook_url"],
        "open_external_source":True,
        "download_method":"OPEN_GOOGLE_DRIVE_SOURCE__DO_NOT_INVENT_DIRECT_DOWNLOAD",
        "book_printed_page":e["workbook_printed_page"],
        "pdf_page_1_based":e["workbook_pdf_page"],
        "exercise":e["activity_title"],
        "printed_exercise_sp_codes":e["workbook_printed_sp_codes"],
        "printed_sp_matches_pdp":is_direct_sp_match(e),
        "assignment_status":("PRINTED_SP_MATCH__TEACHER_APPROVAL_PENDING" if is_direct_sp_match(e)
                             else "RELATED_ONLY__DO_NOT_ASSIGN_AS_SP_PBD"),
        "pdp_code":pdp_code,
        "sp":sp,
        "curriculum_review_status":"PRINTED_PAGE_CONTENT_VISUALLY_REVIEWED__TEACHER_APPROVAL_PENDING",
        "content_review_status":e["page_content_review"],
        "teacher_usage_guidance":e["lesson_guidance"],
        "teacher_academic_approved":False,
        "ready_for_runtime":False,
    }
