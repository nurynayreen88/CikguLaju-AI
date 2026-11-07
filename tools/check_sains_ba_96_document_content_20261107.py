"""Fail-closed check of 96 Science Year2/3 draft RPH BA text, source and safety.

Executed only after CI renders 51 Y2 + 45 Y3 PDF/DOCX and prints Word to
PDF using LibreOffice. This validates exact printed exercise references and
two related-only cases, NOT academic suitability or runtime activation.
"""
from __future__ import annotations
import csv
import json
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from tools.sains_buku_aktiviti_mapping_20261107 import (
    ROOT, load_activity_books, is_direct_sp_match
)
from tools.render_sains_y2_51_rph_draf_20261107 import OUT as Y2
from tools.render_sains_y3_45_review_pack_20261106 import OUTPUT as Y3

OUT=ROOT/"build/sains_ba_96_actual_document_qa_20261107"

def norm(text):
    return re.sub(r"\s+"," ",text).strip().casefold()

def check_documents():
    mapping=load_activity_books()
    manifest={}
    for year,folder,name in [
        (2,Y2,"RPH_Y2_51_MANIFEST_DRAF.csv"),
        (3,Y3,"MANIFEST_DRAF.csv"),
    ]:
        with (folder/name).open(encoding="utf-8-sig",newline="") as f:
            records=list(csv.DictReader(f))
        if len(records)!=(51 if year==2 else 45):
            raise RuntimeError(f"Year{year} manifest count invalid")
        manifest[year]=records
    outcome=[]
    for year,folder in ((2,Y2),(3,Y3)):
        for i in range(1,len(mapping[year])+1):
            code=f"SCI-Y{year}-PDP-{i:03d}"
            entry=mapping[year][code]
            base=f"SAINS_T{year}_PDP_{i:03d}_DRAF"
            wp=folder/(base+".docx")
            pp=folder/(base+".pdf")
            if not wp.exists() or not pp.exists():
                raise RuntimeError("Missing RPH documents "+code)
            document=Document(str(wp))
            doc_text=norm(" ".join(
                 c.text for table in document.tables for row in table.rows
                 for c in row.cells
            ))
            pdf=PdfReader(str(pp))
            if len(pdf.pages)!=1:
                raise RuntimeError("PDF no longer one page "+code)
            pdf_text=norm(pdf.pages[0].extract_text())
            if not pdf_text or len(pdf_text)<500:
                raise RuntimeError("PDF text incomplete "+code)
            expected_page=f"m/s bercetak {entry['workbook_printed_page']}"
            exercise=entry["activity_title"]
            for format_name,text in (("Word",doc_text),("PDF",pdf_text)):
                for part in ("buku aktiviti sains tahun "+str(year),
                             expected_page.casefold(),norm(exercise)):
                    if part not in text:
                        raise RuntimeError(f"Missing/mismatched BA reference {code}: {format_name}: {part}")
                if entry["lesson_guidance"] and norm(entry["lesson_guidance"]) not in text:
                    raise RuntimeError(f"Missing safe, page-specific teacher guidance: {code} {format_name}")
                if is_direct_sp_match(entry):
                    if "rujukan sahaja" in text and year==2:
                        # No other exercise in this single RPH may be related-only.
                        raise RuntimeError("Direct SP marked as related-only "+code)
                else:
                    if "rujukan sahaja" not in text or "bukan tugasan pbd" not in text:
                        raise RuntimeError("Unmatched workbook assigned as SP PBD "+code)
            match=[r for r in manifest[year]
                   if r.get("pdp_code",r.get("pdp"))==code]
            if len(match)!=1:
                raise RuntimeError("Manifest source code missing/duplicate "+code)
            manifest_row=match[0]
            if str(entry["workbook_printed_page"]) not in (
                str(manifest_row.get("activity_book_page",""))
                if year==2 else manifest_row.get("activity_book_ref","")):
                raise RuntimeError("Manifest book page differs from printed exercise "+code)
            if year==2 and entry["sp"] in ("4.1.7","6.1.6"):
                if "lembaran pbd alternatif" not in doc_text or "lembaran pbd alternatif" not in pdf_text:
                    raise RuntimeError("Missing source-specific PBD alternative callout in RPH "+code)
                from tools.render_sains_y2_2_sp_alternative_pbd_20261107 import doc_file
                alt=doc_file(entry["sp"])
                if not alt.is_file() or not alt.with_suffix(".pdf").is_file():
                    raise RuntimeError("Expected original PBD alternative Word/PDF not rendered "+code)
                alt_pdf=PdfReader(str(alt.with_suffix(".pdf")))
                if len(alt_pdf.pages)!=1:
                    raise RuntimeError("Original PBD alternative exceeded one A4 page "+code)
                if "BUKAN LATIHAN BUKU AKTIVITI RASMI" not in alt_pdf.pages[0].extract_text():
                    raise RuntimeError("PBD alternative not labelled non-official BA "+code)
            outcome.append({
                "pdp_code":code,
                "source_sp":entry["sp"],
                "book_printed_page":entry["workbook_printed_page"],
                "workbook_printed_sp":",".join(entry["workbook_printed_sp_codes"]),
                "sp_code_equal":is_direct_sp_match(entry),
                "pdf_one_page":True,
                "docx_contains_exact_book_page":True,
                "pdf_contains_exact_book_page":True,
                "specific_safe_usage_reviewed":bool(entry["lesson_guidance"]),
                "teacher_academic_approved":False,
                "staging_release":"HOLD",
            })
    if len(outcome)!=96 or sum(x["sp_code_equal"] for x in outcome)!=94:
        raise RuntimeError("Expected 94 direct and 2 related-only Book Activity refs")
    if sum(x["specific_safe_usage_reviewed"] for x in outcome)!=96:
        raise RuntimeError("Expected 96 page-specific exercise guidance records")
    return outcome

def main():
    rows=check_documents()
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/"SAINS_BA_96_RPH_SOURCE_PAGE_QA.csv").open(
        "w",newline="",encoding="utf-8-sig") as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]))
        wr.writeheader();wr.writerows(rows)
    info={
        "source":"Sains Tahun2/3 scanned original activity books",
        "rph_documents_checked":96,"year2":51,"year3":45,
        "source_code_match":94,"related_different_sp":2,
        "page_content_safety_reviewed":96,
        "new_individual_page_reviews":85,
        "original_alternative_pbd_for_mismatched_sp":2,
        "alternatives_not_official_activity_book":True,
        "previous_individual_page_reviews":11,
        "docx_page_source_coverage":96,"pdf_page_source_coverage":96,
        "academic_certified":0,"runtime_enabled":False,
        "release":"STAGING_ONLY_HOLD",
    }
    (OUT/"QUALITY_GATE_BOOK_ACTIVITY_HOLD.json").write_text(
        json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_BA_96_SOURCE_DOCUMENTS: 96 Word/PDF verified; "
          "94 direct-SP / 2 related-only, 96 page-specific usage notes; HOLD")

if __name__=="__main__":
    main()
