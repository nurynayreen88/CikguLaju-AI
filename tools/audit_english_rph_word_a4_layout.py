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
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(.75);sec.bottom_margin=Cm(.75)
    sec.left_margin=Cm(1.1);sec.right_margin=Cm(1.1)
    normal=doc.styles["Normal"]
    normal.font.name="Arial";normal.font.size=Pt(8.5)
    normal.paragraph_format.space_before=Pt(0)
    normal.paragraph_format.space_after=Pt(0)
    normal.paragraph_format.line_spacing=1
    doc.add_heading("DAILY LESSON PLAN",level=1)
    info=doc.add_table(rows=0,cols=2)
    for key,val in [
        ("Subject","English"),("Year",str(y)),("Date","03/11/2026"),
        ("Day","Tuesday"),("Time","08:00–09:00"),("Class",f"{y} Amanah"),
        ("Number of pupils","30"),("Topic",f"Lesson {n}: Unit topic"),
        ("Main content standard","SOW Main: applicable content standard"),
        ("Main learning standard","SOW Main: curriculum Learning Standard"),
        ("Complementary content standard","SOW Complementary: curriculum content standard"),
        ("Complementary learning standard","SOW Complementary: Learning Standard"),
        ("Learning objective","By the end of this lesson, pupils achieve two specified, measurable lesson outcomes relevant to the unit."),
        ("Success criteria","Pupils provide individual evidence for two linked success criteria during lesson assessment."),
        ("Prior knowledge","Vocabulary from recent lessons"),
        ("Materials","Student/Pupil Book, Teacher's Book, Workbook and relevant picture cards or equipment; source-specific items vary by Lesson."),
        ("CCE / values","Communication, creativity and responsible citizenship"),
        ("HOTS / PAK21","Group discussion and paired reasoning"),
        ("Assessment / PBD",rows["PENTAKSIRAN"]),
    ]:
        cells=info.add_row().cells
        cells[0].text=key;cells[1].text=val
    phases=doc.add_table(rows=1,cols=3)
    phases.rows[0].cells[0].text="Phase"
    phases.rows[0].cells[1].text="Teaching and learning activities"
    phases.rows[0].cells[2].text="Notes"
    for name,key in (("Set induction","SET INDUKSI"),("Main activities","AKTIVITI UTAMA"),("Closure","PENUTUP")):
        r=phases.add_row()
        r.cells[0].text=name;r.cells[1].text=rows[key];r.cells[2].text=""
    summary=doc.add_table(rows=1,cols=2)
    summary.rows[0].cells[0].text="Reflection"
    summary.rows[0].cells[1].text="___/___ achieved; ___/___ need support"
    for table in doc.tables:
        table.autofit=False
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before=Pt(0)
                    paragraph.paragraph_format.space_after=Pt(0)
                    paragraph.paragraph_format.line_spacing=1
                    for run in paragraph.runs:run.font.size=Pt(8.5)
    doc.save(path)

def main():
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
            "scope":"isolated A4 layout approximation; NOT the live Word/PDF generator or a READY certification"}
    (OUT/"a4_diagnostic.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("A4_LAYOUT_DIAGNOSTIC",json.dumps({"count":len(items),"one":report["one_page"],"long":problems},ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
