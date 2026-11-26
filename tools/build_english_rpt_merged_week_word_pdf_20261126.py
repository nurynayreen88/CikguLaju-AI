"""Private QA: editable English SK RPT 2027 with real merged WEEK cells.

Layout reference: RPT ENGLISH YEAR 2 2026, Drive 1g8FlCb3bQXA0rsuZyLVBvQkGLQcQ25Fk.
The existing source_rows/schedule retain 160 SOW references and 142 sessions.
Do not upload premium Word artifacts to public CI or overwrite the live PDFs.
"""
from collections import Counter
from hashlib import sha1, sha256
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
from docx.shared import Cm, Pt, RGBColor
from tools.build_english_rpt_2027_review import source_rows, schedule, SOURCE

LIVE_BLOBS = {
    2: "4454324730144206e86aee94cbf1d7e8775c71ea",
    3: "aff6f9c67f75ea0db2ffb692214b056f6ca83b51",
    4: "2783eaf44733a516c8685f72ebf7d25762623b5e",
    5: "05902d918882775528b078d246193eff5e2a83ed",
    6: "ffce8f7b79b8821a4df9956c210454191c4af41c",
}
HEADERS = ("WEEK / DATE", "LESSON / THEME / TOPIC",
           "CONTENT STANDARD / LEARNING STANDARD", "REFERENCE / MATERIALS")
WIDTHS = (3.0, 6.0, 12.6, 5.6)
CLOSED = {6: "Festival holidays / 0 planned Lessons",
          19: "Aidiladha and Wesak / 0 planned Lessons",
          44: "Year-end activities / 0 new Lessons"}
CLOSED.update(dict.fromkeys(range(40,44), "Revision, assessment or school activities / 0 new Lessons"))

def mark(el, tag, attrs=None):
    child=OxmlElement(tag)
    for key,val in (attrs or {}).items(): child.set(qn(key),str(val))
    el.append(child)
    return child

def fill(cell, lines, *, bold=False, center=False, shade=None):
    cell.text=""
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if center else WD_CELL_VERTICAL_ALIGNMENT.TOP
    for i,line in enumerate(lines):
        p=cell.paragraphs[0] if i==0 else cell.add_paragraph()
        p.paragraph_format.space_after=Pt(1.5)
        p.paragraph_format.space_before=Pt(0)
        p.paragraph_format.line_spacing=1.06
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
        run=p.add_run(line)
        run.bold=bold or bool(re.fullmatch(r"LESSON:\s*\d+",line)) or line in {"MAIN","COMPLEMENTARY"} or line.startswith("Session ")
        run.font.name="Arial"
        run.font.size=Pt(9)
    if shade: mark(cell._tc.get_or_add_tcPr(),"w:shd",{"w:fill":shade})

def table(doc):
    t=doc.add_table(rows=1,cols=4)
    t.style="Table Grid"
    t.autofit=False
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,w in enumerate(WIDTHS):
        t.columns[i].width=Cm(w)
        t.rows[0].cells[i].width=Cm(w)
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    for cell,heading in zip(t.rows[0].cells,HEADERS,strict=True):
        fill(cell,[heading],bold=True,center=True,shade="E2EAD9")
    return t

def add_row(t):
    row=t.add_row()
    mark(row._tr.get_or_add_trPr(),"w:cantSplit")
    for cell,w in zip(row.cells,WIDTHS,strict=True): cell.width=Cm(w)
    return row

def cover(doc,year):
    # Editable Word cover candidate; exact original PDF cover is preserved
    # separately when producing the candidate PDF.
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(32)
    p.paragraph_format.space_after=Pt(20)
    run=p.add_run("RANCANGAN PENGAJARAN TAHUNAN 2027")
    run.bold=True;run.font.size=Pt(21)
    p=doc.add_paragraph(f"ENGLISH (SK) • YEAR {year} • GROUP A & GROUP B")
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold=True;p.runs[0].font.size=Pt(16)
    t=doc.add_table(rows=3,cols=2)
    t.style="Table Grid";t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,(a,b) in enumerate((("SCHOOL LOGO",""),("SCHOOL NAME",""),("TEACHER NAME",""))):
        fill(t.cell(i,0),[a],bold=True,shade="E2EAD9");fill(t.cell(i,1),[b])
    p=doc.add_paragraph("160 SOW Lessons • 142 teaching sessions")
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

def normalize(value):
    return re.sub(r"\s+"," ",value).strip()

def source_identity(year):
    path=SOURCE/f"RPT_English_SK_2027_Year_{year}_A_B.pdf"
    raw=path.read_bytes()
    actual=sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if actual!=LIVE_BLOBS[year]: raise ValueError("Active English RPT source changed")
    return path,sha256(raw).hexdigest()

