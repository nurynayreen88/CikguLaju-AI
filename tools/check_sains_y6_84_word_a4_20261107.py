"""One-page A4 smoke test for 84 Year6 Sains Word review RPH.

This checks printed output, not the correctness of DSKP/textbook/pedagogy.
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
from pypdf import PdfReader
from tools.render_sains_y6_84_rph_draf_20261107 import OUT, ROOT

DEST=ROOT/"build/sains_y6_84_word_print_QA_20261107"

def main():
    exe=shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:raise RuntimeError("LibreOffice unavailable, pagination unverified")
    docs=sorted(OUT.glob("SAINS_T6_PDP_*_DRAF.docx"))
    if len(docs)!=84:raise RuntimeError(f"Expected 84 drafts, got {len(docs)}")
    DEST.mkdir(parents=True,exist_ok=True)
    command=[
      exe,"-env:UserInstallation=file:///tmp/cikgulaju_science_year6_print",
      "--headless","--convert-to","pdf","--outdir",str(DEST),
      *[str(d) for d in docs],
    ]
    proc=subprocess.run(command,capture_output=True,text=True,timeout=240,check=False)
    if proc.returncode!=0:
        raise RuntimeError("Word printing failed: "+proc.stderr[-1500:])
    failures=[]
    for doc in docs:
        converted=DEST/(doc.stem+".pdf")
        if not converted.exists():
            raise RuntimeError("Word PDF missing "+doc.name)
        pdf=PdfReader(str(converted))
        pages=len(pdf.pages)
        size=pdf.pages[0].mediabox
        if abs(float(size.width)-595.28)>2 or abs(float(size.height)-841.89)>2:
            raise RuntimeError("Non-A4 printed Word "+doc.name)
        text=pdf.pages[0].extract_text()
        if "Aktiviti 1" not in text or "Aktiviti 2" not in text:
            raise RuntimeError("Activities missing in Word PDF "+doc.name)
        if pages!=1:failures.append({"document":doc.name,"pages":pages})
    (OUT/"WORD_PRINT_QA.json").write_text(json.dumps({
       "year":6,"checked":len(docs),"one_page_pass":len(docs)-len(failures),
       "overflow":failures,"status":"DRAF_PRINT_ONLY_NOT_ACADEMIC_READY",
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"SAINS_Y6_PRINT_QA: {len(docs)-len(failures)}/84 Word A4 single-page")
    if failures:
        raise RuntimeError("Year6 Word page overflow: "+repr(failures[:12]))

if __name__=="__main__":
    main()
