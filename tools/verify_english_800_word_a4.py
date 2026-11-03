"""Read-only offline full A4 verification for English RPH Y2-Y6 (800 lessons).
Word builder is AST-locked to the active app.py function. Y6 uses live compact adapter.
Y5 remains DRAF; generated PDFs are LibreOffice conversions, NOT native bot PDFs.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from docx import Document
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.audit_english_rph_word_a4_layout import from_source,write_word,validate_word_function_snapshot,FIELDS
from web.english_y6_word_a4_runtime import compact_word_file
from web.english_y5_standalone_runtime import load_lesson as load_y5_draft, CHOICE_LESSONS

Y2_OVERFLOW = frozenset((2,3,12,13,14))
Y5_OVERFLOW = frozenset((90,110,136))

def year5_teacher_choice_preview(n):
    """Offline-only proposal: never install runtime or pretend CS/LS are official."""
    plan = load_y5_draft(n)
    if plan is None:
        raise RuntimeError(f"Y5 teacher-choice L{n} cannot parse from original draft")
    return {
        "SET INDUKSI": plan["intro"],
        "AKTIVITI UTAMA": plan["activities"],
        "PENTAKSIRAN": plan["pbd"],
        "PENUTUP": plan["closure"],
        "BAHAN BANTU MENGAJAR": plan["materials"],
        "OBJEKTIF PEMBELAJARAN": plan["objective"],
        "KRITERIA KEJAYAAN": plan["objective"],
        "STANDARD KANDUNGAN": "Teacher to select from Year 5 DSKP (not fixed by SOW)",
        "STANDARD PEMBELAJARAN": "Teacher to select and verify against DSKP",
        "PEMULIHAN / PENGAYAAN": plan["differentiation"]
    }

def all_text(path):
    d=Document(str(path))
    a=[p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                a.extend(p.text for p in c.paragraphs)
    return "\n".join(a)

def main(year,batch_size):
    validate_word_function_snapshot()
    out=ROOT/"output"/"english_full_a4_20261103"/f"year{year}"
    wd,pd=out/"docx",out/"pdf"
    wd.mkdir(parents=True,exist_ok=True);pd.mkdir(parents=True,exist_ok=True)
    results=[];files=[]
    for n in range(1,161):
        r={"year":year,"lesson":n,"y5_draft":year==5}
        f=wd/f"Y{year}_L{n:03d}.docx"
        try:
            data=(year5_teacher_choice_preview(n) if year==5 and n in CHOICE_LESSONS
                  else from_source(year,n))
            r["teacher_choice_preview"]=bool(year==5 and n in CHOICE_LESSONS)
            r["phase_chars"]={k:len(str(data.get(k) or "")) for k in FIELDS}
            write_word(year,n,data,f)
            original=all_text(f)
            compact = (year == 6 or (year == 2 and n in Y2_OVERFLOW)
                       or (year == 5 and n in Y5_OVERFLOW))
            if compact:
                if not compact_word_file(str(f)):
                    raise ValueError("8pt Word compactor refused DOCX")
                if all_text(f) != original:
                    raise ValueError("8pt Word compactor modified lesson content")
            r["layout_adjusted"] = compact
            r["word_chars"]=len(all_text(f))
            r["word_ok"]=True
            files.append(f)
        except Exception as exc:
            r["word_ok"]=False
            r["error"]="WORD:"+repr(exc)
        results.append(r)
    batches=[]
    for offset in range(0,len(files),batch_size):
        selected=files[offset:offset+batch_size]
        cmd=["libreoffice","-env:UserInstallation=file://"+str(out/"lo-profile"),
             "--headless","--convert-to","pdf","--outdir",str(pd),*[str(f) for f in selected]]
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
        batches.append({"offset":offset,"count":len(selected),"rc":run.returncode,"stderr":run.stderr[-400:]})
    for r in results:
        if not r["word_ok"]:continue
        p=pd/f"Y{year}_L{r['lesson']:03d}.pdf"
        if not p.exists():
            r["error"]="PDF not generated"
            continue
        try:
            pages=PdfReader(str(p)).pages
            r["pages"]=len(pages)
            r["a4"]=bool(pages) and all(
                abs(float(x.mediabox.width)-595.28)<1.5 and
                abs(float(x.mediabox.height)-841.89)<1.5 for x in pages)
            r["pdf_chars"]=sum(len(x.extract_text() or "") for x in pages)
            r["text_extraction_suspect"]=r["pdf_chars"]<0.60*r["word_chars"]
        except Exception as exc:
            r["error"]="PDF:"+repr(exc)
    stats=Counter()
    for r in results:
        stats["total"]+=1
        if r.get("word_ok"):stats["word_ok"]+=1
        if "pages" in r:stats["pdf_ok"]+=1
        if r.get("pages")==1 and r.get("a4"):stats["one_page_a4"]+=1
        if r.get("pages",0)>1:stats["multi_page"]+=1
        if r.get("error"):stats["errors"]+=1
        if r.get("text_extraction_suspect"):stats["suspect_extraction"]+=1
    report={"scope":"AST-matched production Word table builder, Y6 production Word compactor, LibreOffice PDF approximation; no Telegram or native PDF",
            "year":year,"status":"audit only, not READY",
            "year2_pilot_adjustments":[2,3,12,13,14] if year == 2 else [],
            "year5_draft_pilot_adjustments":[90,110,136] if year == 5 else [],
            "year5_choice_preview_not_production":list(sorted(CHOICE_LESSONS)) if year == 5 else [],
            "counts":dict(stats),"non_one_page":[r["lesson"] for r in results if r.get("pages")!=1 or not r.get("a4")],
            "suspect_text":[r["lesson"] for r in results if r.get("text_extraction_suspect")],
            "batches":batches,"lessons":results}
    (out/"verification.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print("FULL_A4_AUDIT_Y"+str(year),json.dumps({"counts":dict(stats),"non_one_page":report["non_one_page"],
          "suspect":report["suspect_text"]},ensure_ascii=False),flush=True)
    if stats["word_ok"]!=160 or stats["pdf_ok"]!=160:
        raise SystemExit("Incomplete verification - see artifact for errors")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--year",type=int,required=True,choices=range(2,7))
    a.add_argument("--batch-size",type=int,default=25)
    args=a.parse_args()
    main(args.year,args.batch_size)
