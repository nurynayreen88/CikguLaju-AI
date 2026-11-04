"""Offline A4 audit for newly exposed 11 Year4 + 151 Year5 English RPH drafts.

Uses AST-matched native Word table function in qa snapshot. LibreOffice PDF
conversion is layout QA only, NOT proof of native Telegram PDF delivery.
No application startup, user database, API, credentials or credit mutations.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from docx import Document
from docx.shared import Cm, Pt
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_english_rph_word_a4_layout import validate_word_function_snapshot
from qa.english_word_builder_snapshot import _create_rph_word
from web.english_y4_pending_draft_preview_runtime import PENDING, adapt_rows as y4
from web.english_y5_fixed_draft_preview_runtime import preview_rows as y5
from web.english_y5_standalone_runtime import CHOICE_LESSONS
from web.english_y6_word_a4_runtime import compact_word_file

OUT = ROOT / "output" / "english_y4_y5_full_draft_a4"


def _get_text(path):
    d = Document(str(path))
    result = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                result.extend(p.text for p in cell.paragraphs)
    return "\n".join(result)


def _build(year, number, file):
    state={"task":"rph","subject":"English","year":"Year %d" % year,
           "lesson_no":number}
    original={
        "MATA PELAJARAN":"English", "TAHUN/TINGKATAN":"Year %d"%year,
        "TARIKH":"04/11/2026", "HARI":"Wednesday", "MASA":"08:00 - 09:00",
        "KELAS":"%d Amanah"%year, "BILANGAN MURID":"30",
        "TAJUK":"Legacy generic title", "MAIN CONTENT STANDARD":"Legacy",
        "MAIN LEARNING STANDARD":"Legacy",
        "COMPLEMENTARY CONTENT STANDARD":"Legacy",
        "COMPLEMENTARY LEARNING STANDARD":"Legacy",
        "OBJEKTIF PEMBELAJARAN":"Old generic objective",
        "KRITERIA KEJAYAAN":"Old generic success",
        "PENGETAHUAN SEDIA ADA":"Familiar vocabulary and unit language",
        "BAHAN BANTU MENGAJAR":"Old generic materials",
        "EMK / NILAI":"Communication and responsibility",
        "KBAT / PAK21":"Pair and group reasoning",
        "PENTAKSIRAN":"Old generic PBD",
        "SET INDUKSI":"Old generic induction",
        "AKTIVITI UTAMA":"Old generic activities",
        "PENUTUP":"Old generic closure",
        "PEMULIHAN / PENGAYAAN":"Support and extension",
        "REFLEKSI":"___/___ met objectives; ___/___ require support",
    }
    rendered = y4(state, original) if year == 4 else y5(state, original)
    if rendered is original:
        raise RuntimeError("No preview overlay: Year %d Lesson %d" % (year,number))
    if "DRAF" not in rendered.get("TAJUK", ""):
        raise RuntimeError("Missing DRAF label: Year %d Lesson %d" % (year,number))
    doc=Document()
    sec=doc.sections[0]
    sec.top_margin=Cm(1.35)
    sec.bottom_margin=Cm(1.4)
    sec.left_margin=Cm(1.55)
    sec.right_margin=Cm(1.55)
    doc.styles["Normal"].font.name="Arial"
    doc.styles["Normal"].font.size=Pt(10.5)
    _create_rph_word(doc, sec, state, rendered, str(file))
    before=_get_text(file)
    if not compact_word_file(file):
        raise RuntimeError("Compactor refused Year %d Lesson %d" % (year,number))
    after=_get_text(file)
    if before != after:
        raise RuntimeError("Text changed during compaction Year %d Lesson %d" % (year,number))
    if any(x in after for x in ("Legacy generic title","Old generic objective",
                               "Old generic activities","Old generic PBD")):
        raise RuntimeError("Legacy data leaked Year %d Lesson %d" % (year,number))
    if "DRAF" not in after:
        raise RuntimeError("DRAF label lost")
    return {
        "year":year, "lesson":number, "docx":file.name,
        "word_characters":len(after),
        "stages":{key:len(rendered.get(key,"")) for key in
                  ("SET INDUKSI","AKTIVITI UTAMA","PENTAKSIRAN","PENUTUP")},
    }


def run(year):
    validate_word_function_snapshot()
    numbers = sorted(PENDING if year == 4 else set(range(1,161))-CHOICE_LESSONS)
    target=OUT/("year%d"%year)
    wd,pd=target/"docx",target/"pdf"
    wd.mkdir(parents=True,exist_ok=True)
    pd.mkdir(parents=True,exist_ok=True)
    records=[]
    files=[]
    for n in numbers:
        f=wd/("Y%d_L%03d_DRAFT.docx"%(year,n))
        record=_build(year,n,f)
        files.append(f)
        records.append(record)
    for start in range(0,len(files),25):
        cmd=["libreoffice","-env:UserInstallation=file://"+str(target/"lo-profile"),
             "--headless","--convert-to","pdf","--outdir",str(pd),
             *[str(p) for p in files[start:start+25]]]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
        if result.returncode:
            raise RuntimeError("PDF conversion failed at offset %d: %s" %
                               (start,result.stderr[-800:]))
    for record in records:
        file=pd/record["docx"].replace(".docx",".pdf")
        if not file.is_file():
            raise RuntimeError("PDF not generated: "+str(file))
        pages=PdfReader(str(file)).pages
        record["pages"]=len(pages)
        record["a4"]=all(abs(float(p.mediabox.width)-595.28)<1.5 and
                         abs(float(p.mediabox.height)-841.89)<1.5 for p in pages)
        extracted="\n".join(p.extract_text() or "" for p in pages)
        record["draft_label_in_pdf"]="DRAF" in extracted
        record["pdf_text_characters"]=len(extracted)
    bad=[r["lesson"] for r in records if r["pages"]!=1 or
         not r["a4"] or not r["draft_label_in_pdf"]]
    report={"year":year,"requested_count":len(numbers),"rendered_count":len(records),
            "one_page_a4":len(records)-len(bad),"non_compliant_lessons":bad,
            "scope":"Offline exact active Word table snapshot + local LibreOffice PDF conversion. Not native Telegram PDF or teacher approval.",
            "lessons":records}
    (target/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print("ENGLISH_DRAFT_A4_Y%d count=%d one_page=%d non_compliant=%s" %
          (year,len(records),len(records)-len(bad),bad),flush=True)
    if bad:
        raise SystemExit("A4 layout verification failed; see per-Lesson report")


if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--year",required=True,type=int,choices=(4,5))
    run(arg.parse_args().year)
