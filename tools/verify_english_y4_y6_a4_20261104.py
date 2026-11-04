"""Offline A4 Word-to-PDF QA of Year4 fixed 149 and Year6 teacher-choice 14.

Uses AST-parity locked native Word builder. Year4 is measured both before
and after optional text-preserving compaction; Year6 already uses its
production Word compaction. This is NOT the native Telegram PDF pipeline.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from docx import Document
from docx.shared import Cm, Pt
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from tools.audit_english_rph_word_a4_layout import validate_word_function_snapshot
from qa.english_word_builder_snapshot import _create_rph_word
from web.english_y4_standalone_runtime import adapt_rows as y4_fixed
from web.english_y4_pending_draft_preview_runtime import PENDING as Y4_NOT_FIXED
from web.english_y6_standalone_runtime import adapt_rows as y6
from web.english_y6_standalone_runtime import Y6_TEACHER_CHOICES
from web.english_y6_word_a4_runtime import compact_word_file

TARGET=ROOT/"output"/"english_y4_y6_word_a4_20261104"


def _text(path):
    doc=Document(str(path))
    content=[p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                content += [p.text for p in cell.paragraphs]
    return "\n".join(content)


def _base(year):
    return {
        "MATA PELAJARAN":"English", "TAHUN/TINGKATAN":"Year %d"%year,
        "TARIKH":"04/11/2026", "HARI":"Wednesday", "MASA":"08:00 - 09:00",
        "KELAS":"%d Amanah"%year,"BILANGAN MURID":"30",
        "TAJUK":"LEGACY GENERIC TOPIC","MAIN CONTENT STANDARD":"LEGACY",
        "MAIN LEARNING STANDARD":"LEGACY","COMPLEMENTARY CONTENT STANDARD":"LEGACY",
        "COMPLEMENTARY LEARNING STANDARD":"LEGACY",
        "OBJEKTIF PEMBELAJARAN":"LEGACY GENERIC OBJECTIVE",
        "KRITERIA KEJAYAAN":"LEGACY GENERIC SUCCESS",
        "PENGETAHUAN SEDIA ADA":"Familiar topic words",
        "BAHAN BANTU MENGAJAR":"LEGACY GENERIC MATERIALS",
        "EMK / NILAI":"Communication", "KBAT / PAK21":"Evidence-based tasks",
        "PENTAKSIRAN":"LEGACY GENERIC ASSESSMENT",
        "SET INDUKSI":"LEGACY GENERIC INDUCTION",
        "AKTIVITI UTAMA":"LEGACY GENERIC ACTIVITIES",
        "PENUTUP":"LEGACY GENERIC CLOSURE",
        "PEMULIHAN / PENGAYAAN":"Support and extend by task evidence",
        "REFLEKSI":"___/___ pupils achieved; ___/___ need help",
    }


def _build(year, number, docx):
    state={"task":"rph","subject":"English","year":"Year %d"%year,"lesson_no":number}
    base=_base(year)
    rph=y4_fixed(state,base) if year==4 else y6(state,base)
    if rph is base:
        raise RuntimeError("No Year%d L%d source renderer" %(year,number))
    if "LEGACY" in (rph.get("TAJUK","") + rph.get("OBJEKTIF PEMBELAJARAN","")
                     + rph.get("PENTAKSIRAN","")):
        raise RuntimeError("Legacy text in Year%d L%d"%(year,number))
    if year==6 and "DRAF" not in rph.get("TAJUK",""):
        raise RuntimeError("Year6 choice document lacks DRAF marking")
    doc=Document()
    sec=doc.sections[0]
    sec.top_margin=Cm(1.35);sec.bottom_margin=Cm(1.4)
    sec.left_margin=Cm(1.55);sec.right_margin=Cm(1.55)
    doc.styles["Normal"].font.name="Arial"
    doc.styles["Normal"].font.size=Pt(10.5)
    _create_rph_word(doc,sec,state,rph,str(docx))
    before=_text(docx)
    return before


def _convert(files,outdir,profile):
    outdir.mkdir(parents=True,exist_ok=True)
    for i in range(0,len(files),25):
        cmd=["libreoffice","-env:UserInstallation=file://"+str(profile),
             "--headless","--convert-to","pdf","--outdir",str(outdir),
             *[str(p) for p in files[i:i+25]]]
        res=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
        if res.returncode:
            raise RuntimeError("LibreOffice conversion failed: "+res.stderr[-500:])


def _measure(doc,pdf,year):
    p=PdfReader(str(pdf)).pages
    extracted="\n".join(page.extract_text() or "" for page in p)
    return {
        "pages":len(p),
        "a4":all(abs(float(x.mediabox.width)-595.28)<1.5 and
                  abs(float(x.mediabox.height)-841.89)<1.5 for x in p),
        "source_text":len(_text(doc)),
        "pdf_text":len(extracted),
        "draft_label":("DRAF" in extracted) if year==6 else True,
    }


def run(year):
    validate_word_function_snapshot()
    nums=sorted(set(range(1,161))-Y4_NOT_FIXED if year==4 else Y6_TEACHER_CHOICES)
    folder=TARGET/("year%d"%year)
    raw=folder/"raw"
    compact=folder/"compact"
    raw.mkdir(parents=True,exist_ok=True)
    compact.mkdir(parents=True,exist_ok=True)
    records=[]
    raw_files=[]
    compact_files=[]
    for number in nums:
        name="Y%d_L%03d_RPH.docx"%(year,number)
        f=raw/name
        original_text=_build(year,number,f)
        compact_file=compact/name
        compact_file.write_bytes(f.read_bytes())
        if not compact_word_file(str(compact_file)):
            raise RuntimeError("A4 compactor failed Year%d L%d"%(year,number))
        if _text(compact_file)!=original_text:
            raise RuntimeError("Compactor changed lesson text Year%d L%d"%(year,number))
        raw_files.append(f)
        compact_files.append(compact_file)
        records.append({"year":year,"lesson":number})
    _convert(raw_files,folder/"pdf_raw",folder/"lo-profile")
    _convert(compact_files,folder/"pdf_compact",folder/"lo-profile")
    for entry,r,c in zip(records,raw_files,compact_files):
        entry["raw"]=_measure(r,folder/"pdf_raw"/r.name.replace(".docx",".pdf"),year)
        entry["compact"]=_measure(c,folder/"pdf_compact"/c.name.replace(".docx",".pdf"),year)
        if entry["compact"]["source_text"] != entry["raw"]["source_text"]:
            raise RuntimeError("Text changed in compressed Word")
    raw_one=sum(x["raw"]["pages"]==1 and x["raw"]["a4"] for x in records)
    compact_one=sum(x["compact"]["pages"]==1 and x["compact"]["a4"]
                    and x["compact"]["draft_label"] for x in records)
    report={"year":year,"lesson_total":len(nums),"raw_one_page_a4":raw_one,
            "compact_one_page_a4":compact_one,
            "raw_overflows":[x["lesson"] for x in records if x["raw"]["pages"]>1],
            "compact_overflows":[x["lesson"] for x in records if x["compact"]["pages"]>1],
            "scope":"Local Word builder + LibreOffice conversion, NOT native Telegram PDF or real-user download.",
            "lessons":records}
    (folder/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ENGLISH_Y%d_A4 raw=%d/%d compact=%d/%d" %
          (year,raw_one,len(nums),compact_one,len(nums)),flush=True)
    print("RAW_OVERFLOW",report["raw_overflows"],flush=True)
    print("COMPACT_OVERFLOW",report["compact_overflows"],flush=True)
    if compact_one != len(nums):
        raise SystemExit("Even compact Word does not reach A4 for all selected lessons")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--year",required=True,type=int,choices=(4,6))
    run(parser.parse_args().year)
