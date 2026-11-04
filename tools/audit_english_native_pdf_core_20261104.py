"""Offline executable native ReportLab RPH PDF *core* audit.

Extracts the real RPH PDF-generator function from app.py by AST, instead of
imitating its tables. Executes its native PDF path in an isolated namespace
with benign display helpers and *pre-rendered lesson rows*. Does NOT import
Flask, user DB, Telegram, or run quota/payment code. The real live wrapper
also changes PDF footer globally, so this is NOT full production end-to-end.

Do not mark FINAL READY from this test. Records exact A4 page counts and
missing text fields for a selected cross-year test matrix.
"""
import ast
import argparse
import json
from functools import lru_cache
import os
from pathlib import Path
import re
import sys
import tempfile
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.audit_english_2_6_release_status_20261104 import _render

CASES={
    2:(1,30,93,160),
    3:(1,30,93,160),
    4:(1,2,16,30,80,130,160),
    5:(1,16,34,88,141,160),
    6:(1,16,32,80,155,156,157,158,160),
}


@lru_cache(maxsize=1)
def _real_rph_pdf_function():
    path=ROOT/"app.py"
    source=path.read_text(encoding="utf-8")
    tree=ast.parse(source,filename=str(path))
    matches=[]
    for node in tree.body:
        if not isinstance(node,ast.FunctionDef) or node.name!="create_pdf_file":
            continue
        block=ast.get_source_segment(source,node) or ""
        if "info_labels=" in block and "SimpleDocTemplate(" in block and "pdf.build(story" in block:
            matches.append(node)
    if len(matches)!=1:
        raise RuntimeError("Expected exactly one production native PDF table generator, got %d" % len(matches))
    node=matches[0]
    # Never evaluate untrusted app-level startup statements.
    isolated=ast.Module(body=[node],type_ignores=[])
    ast.fix_missing_locations(isolated)
    return compile(isolated,str(path),"exec"),node.lineno


