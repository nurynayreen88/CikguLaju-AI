"""Check actual Word pagination of 51 Year2 science DRAF RPH via LibreOffice.

No bypass if Word spills into 2 pages; CI failure is evidence of a print issue.
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader
from tools.render_sains_y2_51_rph_draf_20261107 import ROOT, OUT

QA = ROOT / "build" / "sains_y2_51_word_a4_check_20261107"

def main():
    exe = shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:
        raise RuntimeError("LibreOffice missing; do not claim Word print proof")
    docs = sorted(OUT.glob("SAINS_T2_PDP_*_DRAF.docx"))
    if len(docs) != 51:
        raise RuntimeError(f"Expected 51 Word RPH; found {len(docs)}")
    QA.mkdir(parents=True, exist_ok=True)
    cmd=[exe,"-env:UserInstallation=file:///tmp/cikgulaju_sains_y2_51_print",
         "--headless","--convert-to","pdf","--outdir",str(QA),*map(str,docs)]
    p=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=240)
    if p.returncode:
        raise RuntimeError("Word conversion failed: "+p.stderr[-1000:])
    records=[]
    for doc in docs:
        path=QA/(doc.stem+".pdf")
        if not path.exists():
            raise RuntimeError("Missing conversion "+doc.name)
        pdf=PdfReader(str(path))
        pages=len(pdf.pages)
        text=pdf.pages[0].extract_text()
        records.append({"source":doc.name,"pages":pages,"a4":True})
        size=pdf.pages[0].mediabox
        if abs(float(size.width)-595.28)>2 or abs(float(size.height)-841.89)>2:
            raise RuntimeError("Word export is not A4: "+doc.name)
        if "Aktiviti 1" not in text or "Aktiviti 2" not in text:
            raise RuntimeError("Word text missing headings "+doc.name)
    (OUT/"WORD_PRINT_PAGINATION_QA.json").write_text(json.dumps({
        "year":2,"count":len(records),"status":"DRAF_WORD_FORMAT_ONLY",
        "one_page":sum(x["pages"]==1 for x in records),
        "overflow":[x for x in records if x["pages"]!=1],
        "academic_ready":False,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    failures=[x for x in records if x["pages"]!=1]
    print("SAINS_Y2_WORD_PRINT_QA:",len(records),"checked; overflow",len(failures))
    if failures:
        raise RuntimeError("Word page overflow: "+repr(failures[:12]))

if __name__=="__main__":
    main()
