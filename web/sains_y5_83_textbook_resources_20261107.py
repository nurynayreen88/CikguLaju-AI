"""Source-linked Year5 Science textbook cards for staging review only.

A single official-textbook edition is split across three external PDF source
links. This module never copies book PDFs, enables live download, or marks
curriculum/teacher approval. It does not modify any database.
"""
from __future__ import annotations

from tools.render_sains_y5_83_rph_draf_20261107 import get_y5_records
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import (
    checked_book_pages, source_part_for_printed_page, SHA,
)

def proposed_textbook_material(subject, year, pdp_code, sp):
    """Return a linked textbook reference, NOT a downloadable app asset."""
    if str(subject).strip().casefold() not in ("sains", "science") or str(year)!="5":
        return None
    records={item["pdp_code"]:item for item in get_y5_records()}
    row=records.get(str(pdp_code))
    if row is None or row["sp"]!=str(sp):
        raise ValueError("Sains Tahun 5 PdP/SP not in staged source roster")
    ledger=checked_book_pages()
    evidence=ledger[row["sp"]]
    part_no,part_index=source_part_for_printed_page(evidence["primary_page"])

    # The checker already verifies exact source SHA-256, printed range and order.
    # Never infer a direct-download Google Drive link from a shared URL.
    from tools.sains_y5_83_textbook_original_sp_pages_20261107 import LEDGER
    import json
    source=json.loads(LEDGER.read_text(encoding="utf-8"))
    parts=source["source_parts"]
    if len(parts)!=3 or any(parts[i]["sha256"]!=SHA[i] for i in range(3)):
        raise ValueError("Year5 source edition or checksum changed")
    pages=[]
    for printed in evidence["printed_pages"]:
        source_part,zero_index=source_part_for_printed_page(printed)
        pages.append({
            "printed_page":printed,
            "source_part":source_part,
            "pdf_page_1_based":zero_index+1,
            "source_url":parts[source_part-1]["url"],
        })

    return {
        "material_type":"BUKU_TEKS",
        "name":f"Buku Teks Sains Tahun 5 — Bahagian {part_no}",
        "subject":"Sains",
        "year":5,
        "pdp_code":row["pdp_code"],
        "sp":row["sp"],
        "textbook_edition":"KSSR Semakan 2017, cetakan 2020",
        "textbook_isbn":"978-983-49-2831-5",
        "primary_printed_page":evidence["primary_page"],
        "primary_pdf_page_1_based":part_index+1,
        "source_url":parts[part_no-1]["url"],
        "source_part":part_no,
        "source_pages":pages,
        "source_parts":[{
            "part":p["part"],
            "printed_from":p["printed_from"],
            "printed_to":p["printed_to"],
            "source_url":p["url"],
            "sha256":p["sha256"],
        } for p in parts],
        "open_external_source":True,
        "download_method":"OPEN_EXTERNAL_DRIVE_SOURCE__NO_APP_COPY",
        "direct_download_url":None,
        "source_code_page_status":"83_83_SP_EXACT_TOKEN_MATCH__CONTENT_REVIEW_PENDING",
        "teacher_academic_approved":False,
        "ready_for_runtime":False,
    }
