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
from collections import Counter
import json
import re
from pathlib import Path
import sys

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_english_2_6_release_status_20261104 import _render
from tools.audit_english_native_pdf_core_20261104 import _make_native_pdf

SOW = json.loads((ROOT / "audits/english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
OUTPUT = ROOT / "output" / "english_2_6_native_pdf_smoke_20261104"
RPH_KEYS = ("TAJUK", "MAIN CONTENT STANDARD", "MAIN LEARNING STANDARD",
            "COMPLEMENTARY CONTENT STANDARD", "COMPLEMENTARY LEARNING STANDARD",
            "OBJEKTIF PEMBELAJARAN", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP")


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
    target=OUTPUT/f"year{year}"
    target.mkdir(parents=True,exist_ok=True)
    for n in nums:
        sow=SOW[f"{year}/{n}"]
        rows,_=_render(year,n,sow)
        if any(not str(rows.get(k) or "").strip() for k in RPH_KEYS):
            # Do not hide known per-lesson metadata omissions.
            missing=[k for k in RPH_KEYS if not str(rows.get(k) or "").strip()]
            results.append({"lesson":n,"error":"missing row fields "+repr(missing)})
            continue
        try:
            final=target/f"Y{year}_L{n:03d}_native_layout.pdf"
            _make_native_pdf(rows, year, n, final)
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
                        if not sow["teacher_selected"] else None,
                    "has_pbd":bool(content and "assessment" in content.casefold() or
                                     "pentaksiran" in content.casefold()),
                    "internal_label_in_pdf":bool(re.search(r"\bDRAF\b|QA status:", content, re.I))}
            results.append(result)
        except Exception as exc:
            results.append({"lesson":n,"error":repr(exc)})
            if len(results) == 1:
                print(f"Native PDF diagnostic for Lesson {n}: {exc!r}", flush=True)
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
    if summary["errors"] or report["non_one_page"]:
        raise SystemExit("Native PDF verification failed. See native_pdf_report.json.")
    if any(row.get("internal_label_in_pdf") for row in results):
        raise SystemExit("A teacher PDF contains an internal draft or QA label.")


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
