"""Guard 83 Year5 Science source textbook SP/page code matches across 3 PDFs.

This is a versioned evidence ledger derived from original book PDF texts.
CI intentionally does NOT redistribute the copyrighted books or claim
that a printed SP code establishes full pedagogical PBD suitability.
"""
from __future__ import annotations
import json
from pathlib import Path

from web.sains_y5_83_activity_bank_draf_20261107 import BANK

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/sains_y5_83_full_textbook_printed_sp_pages_20261107.json"
SHA=(
    "322b8ea0e19fc5b6da1c41ff64a25d22e470917027d9b293c85efc045a6be3e2",
    "7469fdadc20cfb275256e5d760f86b36f859cc259f31610865052d752acf820e",
    "629a17b3b493e121285cba65e0925023c71cefadd5c3a740f6e6b82b63ce3d9d",
)
RANGES=((1,35,43),(36,130,95),(131,234,104))

def source_part_for_printed_page(n: int):
    for i,(lo,hi,pdf_count) in enumerate(RANGES):
        if lo<=n<=hi:
            return i+1, (n+7 if i==0 else n-lo)
    raise ValueError(f"Invalid Year5 printed textbook page {n}")

def checked_book_pages():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    if (data.get("source_year")!=5 or data.get("source_pdp_count")!=83
        or data.get("edition_isbn")!="978-983-49-2831-5"
        or data.get("all_printed_pages_sequence_complete") is not True
        or data.get("print_page_count")!=234
        or data.get("status")!="ALL_83_SP_PRINTED_PAGE_TEXT_MATCH__ACADEMIC_HOLD"
        or data.get("no_live_system_modification") is not True
        or data.get("no_db_writes") is not True
        or data.get("no_official_textbook_pdf_redistribution") is not True):
        raise ValueError("Year5 full 3-part textbook audit source/status unknown")
    parts=data["source_parts"]
    if len(parts)!=3:raise ValueError("Expected precisely 3 original book PDF parts")
    for i,(part,sha,(lo,hi,count)) in enumerate(zip(parts,SHA,RANGES),1):
        if (part["part"]!=i or part["sha256"]!=sha
            or part["printed_from"]!=lo or part["printed_to"]!=hi
            or part["pdf_page_count"]!=count
            or part["bytes"]<=100000
            or part["url"].split("/file/d/")[-1].split("/")[0]!=part["file_id"]):
            raise ValueError("Original Year5 book part checksum/range changed: "+str(i))
    items=data["items"]
    mapped={x["sp"]:x for x in items}
    if len(mapped)!=83 or len(items)!=83 or set(mapped)!=set(BANK):
        raise ValueError("Year5 83 distinct SP codes changed from approved source roster")
    seen=set()
    for sp,entry in mapped.items():
        pages=entry["printed_pages"]
        if (not pages or pages!=sorted(set(pages))
            or pages[0]!=entry["primary_page"]
            or not all(isinstance(p,int) and 1<=p<=234 for p in pages)
            or entry["page_sp_evidence"]!="ORIGINAL_PDF_TEXT_HAS_EXACT_SP_TOKEN"
            or entry["teacher_academic_approved"] is not False
            or entry["official_sp_semantics_not_approved"] is not True):
            raise ValueError("Invalid book SP/page/safe status: "+sp)
        for page in pages:
            part,index=source_part_for_printed_page(page)
            if not 0<=index<RANGES[part-1][2]:
                raise ValueError("PDF index out of bounds for "+sp)
        seen.update(pages)
    summary=data["summary"]
    if (summary["source_sp_with_at_least_one_pdf_text_code_match"]!=83
        or summary["unique_pages_with_source_sp_tokens"]!=len(seen)
        or len(seen)!=103
        or summary["sampled_page_image_count"]!=16
        or summary["teacher_academic_approval_count"]!=0
        or summary["runtime_e2e_approved"] is not False):
        raise ValueError("Year5 83-SP book evidence or academic HOLD counts inconsistent")
    return mapped

if __name__=="__main__":
    rows=checked_book_pages()
    print("SAINS_YEAR5_83_BOOK_SP: 234/234 printed pages continuous, "
          "83/83 primary SP labels present, 103 unique SP-tagged pages, "
          "16 source page visual samples, 0 approved academically, HOLD")
