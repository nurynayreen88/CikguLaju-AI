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
EXPECTED={2:51,3:45}
URL_IDS={2:"1j0qoRWHcaAzHVgbb6uua7k_3i2-qVm0v",
         3:"1kVL3PT-VjQiITqmfNXlURQA8gLYvCrI5"}
OFFSETS={2:4,3:5}
PDF_PAGES={2:89,3:98}

def load_activity_books():
    obj=json.loads(MAPPING.read_text(encoding="utf-8"))
    if obj["no_db_update"] is not True or obj["no_approval_or_quality_grade"] is not True:
        raise ValueError("Activity books must be staging HOLD")
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
            if not entry["activity_title"] or entry["source_status"]!="PRINTED_TOC_VISUALLY_CHECKED_EXERCISE_APPROVAL_PENDING":
                raise ValueError("Unverified exercise title "+code)
            sp_set.add(sp)
            found[code]={**entry,"workbook_url":expected_url,"workbook_title":source["title"]}
        results[year]=found
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
    teaching=" Murid melengkapkan latihan berkaitan; guru menyemak respons individu sebagai bukti PBD."
    status=" Padanan kandungan latihan dengan SP masih DRAF untuk pengesahan guru."
    return ref+teaching+status+(f" Sumber buku: {entry['workbook_url']}" if include_url else "")

if __name__=="__main__":
    rows=load_activity_books()
    print("SAINS_BA_20261107: Year2",len(rows[2]),"Year3",len(rows[3]),
          "exercise links and TOC printed pages; still HOLD")
