"""Strict staging-only mapping of 96 Sains Year2/3 PdP to original activity-book exercises.

The original scanned books (not copied to the repo) are linked to source
school-hosted Drive URLs. Their printed tables of contents were reviewed as
images. An exact exercise-page/title citation is source-grounded; full academic
equivalence to each SP and exercise-page teacher sign-off is still pending.

No DB/Telegram/Web production writes or automatic "ready" promotion.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAPPING=ROOT/"audits/sains_y2_y3_buku_aktiviti_mapping_20261107.json"
PAGE_CONTENT=ROOT/"audits/sains_y2_y3_ba_page_content_safety_review_20261107.json"
REMAINING_PAGE_CONTENT={
    2:ROOT/"audits/sains_y2_43_remaining_page_content_20261107.json",
    3:ROOT/"audits/sains_y3_42_remaining_page_content_20261107.json",
}
EXPECTED={2:51,3:45}
URL_IDS={2:"1j0qoRWHcaAzHVgbb6uua7k_3i2-qVm0v",
         3:"1kVL3PT-VjQiITqmfNXlURQA8gLYvCrI5"}
OFFSETS={2:4,3:5}
PDF_PAGES={2:89,3:98}

def load_activity_books():
    obj=json.loads(MAPPING.read_text(encoding="utf-8"))
    if obj["no_db_update"] is not True or obj["no_approval_or_quality_grade"] is not True:
        raise ValueError("Activity books must be staging HOLD")
    page_reviews=json.loads(PAGE_CONTENT.read_text(encoding="utf-8"))
    if page_reviews.get("status")!="STAGING_HOLD" or page_reviews.get("all_96_individual_academic_approved") is not False:
        raise ValueError("Page-content review cannot be promoted to READY")
    specific=page_reviews["items"]
    if len(specific)!=11 or page_reviews.get("reviewed_exercises")!=11:
        raise ValueError("Expected 11 individually reviewed exercise pages")
    for year,expected_count in ((2,43),(3,42)):
        extra=json.loads(REMAINING_PAGE_CONTENT[year].read_text(encoding="utf-8"))
        if (extra.get("year")!=year or extra.get("status")!="STAGING_HOLD"
            or extra.get("academic_approval") is not False
            or len(extra.get("items",[]))!=expected_count):
            raise ValueError(f"Unapproved/incomplete Year{year} page audit")
        expected_url=f"https://drive.google.com/file/d/{URL_IDS[year]}/view"
        if extra.get("source")!=expected_url:
            raise ValueError(f"Workbook source mismatch Year{year}")
        specific.extend(extra["items"])
    if len(specific)!=96:
        raise ValueError("Must have 96 individually checked workbook pages")
    by_specific={}
    for rec in specific:
        key=(rec["year"],rec["sp"])
        if key in by_specific or rec.get("type") not in (
            "SAFE_SUBSTITUTE","RELATED_ONLY_ORIGINAL_PBD",
            "DIRECT_WORKBOOK_CONTEXT","DIRECT_WORKBOOK_SAFETY",
            "DIRECT_EXERCISE_CONTENT_REVIEW"):
            raise ValueError("Duplicate or unrecognized exercise review")
        if not rec.get("guidance") or not rec.get("evidence"):
            raise ValueError("Missing exercise source or safe usage")
        if rec["type"]=="DIRECT_EXERCISE_CONTENT_REVIEW":
            if (rec.get("teacher_academic_approved") is not False
                or rec.get("source_check")!="SCANNED_PAGE_TEXT_AND_IMAGES_VISUALLY_INSPECTED"):
                raise ValueError("Unverified page-content review")
        by_specific[key]=rec
    results={}
    for year,count in EXPECTED.items():
        records=obj["items"][str(year)]
        source=obj["sources"][str(year)]
        if len(records)!=count or source["pdf_pages"]!=PDF_PAGES[year] or source["printed_page_to_pdf_offset"]!=OFFSETS[year]:
            raise ValueError("Activity book source count/pages changed")
        expected_url=f"https://drive.google.com/file/d/{URL_IDS[year]}/view"
        if source["url"]!=expected_url:
            raise ValueError("Unexpected workbook source URL")
        found={}
        sp_set=set()
        for i,entry in enumerate(records,1):
            code=f"SCI-Y{year}-PDP-{i:03d}"
            sp=entry["sp"]
            if entry["pdp_code"]!=code or entry["year"]!=year:
                raise ValueError("Workbook PdP identity changed at "+code)
            if not re.fullmatch(r"\d+\.\d+\.\d+",sp) or sp in sp_set:
                raise ValueError("Duplicate/nonstandard workbook SP "+str(sp))
            if entry["workbook_pdf_page"]!=entry["workbook_printed_page"]+OFFSETS[year]:
                raise ValueError("Workbook PDF-to-printed-page offset mismatch "+code)
            if not 1<=entry["workbook_pdf_page"]<=PDF_PAGES[year]:
                raise ValueError("Workbook page is outside original scan")
            if not entry["activity_title"] or entry["source_status"]!="FULL_PRINTED_EXERCISE_PAGE_REVIEWED__TEACHER_SIGNOFF_PENDING":
                raise ValueError("Unverified exercise title "+code)
            sp_codes=entry.get("workbook_printed_sp_codes")
            if not isinstance(sp_codes,list) or not sp_codes:
                raise ValueError("Missing visually checked printed workbook SP: "+code)
            is_direct=sp in sp_codes
            declared=entry.get("matching_status")
            expected=("PRINTED_EXERCISE_SP_CODE_MATCH__ACADEMIC_SIGNOFF_PENDING"
                      if is_direct else "RELATED_DIFFERENT_SP__DO_NOT_ASSIGN_AS_SP_PBD")
            if declared!=expected or entry.get("academic_approval") is not False:
                raise ValueError("Workbook may not declare SP equivalence/approval: "+code)
            if not is_direct and (year,sp) not in {(2,"4.1.7"),(2,"6.1.6")}:
                raise ValueError("Unexpected workbook SP mismatch "+code)
            review=by_specific.get((year,sp))
            if not review:
                raise ValueError("Unreviewed workbook exercise page: "+code)
            if (review["page"]!=entry["workbook_printed_page"]
                or review["exercise"]!=entry["activity_title"]
                or review["year"]!=year or review["sp"]!=sp):
                raise ValueError("Reviewed exercise source/code/page changed: "+code)
            if review.get("pdp_code") and review["pdp_code"]!=code:
                raise ValueError("Review PdP mismatch: "+code)
            if (review["type"]=="RELATED_ONLY_ORIGINAL_PBD")!= (not is_direct):
                raise ValueError("Related-only exercise may not be direct SP/PBD")
            sp_set.add(sp)
            found[code]={**entry,"workbook_url":expected_url,
                         "workbook_title":source["title"],
                         "lesson_guidance":review["guidance"],
                         "page_content_review":review["type"],
                         "page_content_evidence":review["evidence"],
                         "page_content_teacher_signoff":"MISSING"}
        results[year]=found
    if sum(len(x) for x in results.values())!=96:
        raise ValueError("96 workbook exercise review coverage required")
    return results

def activity_for(year,pdp_code,sp):
    """Exact year/pdp/SP needed; no silent fallback to an unrelated exercise."""
    row=load_activity_books().get(year,{}).get(pdp_code)
    if not row or row["sp"]!=sp:
        raise ValueError(f"No academically safe workbook mapping: {year} {pdp_code} {sp}")
    return row

def activity_note(entry,year,*,include_url=False):
    ref=(f"Buku Aktiviti Sains Tahun {year}, aktiviti “{entry['activity_title']}”, "
         f"m/s bercetak {entry['workbook_printed_page']} (PDF halaman {entry['workbook_pdf_page']}).")
    teaching=" Murid boleh melengkapkan latihan selepas guru mengesahkan kesesuaian; guru menyemak respons individu."
    status=" Padanan kandungan latihan dengan SP masih DRAF untuk pengesahan guru."
    if entry["matching_status"].startswith("RELATED_DIFFERENT_SP"):
        teaching=(f" Latihan ini berlabel SP buku {', '.join(entry['workbook_printed_sp_codes'])}, "
                  f"bukan SP PdP {entry['sp']}; **rujukan berkaitan sahaja**, "
                  "JANGAN tetapkan sebagai bukti PBD untuk SP ini.")
    if entry.get("lesson_guidance"):
        teaching+=" "+entry["lesson_guidance"]
    return ref+teaching+status+(f" Sumber buku: {entry['workbook_url']}" if include_url else "")

def is_direct_sp_match(entry):
    return entry["matching_status"]=="PRINTED_EXERCISE_SP_CODE_MATCH__ACADEMIC_SIGNOFF_PENDING"

def activity_short_note(entry,year):
    page=entry["workbook_printed_page"]
    title=entry["activity_title"]
    guidance=entry.get("lesson_guidance")
    if is_direct_sp_match(entry):
        return (f"Buku Aktiviti Sains Tahun {year}, m/s bercetak {page}: '{title}' "
                "(SP sama; DRAF). "+(guidance if guidance else "Guru semak jawapan individu."))
    return (f"Buku Aktiviti Sains Tahun {year}, m/s bercetak {page}: '{title}' "
            f"(SP buku {','.join(entry['workbook_printed_sp_codes'])} "
            f"bukan SP PdP {entry['sp']}); RUJUKAN SAHAJA, bukan tugasan PBD. "
            +(guidance or ""))

if __name__=="__main__":
    rows=load_activity_books()
    print("SAINS_BA_20261107: Year2",len(rows[2]),"Year3",len(rows[3]),
          "exercise links and TOC printed pages; still HOLD")