def render(year,out):
    active,digest=source_identity(year)
    rows=source_rows(year)
    weeks=schedule(year)
    assert len(rows)==160 and len(weeks)==44
    assert sum(len(sessions) for _,_,_,sessions in weeks)==142
    # Confirm each original dated source row matches the integrated live PDF.
    # The exact ordered Lesson identifiers must match, not only the count.
    with fitz.open(active) as original:
        text="\n".join(p.get_text() for p in list(original)[3:])
        ids=[int(n) for n in re.findall(r"(?m)^LESSON:\s*(\d+)\s*$",text)]
        if ids!=list(range(1,161)): raise ValueError(f"Live Lesson sequence mismatch Y{year}: {len(ids)}")
        for n in ids:
            for line in [*rows[n][0],*rows[n][1],*rows[n][2]]:
                if line and normalize(line) not in normalize(text):
                    raise ValueError(f"Live content not matched Y{year} L{n}: {line}")
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Cm(29.7);sec.page_height=Cm(21)
    sec.left_margin=sec.right_margin=Cm(1.25)
    sec.top_margin=sec.bottom_margin=Cm(1.15)
    sec.header_distance=Cm(.5);sec.footer_distance=Cm(.5)
    sec.header.paragraphs[0].text=f"SCHEME OF WORK ENGLISH YEAR {year} (SK) 2027"
    footer=sec.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Page ")
    field=mark(footer._p,"w:fldSimple",{"w:instr":"PAGE"})
    style=doc.styles["Normal"];style.font.name="Arial";style.font.size=Pt(9)
    cover(doc,year)
    counts=[]
    for index,(week,a,b,sessions) in enumerate(weeks):
        # One table per week: all lessons keep separate rows and share the
        # vertically merged WEEK cell. Word repeats headers if a long week
        # crosses a page; never collapse CS/LS or join unrelated lessons.
        t=table(doc)
        if sessions:
            for slot,session in enumerate(sessions,1):
                for n in session:
                    row=add_row(t)
                    topic,standards,references=rows[n]
                    label=f"Session {slot} · 60 min" if len(session)==1 else f"Session {slot} · RPH {session[0]:03d}+{session[1]:03d}"
                    fill(row.cells[1],[topic[0],label,*topic[1:]])
                    fill(row.cells[2],standards)
                    fill(row.cells[3],references)
        else:
            row=add_row(t)
            fill(row.cells[1].merge(row.cells[3]),[CLOSED[week]])
        nrows=sum(map(len,sessions)) or 1
        merged=t.cell(1,0)
        if nrows>1: merged=merged.merge(t.cell(nrows,0))
        fill(merged,[f"{week:02d}",f"Group A: {a}",f"Group B: {b}"],bold=True,center=True,shade="EAF1E3")
        counts.append(nrows)
        # Separator between independently editable week groups.
        p=doc.add_paragraph()
        p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(0)
        p.paragraph_format.line_spacing=Pt(3)
    name=f"RPT_English_SK_2027_Year_{year}_A_B"
    word=out/(name+".docx")
    doc.save(word)
    check=Document(word)
    assert len(check.tables)==45
    seen=[]
    for t,n in zip(check.tables[1:],counts,strict=True):
        assert len(t.rows)==n+1
        if n>1:
            assert all(t.cell(1,0)._tc is t.cell(i,0)._tc for i in range(1,n+1))
        for row in t.rows[1:]:
            found=re.search(r"LESSON:\s*(\d+)",row.cells[1].text)
            if found:
                lesson=int(found[1]);seen.append(lesson)
                assert all(line in row.cells[2].text for line in rows[lesson][1])
                assert all(line in row.cells[3].text for line in rows[lesson][2])
    assert seen==list(range(1,161))
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),
                        "--headless","--convert-to","pdf","--outdir",str(folder),str(word.resolve())],
                        check=True,timeout=120)
        target=out/(name+".pdf")
        with fitz.open(folder/(name+".pdf")) as converted, fitz.open(active) as original, fitz.open() as result:
            # Keep the exact approved PDF cover. Word cover remains editable
            # pending the separate original-cover/profile visual parity review.
            result.insert_pdf(original,from_page=0,to_page=0)
            result.insert_pdf(converted,from_page=1)
            result.save(target,garbage=4,deflate=True)
        with fitz.open(target) as result,fitz.open(active) as original:
            assert result[0].get_pixmap().samples==original[0].get_pixmap().samples
            body="\n".join(p.get_text() for p in list(result)[1:])
            found=[int(n) for n in re.findall(r"LESSON:\s*(\d+)",body)]
            assert found==list(range(1,161)),(year,len(found))
            for p in result:
                assert abs(p.rect.width-841.89)<2 and abs(p.rect.height-595.28)<2
                assert p.get_text().strip()
            pages=len(result)
    return {"year":year,"lessons":160,"sessions":142,"merged_week_groups":44,"pdf_pages":pages,
            "source_sha256":digest,"word_sha256":sha256(word.read_bytes()).hexdigest(),
            "pdf_sha256":sha256(target.read_bytes()).hexdigest(),
            "status":"PRIVATE_QA_NOT_RELEASED","word_cover_visual_parity_pending":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    result=[render(y,args.out) for y in range(2,7)]
    (args.out/"report.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