def _make_native_pdf(rows,year,lesson,output):
    state={"task":"rph","subject":"English","year":"Year %d"%year,
           "lesson_no":lesson,"topic":"L%03d"%lesson}

    def safe_filename(v):
        return re.sub(r"[^A-Za-z0-9_-]+","_",str(v or ""))[:60]
    def is_english(s):
        return re.sub(r"[^a-z]","",str(s.get("subject") or "").casefold()) in ("english","bi","bahasainggeris")
    def display_label(s,k):
        return k.title().replace(" / "," / ")
    def display_value(s,k,v):
        return str(v or "").replace("Tahun ","Year ") if k=="TAHUN/TINGKATAN" else str(v or "")
    def phase_time(phase,value):
        value=str(value or "")
        lines=value.split("\n")
        if lines and re.fullmatch(r"\(?\d+\s*(?:minutes?|mins?|minit)\)?",lines[0].strip(),re.I):
            return phase+" ("+lines[0].strip()+")","\n".join(lines[1:])
        return phase,value
    def markup(value):
        return xml_escape(str(value)).replace("\n","<br/>")
    def noop(*args,**kwargs):
        return None
    names={
        "os":os,"tempfile":tempfile,"re":re,"colors":colors,
        "getSampleStyleSheet":getSampleStyleSheet,
        "ParagraphStyle":ParagraphStyle,"TA_CENTER":TA_CENTER,"TA_LEFT":TA_LEFT,
        "SimpleDocTemplate":SimpleDocTemplate,"A4":A4,"mm":mm,
        "Paragraph":Paragraph,"Spacer":Spacer,"Table":Table,"TableStyle":TableStyle,
        "escape":xml_escape,"safe_filename":safe_filename,
        "_is_english_subject":is_english,
        "_rph_rows":lambda s,t:rows,
        "_rph_display_label":display_label,"_rph_display_value":display_value,
        "_rph_title":lambda s:"DAILY LESSON PLAN",
        "_rph_attendance_value":lambda v:str(v or ""),
        "_rph_blank_or_value":lambda v:str(v).strip() if v else "____________",
        "_rph_phase_time_v25179":phase_time,
        "_rph_activity_heading_markup_v25184":markup,
        "_pi_primary_v25210":lambda s:False,
        "_pdf_header_footer_en":noop,"_pdf_header_footer":noop,
    }
    for name in ("_worksheet_v2326_launch_guard","_worksheet_v2327_presentation_guard",
                 "_worksheet_visual_gate_v2328","_worksheet_master_design_guard_v2323",
                 "_worksheet_master_hf_guard_v2375","_worksheet_textbook_claim_guard_v2319",
                 "_worksheet_provenance_guard_v2318","_worksheet_production_guard_v2317",
                 "_tahap1_design_guard_v2314"):
        names[name]=noop
    code,line=_real_rph_pdf_function()
    exec(code,names)
    # Production function creates a safe temp PDF filename from cid; record
    # its resulting path, then move only this isolated fixture to output.
    path=names["create_pdf_file"](state,"",int(lesson)+year*1000)
    dest=Path(output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    os.replace(path,dest)
    return line


def run(year, *, all_lessons=False):
    if year not in CASES:
        raise ValueError("English Year 2–6 only")
    sow=json.loads((ROOT/"audits/english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
    outdir=ROOT/"output"/"english_native_pdf_core_audit_20261104"/("year%d"%year)
    outdir.mkdir(parents=True,exist_ok=True)
    results=[]
    lesson_numbers=tuple(range(1,161)) if all_lessons else CASES[year]
    for lesson in lesson_numbers:
        record=sow["%d/%d"%(year,lesson)]
        rows,_=_render(year,lesson,record)
        if "LEGACY" in str(rows.get("TAJUK") or ""):
            raise RuntimeError("Legacy title in Year%d Lesson%d"%(year,lesson))
        output=outdir/("Y%d_L%03d_native_core.pdf"%(year,lesson))
        row={"year":year,"lesson":lesson}
        try:
            row["function_line"]=_make_native_pdf(rows,year,lesson,output)
            pdf=PdfReader(str(output))
            row["pages"]=len(pdf.pages)
            row["a4"]=all(abs(float(p.mediabox.width)-595.28)<2 and
                          abs(float(p.mediabox.height)-841.89)<2 for p in pdf.pages)
            extracted="\n".join(p.extract_text() or "" for p in pdf.pages)
            row["text_characters"]=len(extracted)
            row["sow_main_in_pdf"]=(
                "not fixed by SOW" in extracted if record["teacher_selected"] else
                str(record["main_ls"]) in extracted)
            row["draft_label_in_pdf"]=(
                "DRAF" in extracted if record["teacher_selected"] or
                   year==4 and lesson==30 or year==5 else None)
            row["error"]=None
        except Exception as exc:
            row["error"]=repr(exc)
            row["pages"]=None
        results.append(row)
        print("NATIVE_PDF_CORE",year,lesson,row["pages"],
              row["error"] or "",flush=True)
    report={
        "audit":"native-reportlab-rph-table-ast-execution",
        "scope":"Native app.py ReportLab RPH core compiled from exact AST, with isolated display-helper stubs. Not real Telegram PDF delivery or full runtime.",
        "year":year,"cases":len(results),
        "single_page_a4":sum(r["pages"]==1 and r.get("a4") for r in results),
        "layout_errors":[r for r in results if r["error"]],
        "multi_page":[r["lesson"] for r in results if r["pages"] and r["pages"]>1],
        "lessons":results}
    (outdir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("NATIVE_PDF_REPORT",json.dumps({k:v for k,v in report.items() if k not in ("lessons","layout_errors")}),flush=True)
    if report["layout_errors"]:
        raise SystemExit("Native PDF ReportLab core threw layout errors; see report.json")
    if any(r["pages"] is None or not r["a4"] or not r["sow_main_in_pdf"] for r in results):
        raise SystemExit("Native PDF core missing standards, pages or A4")
    # Preserve multi-page results as honest QA evidence; do not conflate
    # a successful PDF build with 1-page A4 FINAL READY.


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--year",type=int,required=True,choices=range(2,7))
    p.add_argument("--all",action="store_true",help="Audit every Lesson 1–160")
    args=p.parse_args()
    run(args.year,all_lessons=args.all)
