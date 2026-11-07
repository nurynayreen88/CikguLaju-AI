"""Source-to-document QA: Year4 79 Science RPH have correct TOC-unit ranges only.

Checks all *generated* Word/PDF artifacts in staging. TOC unit ranges do
NOT prove any exact SP page, textbook pedagogy, curricular correctness,
teacher approval, live runtime integration or >=80% academic quality.
"""
from __future__ import annotations
import csv
import json
from docx import Document
from pypdf import PdfReader

from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT
from tools.render_sains_y4_79_rph_draf_20261107 import (
    OUT, get_y4_records, textbook_unit_toc,
)

def checked():
    source=get_y4_records()
    units=textbook_unit_toc()
    if len(source)!=79 or len(units)!=19:
        raise ValueError("Missing Year4 79 source SP/TOC units")
    outcome=[]
    for r in source:
        code=r["pdp_code"];n=int(r["pdp_number"])
        stem=f"SAINS_T4_PDP_{n:03d}_DRAF"
        word=OUT/(stem+".docx")
        pdf=OUT/(stem+".pdf")
        if not word.exists() or not pdf.exists():
            raise ValueError("Missing Year4 source Word/PDF: "+code)
        doc=Document(word)
        if (abs(doc.sections[0].page_width.cm-21)>0.07
            or abs(doc.sections[0].page_height.cm-29.7)>0.07):
            raise ValueError("Year4 Word not A4 "+code)
        reader=PdfReader(str(pdf))
        if len(reader.pages)!=1:
            raise ValueError("Year4 PDF must remain exactly one page "+code)
        p=reader.pages[0]
        if abs(float(p.mediabox.width)-595.28)>2 or abs(float(p.mediabox.height)-841.89)>2:
            raise ValueError("Year4 PDF non-A4 "+code)
        text=p.extract_text()
        cells="\n".join(c.text for t in doc.tables for row in t.rows for c in row.cells)
        toc=r["textbook_unit_toc_note"]
        start,end=r["textbook_toc_range"]
        token=f"{start}-{end}"
        for label,v in (("Word",cells),("PDF",text)):
            if (toc not in v
                or "ISI KANDUNGAN SAHAJA" not in v
                or "m/s tepat SP belum disahkan" not in v
                or token not in v
                or r["sp"] not in v):
                raise ValueError("Year4 TOC-source caution missing "+label+": "+code)
        if (r["textbook_pages"] is not None
            or r["curriculum_quality_percent"] is not None
            or r["status"]!="DRAF_HOLD"):
            raise ValueError("Year4 false exact SP textbook page or grade "+code)
        outcome.append({
            "pdp_code":code,
            "sp":r["sp"],
            "sk":r["sk"],
            "original_year4_book_toc_unit":r["textbook_toc_unit"],
            "printed_unit_page_range_only":token,
            "real_docx_pdf_page_and_caution":"PASS",
            "exact_sp_page_verified":False,
            "teacher_academic_approved":False,
            "release":"STAGING_HOLD"
        })
    if len(outcome)!=79 or len({r["pdp_code"] for r in outcome})!=79:
        raise ValueError("Year4 source SP/PdP roster is incomplete")
    return outcome

def main():
    outcome=checked()
    out=ROOT/"build/sains_y4_79_textbook_toc_document_QA_20261107"
    out.mkdir(parents=True,exist_ok=True)
    with (out/"SAINS_Y4_79_PDP_UNIT_TOC_HOLD.csv").open(
        "w",newline="",encoding="utf-8-sig") as fp:
        wr=csv.DictWriter(fp,fieldnames=list(outcome[0]))
        wr.writeheader();wr.writerows(outcome)
    summary={
        "year":4,"pdp":79,"toc_range_references_verified_in_real_word_and_pdf":79,
        "exact_sp_printed_page_verified":0,
        "pdf_one_A4_each":79,
        "teacher_approved":0,
        "academic_score_percent":None,
        "source_type":"ORIGINAL_2019_TEXTBOOK_TOC_UNIT_RANGE_ONLY",
        "web_telegram_production_enabled":False,
        "database_changed":False,
        "status":"STAGING_HOLD"
    }
    (out/"SAINS_Y4_79_UNIT_TOC_QA_HOLD.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SAINS_Y4_TOC_QA: 79/79 Word+PDF unit references and explicit NOT exact SP pages; HOLD")

if __name__=="__main__":
    main()
