#!/usr/bin/env python3
"""Render every Sejarah RPH via a checked snapshot of Telegram's active Word table.

Staging-only, read-only source. This is a stricter layout diagnostic than the
independent Sejarah Word preview; it does not authorize public download.
"""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

from docx import Document
from docx.shared import Cm,Pt
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa.english_word_builder_snapshot import _create_rph_word
from tools.audit_english_rph_word_a4_layout import validate_word_function_snapshot
from web.sejarah_2027_native_layout_adapter import internal_preview_layout
from web.sejarah_2027_word_compact import compact_sejarah_native_word
from web.native_rph_telegram_api import compact_web_word_notes

OUT=ROOT/"output"/"sejarah_native_word_a4_qa"
TEACHER={"class":"","date":"","time":""}  # Editable school/class/date/time blanks for review copy

def get_rows(layout):
    meta={row["label"].upper():row["value"] for row in layout["header"]}
    return {
        **meta,
        "SET INDUKSI":layout["phases"][0]["activity"],
        "AKTIVITI UTAMA":layout["phases"][1]["activity"],
        "PENUTUP":layout["phases"][2]["activity"],
        "PEMULIHAN / PENGAYAAN":layout["footer"][0]["value"],
        "REFLEKSI":layout["footer"][1]["value"],
    }

def run():
    validate_word_function_snapshot()
    word=OUT/"docx";pdf=OUT/"pdf"
    word.mkdir(parents=True,exist_ok=True);pdf.mkdir(parents=True,exist_ok=True)
    records=[]
    for y in (4,5,6):
        for pdp in range(1,37):
            layout=internal_preview_layout(y,pdp,TEACHER)
            rows=get_rows(layout)
            for field in ("STANDARD KANDUNGAN","STANDARD PEMBELAJARAN","OBJEKTIF PEMBELAJARAN","PENTAKSIRAN","AKTIVITI UTAMA"):
                assert rows.get(field),("Missing native row",y,pdp,field)
            doc=Document()
            sec=doc.sections[0]
            sec.left_margin=Cm(1.1);sec.right_margin=Cm(1.1)
            sec.top_margin=Cm(0.75);sec.bottom_margin=Cm(0.75)
            doc.styles["Normal"].font.size=Pt(8.5)
            state={"task":"rph","subject":"Sejarah","year":f"Tahun {y}","lesson_no":pdp}
            name=f"SEJ_T{y}_PDP_{pdp:03d}"
            target=word/(name+".docx")
            _create_rph_word(doc,sec,state,rows,str(target))
            # Reproduce the Web-to-Telegram postprocessing on this same
            # native table document; leave all content intact.
            raw=target.read_bytes()
            native=compact_web_word_notes(raw)
            target.write_bytes(compact_sejarah_native_word(native))
            records.append({"year":y,"pdp":pdp,"name":name,"input_main_chars":len(rows["AKTIVITI UTAMA"])})
    lo=shutil.which("libreoffice") or shutil.which("soffice")
    if not lo:raise RuntimeError("LibreOffice required to measure native Word pagination")
    cmd=[lo,"-env:UserInstallation=file://"+str((OUT/"lo-profile").resolve()),"--headless",
         "--convert-to","pdf","--outdir",str(pdf),
         *[str(word/(x["name"]+".docx")) for x in records]]
    done=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
    if done.returncode:
        raise RuntimeError(done.stdout[-3000:]+"\n"+done.stderr[-3000:])
    failures=[]
    for r in records:
        path=pdf/(r["name"]+".pdf")
        if not path.is_file():
            failures.append({"id":r["name"],"issue":"PDF missing"});continue
        doc=PdfReader(str(path),strict=True)
        r["pages"]=len(doc.pages)
        r["a4"]=all(abs(float(p.mediabox.width)-595.28)<1.5 and abs(float(p.mediabox.height)-841.89)<1.5 for p in doc.pages)
        text="\n".join((p.extract_text() or "") for p in doc.pages)
        r["text_length"]=len(text)
        if r["pages"]!=1 or not r["a4"] or len(text)<350:
            failures.append({"id":r["name"],"pages":r["pages"],"a4":r["a4"],"text_length":len(text)})
    report={"status":"STAGING_TELEGRAM_WORD_SNAPSHOT_LAYOUT_QA_ONLY","total":len(records),"one_a4":sum(r.get("pages")==1 and r.get("a4") for r in records),"failures":failures,"records":records,"ready":False}
    (OUT/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Sejarah native Telegram Word snapshot: {report['one_a4']}/{len(records)} one-page A4, {len(failures)} failures",flush=True)
    for issue in failures[:25]:print(json.dumps(issue),flush=True)
    assert len(records)==108
    assert not failures,"Native Telegram table Word must fit one A4 for every Sejarah PdP"
if __name__=="__main__":run()
