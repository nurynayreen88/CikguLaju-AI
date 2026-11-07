"""Validate official full Year5 DSKP SP statements in 83 rendered Word/PDF.

A code-only SK/SP label is insufficient. All documents must contain their
actual official text, correct grade-year unit, source book reference, and
the academic DRAF/HOLD warning. No production or database modifications.
"""
from __future__ import annotations
import json
from docx import Document
from pypdf import PdfReader

from tools.render_sains_y5_83_rph_draf_20261107 import OUT,ROOT,get_y5_records
from tools.sains_y5_kssr2017_official_sp_statements_20261107 import checked_statements


def normalize(s):
    return "".join(str(s).casefold().split())


def checked():
    rows=get_y5_records()
    official=checked_statements()
    if len(rows)!=83 or len(official)!=83:
        raise ValueError("Unexpected Year5 source roster size")
    for row in rows:
        code=row["pdp_code"]
        stem=f"SAINS_T5_PDP_{int(row['pdp_number']):03d}_DRAF"
        doc=Document(OUT/(stem+".docx"))
        pdf=PdfReader(str(OUT/(stem+".pdf")))
        if len(pdf.pages)!=1:
            raise ValueError("Year5 PDF not exactly one A4: "+code)
        texts={
            "WORD":"\n".join(c.text for tbl in doc.tables for rr in tbl.rows for c in rr.cells),
            "PDF":pdf.pages[0].extract_text(),
        }
        sp=row["sp"]; official_row=official[sp]
        if row["sk_title"]!=official_row["sk_title"] or row["sp_full_text"]!=official_row["sp_text"]:
            raise ValueError("Year5 official full text changed: "+code)
        for medium,text in texts.items():
            norm=normalize(text)
            required=(
                official_row["sk_title"],official_row["sp_text"],
                sp,"DRAF/HOLD",
                "Aktiviti 1","Aktiviti 2",
            )
            if not all(normalize(x) in norm for x in required):
                missing=[x for x in required if normalize(x) not in norm]
                raise ValueError(f"{code} missing exact official SK/SP in {medium}: {missing}")
    return len(rows)


def main():
    count=checked()
    out=ROOT/"build/sains_y5_official_sp_document_QA_20261107"
    out.mkdir(parents=True,exist_ok=True)
    report={
        "year":5,"subject":"Sains",
        "word_pdf_exact_official_sp_text_count":count,
        "word_pdf_official_sk_topic_count":count,
        "official_sp_statement_source":"Owner DSKP KSSR Semakan 2017 Year5 original",
        "academic_signoff":False,"staging_only":True,
        "production_modified":False,"status":"DOCUMENT_SOURCE_TEXT_QA_PASS__ACADEMIC_HOLD"
    }
    (out/"SAINS_Y5_83_OFFICIAL_TEXT_WORD_PDF_HOLD.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_Y5_OFFICIAL_SP_DOCS: 83/83 Word + PDF full SP text and SK topic; academic HOLD")


if __name__=="__main__":
    main()
