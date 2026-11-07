"""Staging-only download-card metadata for Science Year2/3 activity books.

For future Web and Telegram materials dropdowns AFTER curriculum signoff.
A book is one shared PDF per year, not 51/45 fabricated per-PdP PDFs.
Return only verified source links, never silently substitute a year/book or
serve copyrighted binary as app-owned media.
"""
from __future__ import annotations
from tools.sains_buku_aktiviti_mapping_20261107 import activity_for, is_direct_sp_match
from tools.render_sains_y2_2_sp_alternative_pbd_20261107 import TASKS as ORIGINAL_PBD_TASKS, doc_file

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


def proposed_alternative_pbd_material(subject,year,pdp_code,sp):
    """Staging metadata ONLY. No invented LIVE download path or official KPM claim."""
    if str(subject).strip().casefold() not in ("sains","science") or year!=2:
        return None
    task=ORIGINAL_PBD_TASKS.get(str(sp))
    if not task or task["pdp"]!=pdp_code:
        return None
    book=activity_for(2,pdp_code,sp)
    if is_direct_sp_match(book):
        raise ValueError("Original PBD alternative cannot replace a genuine SP-matched BA")
    file=doc_file(sp)
    return {
        "material_type":"PBD_ALTERNATIF_CIKGULAJU",
        "name":f"Pentaksiran Individu Sains Tahun 2 • SP {sp}",
        "pdp_code":pdp_code,
        "sp":sp,
        "word_staging_artifact":file.name,
        "pdf_staging_artifact":file.with_suffix(".pdf").name,
        "official_activity_book":False,
        "relationship_to_book":"ORIGINAL_NOT_KPM_WORKBOOK",
        "book_page_context_only":task["related_page"],
        "book_page_sp_not_equal":task["related_sp"],
        "teacher_academic_approved":False,
        "ready_for_runtime":False,
        "direct_download_url":None
    }
