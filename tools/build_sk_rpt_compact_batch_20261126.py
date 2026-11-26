"""12 SK RPT candidates, native editable cell tables and verified original covers.

Reference table structures: BM existing 2026-layout HTML; PJ SK 2026 Drive
1iYXEatUbSTbV1B4QqLDJsRx_YrW_KsFF; Mathematics SK 2026 Drive
1Lj17523Hl6xQj870vYvR0VFgPGJnsNVb. Only retain the published 2027
SK/SP, lesson labels, notes, dates and source links. Never infer a TP.
The current PDF is authoritative for exact lesson/week allocation.
No OCR, body images, paid public artifacts, or modification of production.
"""
from collections import Counter, defaultdict
from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import argparse
import json
import re
import subprocess
import tempfile

import fitz
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.shared import Cm, Pt
from scripts.build_web_rpt_weekly_suggestions import read_weeks, ROOT
from scripts.reschedule_web_rpt_teaching_weeks import pdf_rows
from web.rpt_original_cover_word import cover_layout, cover_page, attach_original_cover, replace_cover_image

SCOPE={"bahasa_melayu":("BM",range(2,7),"Bahasa Melayu"),
       "pjpk":("PJPK",range(2,7),"Pendidikan Jasmani dan Pendidikan Kesihatan"),
       "matematik":("MATH",range(2,4),"Matematik")}
BANDS=(140,320,445,655,819)
HEADERS=("MINGGU / TARIKH","TEMA / UNIT / TAJUK","STANDARD KANDUNGAN","STANDARD PEMBELAJARAN","CATATAN / RUJUKAN")
WIDTHS=(3.1,5.6,4.9,7.3,6.3)
COLORS={"bahasa_melayu":"D9E9F3","pjpk":"E8EFD7","matematik":"DDE8F5"}
LESSON=re.compile(r"(?:(PJ|PK) )?(?:Lesson|PdP) (\d{3})")
WEEK=re.compile(r"\bM(\d{2})\b")
DATE=re.compile(r"\d{2}/\d{2}/2027")
def mark(el,tag,attrs=None):
    node=OxmlElement(tag)
    for k,v in (attrs or {}).items(): node.set(qn(k),str(v))
    el.append(node)
    return node
def norm(text):
    return re.sub(r"\s+"," ",text).strip()
def format_cell(cell,lines,*,bold=False,center=False,fill=None):
    cell.text=""
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if center else WD_CELL_VERTICAL_ALIGNMENT.TOP
    for i,line in enumerate(lines):
        p=cell.paragraphs[0] if i==0 else cell.add_paragraph()
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after=Pt(1)
        p.paragraph_format.line_spacing=1.03
        run=p.add_run(line)
        run.bold=bold or LESSON.fullmatch(line) is not None
        run.font.name="Arial";run.font.size=Pt(8.5)
    if fill: mark(cell._tc.get_or_add_tcPr(),"w:shd",{"w:fill":fill})
def hyperlink(cell,url):
    if not url.startswith(("https://","http://")): raise ValueError("Unexpected source link")
    p=cell.add_paragraph()
    link=mark(p._p,"w:hyperlink",{"r:id":p.part.relate_to(url,RELATIONSHIP_TYPE.HYPERLINK,is_external=True)})
    run=mark(link,"w:r")
    props=mark(run,"w:rPr");mark(props,"w:color",{"w:val":"164D7E"})
    mark(props,"w:u",{"w:val":"single"})
    mark(run,"w:t").text="Rujukan sumber"
def source_cells(pdf,page_no,row):
    page=pdf[page_no]
    cols=[[] for _ in range(4)]
    for block in page.get_text("dict",clip=row)["blocks"]:
        for line in block.get("lines",()):
            for s in line["spans"]:
                v=s["text"].strip()
                if not v:continue
                x,y=s["origin"]
                idx=next((i for i in range(4) if BANDS[i]-0.2<=x<BANDS[i+1]),None)
                if idx is None: raise ValueError("Text outside original column bands")
                cols[idx].append((y,x,v))
    result=[[" ".join(v for _,_,v in group) for group in _lines(c)] for c in cols]
    if not result[0]: raise ValueError("Missing topic")
    if Counter(norm(" ".join(v for c in result for v in c)).split())!=Counter(norm(page.get_text(clip=row)).split()):
        raise ValueError("Source row text not completely retained")
    links=[]
    for l in page.get_links():
        if row.contains(l["from"]):
            if l["kind"]!=fitz.LINK_URI: raise ValueError("Unexpected link kind")
            links.append(l["uri"])
    return result,links
