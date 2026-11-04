"""Read-only native ReportLab PDF RPH smoke test for English Primary 2–6.

Extracts the exact RPH native PDF builder function from active app.py by AST,
never imports app.py (which would start the Telegram runtime/production DB).
Production-only surrounding global helpers are isolated as English-specific
formatting stubs and no-op callbacks. This tests the same native ReportLab
table/pagination *logic* but is NOT a real teacher Telegram delivery or a
bit-for-bit reproduction of the full production helper stack.

Use --pilot for representative lessons, --all for every source Lesson.
"""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
import tempfile
from collections import Counter
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                               TableStyle, Spacer, PageBreak)

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.audit_english_2_6_release_status_20261104 import _render

SOW=json.loads((ROOT/"audits/english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
OUTPUT=ROOT/"output"/"english_2_6_native_pdf_smoke_20261104"
RPH_KEYS=("TAJUK","MAIN CONTENT STANDARD","MAIN LEARNING STANDARD",
          "COMPLEMENTARY CONTENT STANDARD","COMPLEMENTARY LEARNING STANDARD",
          "OBJEKTIF PEMBELAJARAN","AKTIVITI UTAMA","PENTAKSIRAN","PENUTUP")
GUARDS=(
    "_worksheet_v2326_launch_guard","_worksheet_v2327_presentation_guard",
    "_worksheet_visual_gate_v2328","_worksheet_master_design_guard_v2323",
    "_worksheet_master_hf_guard_v2375","_worksheet_textbook_claim_guard_v2319",
    "_worksheet_provenance_guard_v2318","_worksheet_production_guard_v2317",
    "_tahap1_design_guard_v2314",
)


def _is_english_subject(state):
    return str((state or {}).get("subject") or "").strip().casefold() in (
        "bahasa inggeris","english")


def _phase_time(phase, text):
    lines=str(text or "").strip().splitlines()
    if lines:
        match=re.match(r"^\(?\s*(\d+\s*(?:minit|minutes?|mins?))\s*\)?$",lines[0],re.I)
        if match:
            return "%s (%s)"%(phase,match.group(1)),"\n".join(lines[1:])
    return phase,str(text or "").strip()


def _activity_markup(text):
    return escape(str(text or "")).replace("\r\n","\n").replace("\n","<br/>")


def _display_value(state,key,value):
    v=str(value or "")
    if key=="MATA PELAJARAN":
        return "English"
    if key=="TAHUN/TINGKATAN":
        return re.sub(r"^Tahun\s+","Year ",v,flags=re.I)
    return v


def _selected_active_pdf_builder(source_text):
    """Select actual native ReportLab table renderer, not later wrappers."""
    tree=ast.parse(source_text)
    matches=[]
    for node in tree.body:
        if not isinstance(node,ast.FunctionDef) or node.name!="create_pdf_file":
            continue
        snippet=ast.get_source_segment(source_text,node) or ""
        if ("_worksheet_v2326_launch_guard(s)" in snippet and
                "MAIN CONTENT STANDARD" in snippet and
                "COMPLEMENTARY LEARNING STANDARD" in snippet and
                "pdf.build(story" in snippet and
                "return path" in snippet):
            matches.append(node)
    if len(matches)!=1:
        raise RuntimeError("Unable to select unique production native PDF RPH builder")
    return matches[0]


def _load_native_pdf_function():
    source=(ROOT/"app.py").read_text(encoding="utf-8")
    node=_selected_active_pdf_builder(source)
    env={
        "os":__import__("os"),"tempfile":tempfile,"re":re,"escape":escape,
        "getSampleStyleSheet":getSampleStyleSheet,"ParagraphStyle":ParagraphStyle,
        "TA_CENTER":TA_CENTER,"TA_LEFT":TA_LEFT,"SimpleDocTemplate":SimpleDocTemplate,
        "A4":A4,"mm":mm,"colors":colors,
        "Paragraph":Paragraph,"Table":Table,"TableStyle":TableStyle,
        "Spacer":Spacer,"PageBreak":PageBreak,
        "safe_filename":lambda s:re.sub(r"[^A-Za-z0-9]+","_",str(s or "Lesson"))[:45],
        "_is_english_subject":_is_english_subject,
        "_pi_primary_v25210":lambda *_:False,
        "_rph_title":lambda *_:"DAILY LESSON PLAN",
        "_rph_display_label":lambda _s,k:k.replace("_"," ").title(),
        "_rph_display_value":_display_value,
        "_rph_blank_or_value":lambda value: str(value).strip() if str(value or "").strip() else "_"*28,
        "_rph_attendance_value":lambda value: str(value).strip() if str(value or "").strip() else "____",
        "_rph_phase_time_v25179":_phase_time,
        "_rph_activity_heading_markup_v25184":_activity_markup,
        "_pdf_header_footer_en":lambda *_:None,
        "_pdf_header_footer":lambda *_:None,
        # Replaced on each render, preserving the real source-linked rows.
        "_rph_rows":lambda *_:{},
    }
    for name in GUARDS:
        env[name]=lambda *_:None
    module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
    exec(compile(module,str(ROOT/"app.py"),"exec"),env)
    return env


def run(year, all_lessons=False, lessons=None):
    if year not in range(2,7):
        raise ValueError("English primary Year 2–6 only")
    if lessons is not None:
        nums=sorted(set(int(n) for n in lessons))
        if not nums or any(n<1 or n>160 for n in nums):
            raise ValueError("Lesson numbers must be in 1..160")
    else:
        nums=list(range(1,161)) if all_lessons else sorted(set((1,16,30,40,61,74,88,160)))
    results=[]
    env=_load_native_pdf_function()
    target=OUTPUT/f"year{year}"
    target.mkdir(parents=True,exist_ok=True)
    for n in nums:
        state={"task":"rph","subject":"English","year":f"Year {year}",
               "lesson_no":n,"topic":f"English Lesson {n:03d}",
               "assessment_mode":"formative"}
        sow=SOW[f"{year}/{n}"]
        if not sow["teacher_selected"]:
            state["sp_code"]=sow["main_ls"]
            state["comp_sp_code"]=sow["complementary_ls"]
        rows,_=_render(year,n,sow)
        if any(not str(rows.get(k) or "").strip() for k in RPH_KEYS):
            # Do not hide known per-lesson metadata omissions.
            missing=[k for k in RPH_KEYS if not str(rows.get(k) or "").strip()]
            results.append({"lesson":n,"error":"missing row fields "+repr(missing)})
            continue
        env["_rph_rows"]=lambda *_args,source=dict(rows):source
        try:
            path=env["create_pdf_file"](state,"",f"E{year}L{n:03d}")
            pdf_path=Path(path)
            if not pdf_path.is_file():
                raise RuntimeError("native PDF file missing")
            final=target/f"Y{year}_L{n:03d}_native_layout.pdf"
            final.write_bytes(pdf_path.read_bytes())
            pages=PdfReader(str(final)).pages
            content="\n".join(p.extract_text() or "" for p in pages)
            result={"lesson":n,"pages":len(pages),
                    "a4":all(abs(float(p.mediabox.width)-595.28)<1.5
                             and abs(float(p.mediabox.height)-841.89)<1.5 for p in pages),
                    "pdf_bytes":final.stat().st_size,
                    "text_chars":len(content),
                    "has_title":"DAILY LESSON PLAN" in content,
                    "has_lesson_topic":bool(sow["topic"] and
                                           sow["topic"].casefold() in content.casefold())
                        if not sow["teacher_selected"] else "DRAF" in content,
                    "has_pbd":bool(content and "assessment" in content.casefold() or
                                     "pentaksiran" in content.casefold()),
                    "draft_notice_present":("DRAF" in content) if sow["teacher_selected"] or year==5 else None}
            results.append(result)
        except Exception as exc:
            results.append({"lesson":n,"error":repr(exc)})
    summary=Counter()
    for row in results:
        summary["total"]+=1
        if row.get("error"):
            summary["errors"]+=1
        if row.get("pages"):
            summary["rendered"]+=1
        if row.get("pages")==1 and row.get("a4"):
            summary["one_page_a4"]+=1
        if (row.get("pages") or 0)>1:
            summary["multi_page"]+=1
    report={"year":year,"scope":"Actual AST-extracted ReportLab native PDF table builder with English-only isolated formatting helpers, NOT full Telegram callback, user-account or file-transfer test.",
            "all_lessons":all_lessons,
            "summary":dict(summary),
            "errors":[x for x in results if x.get("error")],
            "non_one_page":[x["lesson"] for x in results if x.get("pages")!=1 or not x.get("a4")],
            "results":results}
    (target/"native_pdf_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("NATIVE_PDF_Y%d"%year,summary,"NON_ONE_PAGE",report["non_one_page"][:40],flush=True)
    if summary["errors"]:
        raise SystemExit("Native PDF isolated layout smoke errors present")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--year",type=int,required=True,choices=range(2,7))
    ap.add_argument("--all",action="store_true")
    ap.add_argument("--lessons",type=str,default="",
                    help="Comma-separated Lesson numbers; selects only those sources")
    args=ap.parse_args()
    if args.all and args.lessons:
        ap.error("Use --all OR --lessons, not both")
    selected=None
    if args.lessons:
        try:
            selected=[int(n.strip()) for n in args.lessons.split(",")]
        except ValueError:
            ap.error("--lessons must be comma-separated integers")
    run(args.year,all_lessons=args.all,lessons=selected)
