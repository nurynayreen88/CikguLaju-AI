"""English Y2-6 offline A4 layout diagnostic using real source content.

This is NOT the Telegram Word generator. It deliberately uses an isolated
python-docx approximation of its three-table A4 layout. Read-only: never
imports app.py, uses production credentials, or changes source files.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

from docx import Document
from docx.shared import Cm,Pt
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
# Direct invocation (python tools/...) must also resolve root-level project modules.
sys.path.insert(0,str(ROOT))
OUT=ROOT/"output"/"english_a4_layout_audit"
SAMPLES={2:[1,40,82,127,152,160],3:[1,20,61,80,93,126,160],
         4:[1,30,74,93,160],5:[1,28,141,159],6:[1,15,21,25,26,31,37,160]}
FIELDS=("SET INDUKSI","AKTIVITI UTAMA","PENTAKSIRAN","PENUTUP")

def from_source(y,n):
    text=(ROOT/f"rph_standalone/english/year{y}/lesson_{n:03d}.md").read_text(encoding="utf-8")
    matches=list(re.finditer(r"(?m)^## ([^\r\n]+)",text))
    parts={}
    for i,m in enumerate(matches):
        h=m.group(1).casefold()
        body=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        body=re.split(r"(?im)^\*\*(?:QA|Source|Status|Verified SOW lesson outline).*?:\*\*",body,maxsplit=1)[0].strip()
        parts[h]=body
    def find(prefixes):
        return next((v for k,v in parts.items() if any(k.startswith(p) for p in prefixes) and v),"")
    activities="\n\n".join(h+"\n"+v for h,v in parts.items() if re.match(r"activity [1234]\b",h))
    rows={"SET INDUKSI":find(("set induction",)),
          "AKTIVITI UTAMA":activities,
          "PENTAKSIRAN":find(("assessment","pbd","reinforcement")),
          "PENUTUP":find(("closure",))}
    if y in (2,3):
        state={"subject":"English","year":f"Tahun {y}","lesson_no":n}
        if y==2:
            from english_y2_standalone_render import apply
        else:
            from english_y3_standalone_render import apply
        rows=apply(state,rows)
    elif y==5:
        from web.english_y5_standalone_runtime import adapt_rows
        state={"subject":"English","year":"Tahun 5","lesson_no":n}
        rows=adapt_rows(state,rows)
    elif y==6:
        from web.english_y6_standalone_runtime import adapt_rows
        state={"subject":"English","year":"Tahun 6","lesson_no":n}
        rows=adapt_rows(state,rows)
    for field in FIELDS:
        if not str(rows.get(field) or "").strip():
            raise RuntimeError(f"Y{y} L{n}: missing {field}")
    return rows

def write_word(y,n,rows,path):
    # This function uses the exact active Word table routine from app.py,
    # with an isolated source-row injector; Telegram/DB startup never runs.
    from qa.english_word_builder_snapshot import _create_rph_word
    doc=Document()
    section=doc.sections[0]
    section.top_margin=Cm(1.35);section.bottom_margin=Cm(1.4)
    section.left_margin=Cm(1.55);section.right_margin=Cm(1.55)
    normal=doc.styles["Normal"]
    normal.font.name="Arial";normal.font.size=Pt(10.5)
    state={"task":"rph","subject":"English","year":f"Tahun {y}"}
    values=dict(rows)
    values.update({
        "MATA PELAJARAN":"English",
        "TAHUN/TINGKATAN":f"Tahun {y}",
        "TARIKH":"03/11/2026","HARI":"Tuesday",
        "MASA":"08:00 – 09:00","KELAS":f"{y} Amanah",
        "BILANGAN MURID":"30","TAJUK":f"Year {y} Lesson {n}",
        "PENGETAHUAN SEDIA ADA":"Known language and vocabulary from previous lessons",
        "EMK / NILAI":"Communication, creativity, collaboration",
        "KBAT / PAK21":"Group and pair reasoning",
        "REFLEKSI":"___/___ achieved; ___/___ need support",
    })
    values.setdefault("MAIN CONTENT STANDARD","SOW Main standard")
    values.setdefault("MAIN LEARNING STANDARD","Official Learning Standard")
    values.setdefault("COMPLEMENTARY CONTENT STANDARD","SOW Complementary standard")
    values.setdefault("COMPLEMENTARY LEARNING STANDARD","Official Learning Standard")
    values.setdefault("OBJEKTIF PEMBELAJARAN","By the end of the lesson, pupils attain two measurable relevant skills.")
    values.setdefault("KRITERIA KEJAYAAN",values["OBJEKTIF PEMBELAJARAN"])
    values.setdefault("BAHAN BANTU MENGAJAR","Student/Pupil Book, Teacher's Book and unit resources")
    _create_rph_word(doc,section,state,values,str(path))


def validate_word_function_snapshot():
    import ast
    # app.py includes later-version Python syntax unrelated to the Word builder.
    # Parse only the last active Word function, not the 2.8 MB production module.
    app_text=(ROOT/"app.py").read_text(encoding="utf-8")
    start=app_text.rindex("\ndef _create_rph_word(")+1
    end=app_text.index("\ndef create_word_file(",start)
    active=ast.parse(app_text[start:end])
    frozen=ast.parse((ROOT/"qa/english_word_builder_snapshot.py").read_text(encoding="utf-8"))
    def last(tree):
        return [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_create_rph_word"][-1]
    if ast.dump(last(active),include_attributes=False)!=ast.dump(last(frozen),include_attributes=False):
        raise RuntimeError("Production Word layout changed: update A4 snapshot after review")


def main():
    validate_word_function_snapshot()
    word=OUT/"docx";pdf=OUT/"pdf"
    word.mkdir(parents=True,exist_ok=True);pdf.mkdir(parents=True,exist_ok=True)
    items=[]
    for y,lessons in SAMPLES.items():
        for n in lessons:
            rows=from_source(y,n)
            file=f"Y{y}_L{n:03d}"
            p=word/(file+".docx")
            write_word(y,n,rows,p)
            items.append({"year":y,"lesson":n,"chars":sum(len(rows[k]) for k in FIELDS),"name":file})
    cmd=["libreoffice","-env:UserInstallation=file://"+str(OUT/"lo-profile"),"--headless",
         "--convert-to","pdf","--outdir",str(pdf),*[str(word/(i["name"]+".docx")) for i in items]]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=420)
    if result.returncode:
        raise RuntimeError("LibreOffice failed: "+result.stderr[-1000:])
    problems=[]
    for item in items:
        p=pdf/(item["name"]+".pdf")
        if not p.exists():raise RuntimeError("Missing PDF "+str(p))
        pages=PdfReader(p).pages
        item["pages"]=len(pages)
        item["a4"]=all(abs(float(x.mediabox.width)-595.28)<1.5 and abs(float(x.mediabox.height)-841.89)<1.5 for x in pages)
        if len(pages)!=1:problems.append(item)
    report={"sample_count":len(items),"one_page":len(items)-len(problems),
            "multi_page":problems,"samples":items,
            "scope":"exact app.py Word table function with isolated row and display helpers; LibreOffice approximation; NOT live Telegram delivery or native PDF generator"}
    (OUT/"a4_diagnostic.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("A4_LAYOUT_DIAGNOSTIC",json.dumps({"count":len(items),"one":report["one_page"],"long":problems},ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
