"""Export one canonical 83-PdP Year5 KSSR2017 source index for RPT/RPH review.

Does not schedule invented school weeks or mutate the existing 2027 RPT,
v26.00 DB, Telegram or Web runtime. Every source row links to actual staged
RPH Word/PDF, original DSKP SP statement, and 3-part book print page.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from tools.render_sains_y5_83_rph_draf_20261107 import ROOT,OUT,get_y5_records
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import source_part_for_printed_page
from tools.sains_y5_kssr2017_official_sp_statements_20261107 import checked_statements

INDEX_OUT=ROOT/"build/sains_y5_83_rpt_rph_review_20261107"

def source_rows():
    official=checked_statements()
    rows=get_y5_records()
    if len(rows)!=83:
        raise ValueError("83 unique Year5 source lessons expected")
    output=[]
    for item in rows:
        code=item["pdp_code"]
        number=int(item["pdp_number"])
        stem=f"SAINS_T5_PDP_{number:03d}_DRAF"
        if not (OUT/(stem+".docx")).is_file() or not (OUT/(stem+".pdf")).is_file():
            raise ValueError("RPT Year5 source row lacks actual Word/PDF "+code)
        if item["sp_full_text"]!=official[item["sp"]]["sp_text"]:
            raise ValueError("SP content not official source "+code)
        part,pdf_index=source_part_for_printed_page(item["textbook_page_primary"])
        output.append({
            "Kod PdP":code,
            "Tahun":5,
            "PdP asal":number,
            "Unit sumber":item["unit"],
            "Tajuk PdP sumber":item["tajuk"],
            "SK":item["sk"],
            "Pernyataan SK":item["sk_title"],
            "SP":item["sp"],
            "Pernyataan SP rasmi":item["sp_full_text"],
            "Buku Teks halaman bercetak":item["textbook_page_primary"],
            "Buku Teks bahagian":part,
            "Buku Teks halaman PDF":pdf_index+1,
            "Fail Word":stem+".docx",
            "Fail PDF":stem+".pdf",
            "Minggu Kumpulan A":"",
            "Minggu Kumpulan B":"",
            "Tarikh PdP":"",
            "Buku Aktiviti T5":"BELUM DISAHKAN_SUMBER",
            "Kelulusan guru/panitia":"PENDING",
            "Status":"STAGING_SOURCE_VALIDATED__RPT_CALENDAR_AND_PEDAGOGY_HOLD",
        })
    if ([r["PdP asal"] for r in output]!=list(range(1,84))
        or len({r["Kod PdP"] for r in output})!=83
        or set(r["SP"] for r in output)!=set(official)):
        raise ValueError("Year5 RPT/RPH source chronology or SP parity invalid")
    if any(r["Minggu Kumpulan A"] or r["Minggu Kumpulan B"] or r["Tarikh PdP"] for r in output):
        raise ValueError("Do not fabricate calendar allocation")
    return output

def main():
    INDEX_OUT.mkdir(parents=True,exist_ok=True)
    rows=source_rows()
    csv_path=INDEX_OUT/"SAINS_T5_83_RPT_RPH_KSSR2017_NO_DATES.csv"
    with csv_path.open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    summary={
        "year":5,"pdp":83,"official_sp_statement_rows":83,
        "source_rph_word_pdf_pairs":83,"week_allocation_complete":False,
        "no_fabricated_holidays_or_week_dates":True,
        "teacher_academic_approval":False,
        "book_activity_source_approved":False,
        "ready_for_release":False,"status":"STAGING_INDEX_AWAITING_2027_CALENDAR_AND_PBD_REVIEW",
        "production_changed":False,"db_changed":False,
    }
    (INDEX_OUT/"SAINS_T5_83_RPT_RPH_SCOPE_HOLD.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_Y5_RPT_RPH_INDEX: 83 official SP/RPH Word/PDF pairs, original PdP numbering; calendar HOLD")

if __name__=="__main__":
    main()
