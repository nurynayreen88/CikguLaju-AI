#!/usr/bin/env python3
"""Keluaran semakan BM Tahun 3: 165 RPH A4 PDF/DOCX + RPT Word.

PENTING: Fail-fail ini kekal DRAF. Tidak menandakan READY atau menyentuh DB.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
import json
import re

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Mm, Pt
from docx.enum.text import WD_LINE_SPACING
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "rph_standalone/bahasa_melayu/year3"
RPT_DIR = ROOT / "rpt_2027/bahasa_melayu/keluaran_format_english"
OUT = ROOT / "dist"
TARGET = OUT / "CikguLaju_BM_Tahun3_2027_DRAF_Pakej_Semakan.zip"

def register_fonts():
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if not regular.exists() or not bold.exists():
        raise RuntimeError("Font DejaVu Sans tidak tersedia pada sistem binaan")
    pdfmetrics.registerFont(TTFont("CJ",str(regular)))
    pdfmetrics.registerFont(TTFont("CJ-Bold",str(bold)))

def cleaned(line):
    return re.sub(r"\bLesson\b", "PdP", re.sub(r"\*\*|__|(?<!\w)\*(?!\s)", "", line)).strip()

def sections(src):
    for raw in src.splitlines():
        s = cleaned(raw)
        if not s:
            continue
        if s.startswith("# "):
            yield ("title",s[2:])
        elif s.startswith("## "):
            yield ("heading",s[3:])
        elif s.startswith("### "):
            yield ("heading",s[4:])
        else:
            yield ("body",s)

def layout_pdf(items,font_size):
    w,h=A4
    width=w-2*13*mm
    output=[]
    total=0
    for kind,content in items:
        if kind=="title":size=font_size+2.0;font="CJ-Bold";after=5
        elif kind=="heading":size=font_size+0.7;font="CJ-Bold";after=3.5
        else:size=font_size;font="CJ";after=1.7
        lines=simpleSplit(content,font,size,width)
        height=len(lines)*size*1.20+after
        output.append((kind,lines,font,size,after))
        total+=height
    return total,output

def make_pdf(path,items):
    usable=A4[1]-17*mm-13*mm-11*mm
    choices=[9.4,9.0,8.6,8.2,7.8,7.4,7.0,6.6,6.2]
    for size in choices:
        height,layout=layout_pdf(items,size)
        if height<=usable: break
    else:
        raise AssertionError(f"{path.name}: content cannot fit one A4 even at min font")
    buff=BytesIO()
    c=canvas.Canvas(buff,pagesize=A4,pageCompression=1)
    c.setTitle("CikguLaju Bahasa Melayu Tahun 3 2027 — DRAF")
    y=A4[1]-14*mm
    for _,lines,font,font_size,after in layout:
        c.setFont(font,font_size)
        for line in lines:
            c.drawString(13*mm,y,line)
            y-=font_size*1.20
        y-=after
    c.setStrokeColorRGB(.7,.7,.7)
    c.line(13*mm,11*mm,A4[0]-13*mm,11*mm)
    c.setFont("CJ",6.5)
    c.drawString(13*mm,7*mm,"DRAF SEMAKAN • BELUM READY • Bukan keluaran Telegram")
    c.showPage();c.save()
    b=buff.getvalue()
    if len(PdfReader(BytesIO(b)).pages)!=1:
        raise AssertionError("One-page PDF validation failed")
    return b,size

def make_docx(items):
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Mm(210);sec.page_height=Mm(297)
    sec.top_margin=Mm(9);sec.bottom_margin=Mm(9)
    sec.left_margin=Mm(12);sec.right_margin=Mm(12)
    sec.header_distance=Mm(4);sec.footer_distance=Mm(4)
    style=doc.styles["Normal"]
    style.font.name="DejaVu Sans";style.font.size=Pt(7.9)
    style.paragraph_format.space_before=Pt(0)
    style.paragraph_format.space_after=Pt(0.7)
    style.paragraph_format.line_spacing=1.0
    for kind,text in items:
        para=doc.add_paragraph()
        if kind=="title":
            para.paragraph_format.space_after=Pt(3)
        elif kind=="heading":
            para.paragraph_format.space_before=Pt(2)
            para.paragraph_format.keep_with_next=True
        run=para.add_run(text)
        if kind!="body":
            run.bold=True
            run.font.size=Pt(9.5 if kind=="title" else 8.2)
    foot=sec.footer.paragraphs[0]
    foot.add_run("CIKGULAJU • BAHASA MELAYU TAHUN 3 • DRAF SEMAKAN — BELUM READY")
    foot.style=doc.styles["Normal"]
    output=BytesIO();doc.save(output)
    return output.getvalue()

def rpt_docx(source):
    doc=Document();sec=doc.sections[0]
    sec.orientation=WD_ORIENT.LANDSCAPE
    sec.page_width=Mm(297);sec.page_height=Mm(210)
    sec.top_margin=Mm(11);sec.bottom_margin=Mm(10)
    sec.left_margin=Mm(11);sec.right_margin=Mm(11)
    normal=doc.styles["Normal"]
    normal.font.name="DejaVu Sans";normal.font.size=Pt(7.5)
    normal.paragraph_format.space_after=Pt(1)
    doc.add_heading("CIKGULAJU | RPT BAHASA MELAYU TAHUN 3 2027",level=0)
    doc.add_paragraph("Kumpulan A + B | 165 PdP | DRAF SEMAKAN (BELUM READY) | SK / KSSR Semakan")
    lines=source.splitlines()
    weekCount=0;lessonCount=0;table=None
    for line in lines:
        if line.startswith("### M"):
            weekCount+=1
            doc.add_heading(cleaned(line[4:]),level=2)
            table=doc.add_table(rows=1,cols=7)
            table.style="Table Grid"
            titles=["PdP","Tema/Unit","Tajuk","SK","SP","BT/BA","PBD/Catatan"]
            for cell,label in zip(table.rows[0].cells,titles):
                cell.text=label
                for p in cell.paragraphs:
                    for r in p.runs:r.bold=True;r.font.size=Pt(7.2)
            continue
        if table is not None and re.match(r"^\|\s*\*\*PdP \d{3}",line):
            cells=[cleaned(x) for x in line.strip().strip("|").split("|")]
            if len(cells)!=7:raise AssertionError(f"Bad RPT row: {cells}")
            row=table.add_row()
            for cell,v in zip(row.cells,cells):
                cell.text=v
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(0)
                    for run in p.runs:run.font.name="DejaVu Sans";run.font.size=Pt(6.6)
            lessonCount+=1
        elif table is not None and re.match(r"^\|\s*—\s*\|",line):
            cells=[cleaned(x) for x in line.strip().strip("|").split("|")]
            if len(cells)==7:
                row=table.add_row()
                for cell,v in zip(row.cells,cells):
                    cell.text=v
                    for p in cell.paragraphs:
                        for run in p.runs:run.font.size=Pt(6.6)
    if lessonCount!=165 or weekCount!=44:
        raise AssertionError(f"RPT count incorrect: {lessonCount} PdP; {weekCount} weeks")
    out=BytesIO();doc.save(out)
    return out.getvalue(),weekCount,lessonCount

def main():
    register_fonts()
    OUT.mkdir(parents=True,exist_ok=True)
    report={"year":3,"status":"DRAF_NOT_READY","lessons":165,"rph_pdf_one_page":0,
            "rph_docx_created":0,"min_pdf_font_pt":99,"rpt_weeks":44}
    with ZipFile(TARGET,"w",ZIP_DEFLATED,compresslevel=6) as archive:
        for n in range(1,166):
            f=SRC/f"lesson_{n:03d}.md"
            if not f.exists():raise AssertionError("Missing RPH "+str(f))
            items=list(sections(f.read_text(encoding="utf-8")))
            pdf,size=make_pdf(f,items)
            word=make_docx(items)
            archive.writestr(f"RPH_PDF_A4_DRAF/PdP_{n:03d}.pdf",pdf)
            archive.writestr(f"RPH_WORD_A4_DRAF/PdP_{n:03d}.docx",word)
            report["rph_pdf_one_page"]+=1
            report["rph_docx_created"]+=1
            report["min_pdf_font_pt"]=min(size,report["min_pdf_font_pt"])
        rpt=RPT_DIR/"RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.md"
        word,weeks,lessons=rpt_docx(rpt.read_text(encoding="utf-8"))
        report["rpt_weeks"]=weeks;report["rpt_lessons"]=lessons
        archive.writestr("RPT_2027/RPT_BM_T3_2027_A_B_DRAF.docx",word)
        archive.write(RPT_DIR/"RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.html",
                      "RPT_2027/RPT_BM_T3_2027_A_B_DRAF.html")
        report["warning"]="Word A4 final page count not visually proofed; PDF one page per RPH verified."
        archive.writestr("MANIFEST.json",json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    print("PACKAGE:",TARGET,"size:",TARGET.stat().st_size)

if __name__ == "__main__":
    main()
