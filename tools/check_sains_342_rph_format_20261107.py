"""Cross-year 342 Science RPH Word/PDF formatting parity gate.

Strictly technical document QA. No DSKP academic grade or LIVE readiness.
In particular, fail if Year3 regresses to a generic 'Aktiviti utama' row
instead of separate bold Aktiviti 1/2 and separate numbered Guru/Murid lines.
"""
from __future__ import annotations
import csv
import json
import re
from pathlib import Path
from docx import Document
from pypdf import PdfReader

from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT,analyze
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import checked_book_pages as year5_book_sp_pages

OUT=ROOT/"build/sains_342_format_consistency_20261107"
ROOTS={
    2:ROOT/"build/sains_y2_51_rph_DRAF_20261107",
    3:ROOT/"build/sains_y3_45_rph_REVIEW_ONLY_20261106",
    4:ROOT/"build/sains_y4_79_rph_DRAF_20261107",
    5:ROOT/"build/sains_y5_83_rph_DRAF_20261107",
    6:ROOT/"build/sains_y6_84_rph_DRAF_20261107",
}
EXPECTED={2:51,3:45,4:79,5:83,6:84}

def validate():
    source,_=analyze()
    if len(source)!=342:
        raise ValueError("Source 342 PdP changed")
    items=[]
    year5_pages=year5_book_sp_pages()
    for year,expected in EXPECTED.items():
        year_rows=[x for x in source if x["tahun"]==year]
        if len(year_rows)!=expected:
            raise ValueError("Wrong source year count "+str(year))
        for row in year_rows:
            n=int(row["pdp_number"])
            code=row["pdp_code"]
            stem=f"SAINS_T{year}_PDP_{n:03d}_DRAF"
            word=ROOTS[year]/(stem+".docx")
            pdf=ROOTS[year]/(stem+".pdf")
            if not word.is_file() or not pdf.is_file():
                raise RuntimeError("Word/PDF missing "+code)
            doc=Document(word)
            if (abs(doc.sections[0].page_width.cm-21)>0.06
                or abs(doc.sections[0].page_height.cm-29.7)>0.06):
                raise ValueError("DOCX is not A4 portrait "+code)
            pdf_obj=PdfReader(str(pdf))
            if len(pdf_obj.pages)!=1:
                raise ValueError("PDF must be one A4 page "+code)
            pg=pdf_obj.pages[0]
            if abs(float(pg.mediabox.width)-595.28)>2 or abs(float(pg.mediabox.height)-841.89)>2:
                raise ValueError("Non A4 PDF "+code)
            page_text=pg.extract_text()
            if row["sp"] not in page_text:
                raise ValueError("PDF SP vanished "+code)
            if "Aktiviti 1" not in page_text or "Aktiviti 2" not in page_text:
                raise ValueError("PDF lost two activity phases "+code)
            if not doc.tables:
                raise ValueError("No RPH structured Word table "+code)
            cells=[cell for table in doc.tables for tr in table.rows for cell in tr.cells]
            word_text="\n".join(c.text for c in cells)
            if row["sp"] not in word_text:
                raise ValueError("Word SP vanished "+code)
            if year==5:
                ref=year5_pages.get(row["sp"])
                if not ref or ref["teacher_academic_approved"] is not False:
                    raise ValueError("Year5 exact code/page source invalid "+code)
                expected_ref=f"BT m/s {ref['primary_page']}"
                if expected_ref not in word_text or expected_ref not in page_text:
                    raise ValueError("Year5 original book printed SP page reference missing "+code)
                if "panitia" not in word_text.lower() or "panitia" not in page_text.lower():
                    raise ValueError("Year5 source code/page falsely treated as teacher approval "+code)
            if year==2 and row["sp"] in ("3.1.3","10.1.6"):
                signal="3.1.4-3.1.6" if row["sp"]=="3.1.3" else "campuran"
                for kind,body in (("Word",word_text),("PDF",page_text)):
                    if signal not in body:
                        raise ValueError("Official Year2 source discrepancy hidden from "+kind+" "+code)
                if row["sp"]=="10.1.6" and "BUKAN petikan SP rasmi" not in page_text:
                    raise ValueError("Official Year2 campuran anomaly misleading in rendered RPH")
            for marker in ("Aktiviti 1","Aktiviti 2"):
                heads=[]
                for cell in cells:
                    for p in cell.paragraphs:
                        if p.text.strip().startswith(marker):
                            heads.append((p.text,p.runs))
                if not heads:
                    raise ValueError("Missing Word main phase "+marker+" "+code)
                if not any(any(run.bold and marker in run.text for run in runs)
                           for _,runs in heads):
                    raise ValueError("Phase label is not bold "+marker+" "+code)
            if year==3:
                phase_table=doc.tables[2]
                left=[tr.cells[0].text for tr in phase_table.rows]
                if ("Aktiviti 1" not in left or "Aktiviti 2" not in left
                    or "Aktiviti utama" in left):
                    raise ValueError("Year3 generic activity row persisted "+code)
                for label in ("Aktiviti 1","Aktiviti 2"):
                    i=left.index(label)
                    cell=phase_table.rows[i].cells[1]
                    lines=[p.text for p in cell.paragraphs]
                    if (len(lines)<3 or not lines[0].startswith(label)
                        or not any(x.startswith("1. Guru ") for x in lines)
                        or not any(x.startswith("2. Murid ") for x in lines)):
                        raise ValueError("Year3 number lines merged or missing "+code)
            else:
                if not re.search(r"1\.\s*Guru ",word_text):
                    raise ValueError("Missing numbered Guru instruction "+code)
                if not re.search(r"2\.\s*Murid ",word_text):
                    raise ValueError("Missing numbered Murid instruction "+code)
            items.append({
                "pdp_code":code,"year":year,"sp":row["sp"],
                "word_a4":True,"pdf_a4_one_page":True,
                "both_activity_headers_bold":True,
                "separate_teacher_pupil_instructions":True,
                "academic_approval":"HOLD",
            })
    if len(items)!=342 or {int(k):sum(r["year"]==int(k) for r in items) for k in EXPECTED}!=EXPECTED:
        raise RuntimeError("342 RPH cross-year coverage wrong")
    return items

def main():
    records=validate()
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/"SAINS_342_RPH_FORMAT_QA_HOLD.csv").open("w",newline="",encoding="utf-8-sig") as f:
        wr=csv.DictWriter(f,fieldnames=list(records[0]))
        wr.writeheader();wr.writerows(records)
    summary={
        "year_counts":{str(y):n for y,n in EXPECTED.items()},
        "document_pairs_checked":342,
        "both_main_activities_bold_and_numbered":342,
        "year3_activity_1_2_rows_separate":45,
        "year5_original_83_sp_code_page_refs_in_real_word_pdf":83,
        "word_page_count_verified_separately_by_LibreOffice":342,
        "pdf_pages_each":1,"academic_approved":0,
        "status":"STAGING_TECHNICAL_PASS_ACADEMIC_HOLD",
        "no_database_or_production_mutation":True,
    }
    (OUT/"SAINS_342_FORMAT_QA_HOLD.json").write_text(
         json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_342_LAYOUT: 342 paired Word/PDF A4, Aktiviti 1/2 bold + numbered; Year3 45 separated; academic HOLD")

if __name__=="__main__":
    main()
