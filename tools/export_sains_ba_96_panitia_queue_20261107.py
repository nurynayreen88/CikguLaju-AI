"""Prepare an immutable-source, human signoff queue for Science Y2/Y3 BA RPH.

Read-only staging; neither CSV cell nor CI result can promote to READY.
Teacher/panitia decisions must be recorded against each actual PdP and
book version outside this script, followed by an explicit reviewed import.
"""
from __future__ import annotations
import csv
import json

from tools.sains_buku_aktiviti_mapping_20261107 import (
    ROOT,load_activity_books,is_direct_sp_match
)

from tools.render_sains_y2_2_sp_alternative_pbd_20261107 import TASKS as ALT_TASKS,doc_file as alt_doc_file

OUT=ROOT/"build/sains_ba_96_actual_document_qa_20261107"

def review_queue():
    rows=load_activity_books()
    result=[]
    for year in (2,3):
        for item in rows[year].values():
            direct=is_direct_sp_match(item)
            alt=(alt_doc_file(item["sp"]).name if year==2 and item["sp"] in ALT_TASKS else "")
            if (not direct)!=bool(alt):
                raise ValueError("Unmatched workbook SP must have exactly one original PBD alternative")
            result.append({
                "Tahun":year,
                "Kod PdP":item["pdp_code"],
                "Kod SP asal PdP":item["sp"],
                "Kod SP bercetak pada BA":",".join(item["workbook_printed_sp_codes"]),
                "Buku Aktiviti m/s bercetak":item["workbook_printed_page"],
                "Buku Aktiviti halaman PDF":item["workbook_pdf_page"],
                "Tajuk latihan":item["activity_title"],
                "Pautan buku":item["workbook_url"],
                "Sifat padanan":"PADANAN KOD SP (belum akademik)" if direct else "RUJUKAN SAHAJA (SP berbeza)",
                "Bukti yang dilihat pada halaman":item["page_content_evidence"],
                "Cadangan tindakan PdP/PBD":item["lesson_guidance"],
                "Lembaran PBD alternatif CikguLaju (bukan BA rasmi)":alt,
                "Status PBD alternatif":"DRAF — PERLU SEMAK PANITIA" if alt else "TIDAK BERKENAAN",
                "Semak makna SP penuh":"BELUM",
                "Semak kualiti latihan vs objektif":"BELUM",
                "Semak bukti PBD individu":"BELUM",
                "Semak keselamatan aktiviti":"BELUM",
                "Semak muka surat Buku Teks":"BELUM",
                "Semak susun atur Word/PDF":"QA TEKNIKAL SAHAJA",
                "Nama guru/panitia penyemak":"",
                "Tarikh semakan":"",
                "Keputusan panitia":"HOLD — BELUM DILULUSKAN",
                "Skor kualiti akademik per PdP":"",
            })
    if len(result)!=96 or sum(r["Sifat padanan"].startswith("PADANAN") for r in result)!=94:
        raise RuntimeError("Teacher approval queue source count wrong")
    return result

def main():
    rows=review_queue()
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"SENARAI_SEMAKAN_PANITIA_SAINS_BA_T2_T3_96_HOLD.csv"
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]))
        wr.writeheader();wr.writerows(rows)
    summary={
        "pdp_count":96,
        "content_guidance_covered":96,
        "matching_printed_sp":94,
        "related_only":2,
        "original_sp_specific_alternative_pbd_sheets":2,
        "academic_signed_off":0,
        "reviewed_by_teacher":False,
        "status":"HOLD",
        "no_db_or_live_runtime_write":True,
        "csv_file":path.name,
    }
    (OUT/"SENARAI_PANITIA_96_HOLD.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PANITIA_BA_96: source-matched human review checklist exported, "
          "96 pending, 0 approved, HOLD")

if __name__=="__main__":
    main()