def _lines(col):
    result=[]
    for item in sorted(col):
        if not result or abs(result[-1][0][0]-item[0])>0.5: result.append([])
        result[-1].append(item)
    return [sorted(line,key=lambda x:x[1]) for line in result]
def week_data(pdf,subject,source):
    dates,plan=read_weeks(source,subject)
    assignments={(c,n):w for w,groups in plan.items() for c,ids in groups.items() for n in ids}
    found=pdf_rows(pdf,False)
    if len(found)!=len(assignments) or set(row[0] for row in found)!=set(assignments):
        raise ValueError("Week allocations and source lesson IDs differ")
    groups=defaultdict(list)
    for identity,pageno,rect in found:
        cells,links=source_cells(pdf,pageno,rect)
        groups[assignments[identity]].append((identity,cells,links))
    # Preserve any printed closure week as well. Never allocate a new lesson.
    closures={}
    for page in list(pdf)[1:]:
        for draw in page.get_drawings():
            rect=draw["rect"]
            if draw["type"] not in ("f","fs") or abs(rect.x0-35)>.1 or abs(rect.width-105)>.1: continue
            cell=page.get_text(clip=rect)
            match=WEEK.search(cell)
            if not match:continue
            week=int(match[1])
            if week in groups:continue
            ds=DATE.findall(cell)
            if len(ds)!=4:raise ValueError("Closure dates missing")
            body=page.get_text(clip=fitz.Rect(140,rect.y0,page.rect.width-23,rect.y1)).strip()
            if LESSON.search(body):raise ValueError("Unmapped lesson in closure week")
            closures[week]=(tuple(date(int(d[6:]),int(d[3:5]),int(d[:2])).isoformat() for d in ds),body)
    return dates,groups,closures
def row_add(t):
    r=t.add_row()
    mark(r._tr.get_or_add_trPr(),"w:cantSplit")
    for c,w in zip(r.cells,WIDTHS):c.width=Cm(w)
    return r
