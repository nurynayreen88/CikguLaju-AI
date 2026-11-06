"""Verify 45 Sains Y3 draft DOCX render on exactly one A4 page.

Runs only on CI-produced draft documents, converting to temporary PDF via
headless LibreOffice. This is a layout QA, NOT a proof of academic approval or
permission to publish to Telegram/Web.
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"build/sains_y3_45_rph_REVIEW_ONLY_20261106"
DEST=ROOT/"build/sains_y3_word_page_count_QA"

def main():
    exe=shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:
        raise RuntimeError("LibreOffice required to verify actual Word pagination")
    docs=sorted(SOURCE.glob("SAINS_T3_PDP_*_DRAF.docx"))
    if len(docs)!=45:
        raise RuntimeError(f"Expected 45 Word documents, got {len(docs)}")
    DEST.mkdir(parents=True,exist_ok=True)
    command=[
        exe, "-env:UserInstallation=file:///tmp/cikgulaju_sains_y3_word_qa",
        "--headless","--convert-to","pdf","--outdir",str(DEST),
        *[str(p) for p in docs],
    ]
    res=subprocess.run(command,check=False,text=True,capture_output=True,timeout=240)
    if res.returncode!=0:
        raise RuntimeError("LibreOffice conversion failed: "+res.stderr[-1000:])
    over=[]
    for doc in docs:
        output=DEST/(doc.stem+".pdf")
        if not output.is_file():raise RuntimeError("Word conversion missing "+doc.name)
        pdf=PdfReader(str(output))
        pages=len(pdf.pages)
        if pages!=1:
            over.append((doc.name,pages))
        box=pdf.pages[0].mediabox
        if abs(float(box.width)-595.28)>2 or abs(float(box.height)-841.89)>2:
            raise RuntimeError("Word print is non-A4: "+doc.name)
        source_txt=pdf.pages[0].extract_text()
        if "AKTIVITI" not in source_txt.upper() or "Sains" not in source_txt:
            raise RuntimeError("Word export lost activity text: "+doc.name)
    print("WORD_PAGINATION_QA 45 A4 pages checked, failures",over)
    if over:
        raise RuntimeError(f"{len(over)} Word docs spill to multiple A4 pages")
    print("WORD_ONE_PAGE_A4 45/45 PASS (CI LibreOffice review only, NOT approved)")

if __name__=="__main__":main()