def render(subject,year,out,manifest):
    code,_,label=SCOPE[subject]
    entry=manifest["files"][f"{subject}:{year}"]
    source=ROOT/entry["path"]
    if sha256(source.read_bytes()).hexdigest()!=entry["sha256"]:raise ValueError("Source checksum mismatch")
    layout=cover_layout(ROOT.parent,subject,year,source)
    with fitz.open(source) as pdf:
        dates,groups,closures=week_data(pdf,code,source)
        expected=[identity for week in sorted(groups) for identity,_,_ in groups[week]]
    doc=Document()
    cover=cover_page(source,layout)
    sec=attach_original_cover(doc,cover)
    sec.header.paragraphs[0].text=f"RANCANGAN PENGAJARAN TAHUNAN 2027 • {label.upper()} TAHUN {year}"
    footer=sec.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Halaman ");mark(footer._p,"w:fldSimple",{"w:instr":"PAGE"})
    style=doc.styles["Normal"];style.font.name="Arial";style.font.size=Pt(8.5)
    style.paragraph_format.space_after=Pt(0)
    t=doc.add_table(rows=1,cols=5)
    t.style="Table Grid";t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,w in enumerate(WIDTHS):
        t.columns[i].width=Cm(w);t.rows[0].cells[i].width=Cm(w)
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    heads=HEADERS if subject!="matematik" else ("MINGGU / TARIKH","BIDANG / TAJUK / LESSON","STANDARD KANDUNGAN","STANDARD PEMBELAJARAN","CATATAN")
    for c,h in zip(t.rows[0].cells,heads):format_cell(c,[h],bold=True,center=True,fill=COLORS[subject])
    links_expected=[]
    blocks=[]
    for week in sorted(set(groups)|set(closures)):
        first=len(t.rows)
        if week in groups:
            d=dates[week]
            for identity,cols,links in groups[week]:
                r=row_add(t)
                for c,v in zip(r.cells[1:],cols):format_cell(c,v or [""])
                for uri in links:hyperlink(r.cells[4],uri)
                links_expected.extend(links)
        else:
            d,body=closures[week]
            r=row_add(t)
            format_cell(r.cells[1].merge(r.cells[4]),[body or ""])
        last=len(t.rows)-1
        merged=t.cell(first,0).merge(t.cell(last,0)) if last>first else t.cell(first,0)
        format_cell(merged,[f"{week:02d}","Kumpulan A:",f"{d[0][8:]}/{d[0][5:7]} – {d[1][8:]}/{d[1][5:7]}",
                             "Kumpulan B:",f"{d[2][8:]}/{d[2][5:7]} – {d[3][8:]}/{d[3][5:7]}"],bold=True,center=True,fill="EAF1E3")
        blocks.append((first,last))
    stem=f"CIKGULAJU_RPT_{subject.upper()}_SK_TAHUN_{year}_2027"
    word=out/(stem+".docx");doc.save(word)
    check=Document(word);assert len(check.tables)==1
    table=check.tables[0];assert table.rows[0]._tr.get_or_add_trPr().find(qn("w:tblHeader")) is not None
    for first,last in blocks:
        assert all(table.cell(first,0)._tc is table.cell(i,0)._tc for i in range(first,last+1))
    actual=[]
    for row in table.rows[1:]:
        for p in row.cells[1].paragraphs:
            m=LESSON.fullmatch(p.text.strip())
            if m:actual.append((m[1] or "",int(m[2])))
    assert actual==expected,(subject,year,len(actual),len(expected))
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless",
                        "--convert-to","pdf","--outdir",str(folder),str(word.resolve())],check=True,timeout=120)
        target=out/(stem+".pdf")
        with fitz.open(folder/(stem+".pdf")) as generated, fitz.open(source) as old, fitz.open() as final:
            assert len(generated)>=2
            final.insert_pdf(old,from_page=0,to_page=0)
            final.insert_pdf(generated,from_page=1)
            final.save(target,garbage=4,deflate=True)
        with fitz.open(target) as final,fitz.open(source) as old:
            assert final[0].get_pixmap().samples==old[0].get_pixmap().samples
            actual=[]
            for p in list(final)[1:]:
                body=norm(p.get_text())
                assert all(norm(h) in body for h in heads),(subject,year,p.number+1,"header missing")
                for ln in p.get_text().splitlines():
                    m=LESSON.fullmatch(ln.strip())
                    if m:actual.append((m[1] or "",int(m[2])))
            assert actual==expected,(subject,year,len(actual),len(expected))
            links_new=[l["uri"] for p in list(final)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI]
            assert Counter(links_new)==Counter(links_expected)
            pages=len(final)
    # Exercise sample profile injection in Word without modifying any teaching row.
    personalized=replace_cover_image(word.read_bytes(),source,layout,{"school":"SK CONTOH UJIAN","teacher":"GURU CONTOH","state":"","logo":None})
    assert Document(BytesIO(personalized)).tables[0]._tbl.xml==check.tables[0]._tbl.xml
    return {"subject":subject,"year":year,"lessons":len(expected),"weekly_groups":len(blocks),
            "pdf_pages":pages,"original_pdf_cover_identical":True,"word_cover_profile_test":True,
            "source_sha256":entry["sha256"],"status":"QA_ONLY_NOT_RELEASED"}
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",required=True,type=Path);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/"manifest.json").read_text("utf8"))
    results=[];failures=[]
    for subject,(_,years,_) in SCOPE.items():
        for year in years:
            try:
                r=render(subject,year,a.out,manifest);results.append(r);print(json.dumps(r),flush=True)
            except Exception as e:
                failures.append({"subject":subject,"year":year,"error":str(e)});print(json.dumps(failures[-1]),flush=True)
    (a.out/"report.json").write_text(json.dumps({"results":results,"failures":failures},indent=2))
    if failures:raise SystemExit("QA failures: "+str(len(failures)))
if __name__=="__main__":main()
