"""Create Sains 2027 A/B RPT review DOCX and landscape A4 PDFs for Years2–6.

This is NOT an official, scheduled or downloadable live RPT. Unit/PdP/SK/SP
come from v25.82 source rows, canonicalized for review. Weeks and dates are
intentionally blank until official 2027 state calendar and local timetable are
integrated. Year1 KP2027 Alam dan Manusia is *not* reused from legacy Sains.
"""
from __future__ import annotations
import csv
import json
from datetime import date
import os
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, LongTable, TableStyle
)
from tools.audit_sains_25_82_delta_20261106 import ROOT as DB_ROOT, load, SOURCES
from web.sains_canonical_unit_preview_20261106 import canonical_science_year
from web.sains_y3_rph_activity_preview_20261106 import source_ledgers

OUT=ROOT/"build/sains_rpt_2027_AB_REVIEW_ONLY_20261106"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
EXPECTED={2:51,3:45,4:79,5:83,6:84}
CALENDAR_SOURCE=ROOT/"audits/sains_rpt_2027_calendar_windows_20261106.json"

def calendar_for(group):
    """KPM group windows are reference dates, NEVER automatic PdP slots."""
    data=json.loads(CALENDAR_SOURCE.read_text(encoding="utf-8"))
    if data.get("status")!="GROUP_PERIODS_CONFIRMED__STATE_DATES_AND_CLASS_TIMETABLE_PENDING":
        raise ValueError("Unapproved calendar source")
    if set(data.get("groups",{}))!={"A","B"} or group not in ("A","B"):
        raise ValueError("Invalid KPM school group")
    block=data["groups"][group]
    start=date.fromisoformat(block["starts"])
    last=date.fromisoformat(block["last_school_day"])
    if start!=date(2027,1,4) or last != date(2027,12,2 if group=="A" else 3):
        raise ValueError("KPM session envelope changed; re-audit required")
    windows=block["holiday_windows"]
    if len(windows)!=4:
        raise ValueError("Expected exactly four official school break windows")
    last_end=None
    for w in windows:
        begin=date.fromisoformat(w["start"])
        end=date.fromisoformat(w["end"])
        if begin>end or begin.year!=2027 or end.year!=2027:
            raise ValueError("Invalid 2027 school break")
        if begin<=start or (last_end and begin<=last_end):
            raise ValueError("Overlapping or out-of-order KPM school breaks")
        last_end=end
    return block

def calendar_cover_lines(group):
    cal=calendar_for(group)
    fmt=lambda iso:date.fromisoformat(iso).strftime("%d/%m/%Y")
    lines=[f"KPM 2027 • Kumpulan {group}: {fmt(cal['starts'])} – {fmt(cal['last_school_day'])}."]
    for window in cal["holiday_windows"]:
        lines.append(f"{window['name']}: {fmt(window['start'])} – {fmt(window['end'])}.")
    lines.append("Cuti negeri/gantian, jadual sekolah dan tarikh setiap PdP: BELUM DISAHKAN.")
    return lines

def safe_text(value):
    return str(value or "").strip()

def enrich_rows(rows,year,pages):
    canonical,_=canonical_science_year(rows,year,2027)
    result=[]
    seen=set()
    for row in sorted(canonical,key=lambda x:int(x["source_sequence_no"])):
        code=row["pdp_sequence_code"]
        if code in seen:raise RuntimeError("Duplicate source PdP: "+code)
        seen.add(code)
        title=row["pdp_title"]
        candidates=""
        if year==3:
            match=pages[code]
            if match["sp_code"]!=row["sp_code"]:
                raise ValueError("RPT/Page source version mismatch")
            candidates=", ".join(map(str,match["printed_book_page_candidates"]))
        result.append({
            "PdP asal":str(row["source_sequence_no"]),
            "Kod sumber":code,
            "Unit":row["unit_title"],
            "SK":row["sk_code"],
            "SP":row["sp_code"],
            "Fokus PdP (sumber, perlu QA)":title,
            "BT ms (cadangan)":candidates,
            "Minggu/tarikh":"BELUM DIJADUAL",
            "Status":"DRAF_SEMAK",
        })
    if len(result)!=EXPECTED[year]:
        raise ValueError(f"Year {year} source row count changed")
    return result

def docx_file(path,year,group,rows):
    doc=Document()
    sec=doc.sections[0];sec.orientation=WD_ORIENT.LANDSCAPE
    sec.page_width=Cm(29.7);sec.page_height=Cm(21.0)
    sec.top_margin=Cm(1.3);sec.bottom_margin=Cm(1.25)
    sec.left_margin=Cm(1.4);sec.right_margin=Cm(1.4)
    normal=doc.styles["Normal"]
    normal.font.name="Arial";normal.font.size=Pt(8.2)
    h=doc.add_paragraph()
    h.alignment=WD_ALIGN_PARAGRAPH.CENTER
    h.add_run("CIKGULAJU\n").bold=True
    h.add_run("RANCANGAN PENGAJARAN TAHUNAN 2027\n").bold=True
    h.add_run("SAINS — TAHUN "+str(year)+"\n").bold=True
    h.add_run("KUMPULAN "+group).bold=True
    h.paragraph_format.space_before=Pt(65)
    h.paragraph_format.space_after=Pt(30)
    for text in [
        "STATUS: DRAF INDEKS PDP — BELUM SIAP UNTUK PENGGUNA",
        "Nama guru: ____________________________________",
        "Nama sekolah: ____________________________________",
        "Rujukan: Sains KSSR (Semakan 2017), sumber PdP v25.82.",
        *calendar_cover_lines(group),
        "Perhatian: Tahun 1 KP2027 menggunakan sumber Alam dan Manusia yang berasingan.",
    ]:
        p=doc.add_paragraph(text)
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(9)
    doc.add_page_break()
    p=doc.add_paragraph(f"Sains Tahun {year} • Kumpulan {group} • {len(rows)} PdP sumber")
    p.runs[0].bold=True
    p.runs[0].font.size=Pt(11)
    t=doc.add_table(rows=1,cols=7)
    t.style="Table Grid"
    columns=["PdP","Unit","SK","SP","Fokus PdP","BT ms*","Tarikh PdP"]
    for c,name in zip(t.rows[0].cells,columns):
        c.text=name
    for row in rows:
        cells=t.add_row().cells
        for cell,value in zip(cells,[
            row["PdP asal"],row["Unit"],row["SK"],row["SP"],
            row["Fokus PdP (sumber, perlu QA)"],row["BT ms (cadangan)"],"Belum dijadual"
        ]):
            cell.text=value
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(0)
                for r in p.runs:r.font.size=Pt(7.3)
    doc.add_paragraph("* Nombor halaman BT Tahun 3 ialah petunjuk sumber yang masih perlu disahkan; tahun lain kosong, bukan diteka.")
    doc.add_paragraph("Dokumen ini ialah indeks DRAF untuk penyusunan RPT; bukan RPT sekolah yang telah diluluskan.")
    doc.save(path)
    check=Document(path)
    if check.sections[0].orientation!=WD_ORIENT.LANDSCAPE:
        raise RuntimeError("RPT DOCX not landscape")
    if len(check.tables)!=1 or len(check.tables[0].rows)!=len(rows)+1:
        raise RuntimeError("RPT source rows lost")

def pdf_file(path,year,group,rows):
    if not Path(FONT).is_file():raise FileNotFoundError("DejaVu font unavailable")
    if "RPTSains" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("RPTSains",FONT))
    style=ParagraphStyle("rptbody",fontName="RPTSains",fontSize=7.1,leading=9)
    title=ParagraphStyle("rpttitle",parent=style,fontSize=20,leading=27,
                         alignment=1,spaceAfter=25)
    subtitle=ParagraphStyle("rptsubtitle",parent=style,fontSize=10,leading=15,
                            alignment=1,spaceAfter=13)
    def pg(text):return Paragraph(escape(str(text)),style)
    doc=SimpleDocTemplate(str(path),pagesize=landscape(A4),
        leftMargin=26,rightMargin=26,topMargin=31,bottomMargin=31)
    story=[Spacer(1,36),
           Paragraph("RANCANGAN PENGAJARAN TAHUNAN 2027",title),
           Paragraph(f"SAINS TAHUN {year} — KUMPULAN {group}",title),
           Paragraph("DRAF INDEKS PDP — BELUM DILULUSKAN UNTUK PENGGUNA",subtitle),
           Paragraph("Nama guru: ___________________________________________",subtitle),
           Paragraph("Nama sekolah: _________________________________________",subtitle),
           *[Paragraph(escape(line),subtitle) for line in calendar_cover_lines(group)],
           Paragraph("Sumber v25.82. Kod PdP, SK dan SP asal dipelihara. Tahun 1 KP2027 tidak termasuk.",subtitle),
           PageBreak(),
           Paragraph(f"Sains Tahun {year} | Kumpulan {group} | {len(rows)} PdP (DRAF)",subtitle)]
    header=["PdP","Unit buku teks","SK","SP","Tajuk/Fokus sumber","BT ms*","Minggu/tarikh"]
    cells=[[pg(x) for x in header]]
    for row in rows:
        cells.append([pg(x) for x in [
            row["PdP asal"],row["Unit"],row["SK"],row["SP"],
            row["Fokus PdP (sumber, perlu QA)"],row["BT ms (cadangan)"],
            "Belum dijadual"]])
    width=[36,127,42,47,292,50,95]
    tab=LongTable(cells,colWidths=width,repeatRows=1,hAlign="LEFT")
    tab.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.28,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))
    story.append(tab)
    story.append(Paragraph("* Halaman Tahun 3 ialah cadangan perlu semakan visual; tahun lain belum dipadankan.",style))
    doc.build(story)
    pdf=PdfReader(str(path))
    if len(pdf.pages)<2:raise RuntimeError("RPT cover or table missing")
    for page in pdf.pages:
        b=page.mediabox
        if not abs(float(b.width)-landscape(A4)[0])<2:
            raise RuntimeError("RPT PDF not landscape A4")

def main():
    import shutil
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    ref,_=source_ledgers()
    with tempfile.TemporaryDirectory(prefix="sains_rpt_source_") as tmp:
        all_rows=load(SOURCES["v25.82"],DB_ROOT,Path(tmp))
    total=0
    for year in range(2,7):
        active=[r for r in all_rows if r.get("year_label")==f"Tahun {year}"]
        lesson_rows=enrich_rows(active,year,ref)
        total+=len(lesson_rows)
        # Save one text-based shared source ledger per grade for approval.
        with (OUT/f"SAINS_TAHUN_{year}_SOURCE_DRAF.csv").open(
            "w",encoding="utf-8-sig",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(lesson_rows[0]))
            writer.writeheader();writer.writerows(lesson_rows)
        for group in ("A","B"):
            stem=f"RPT_SAINS_TAHUN_{year}_2027_KUMPULAN_{group}_DRAF"
            docx_file(OUT/(stem+".docx"),year,group,lesson_rows)
            pdf_file(OUT/(stem+".pdf"),year,group,lesson_rows)
    if total!=342:raise RuntimeError("Sains Years2-6 source changed")
    (OUT/"README_DRAF.txt").write_text(
        "10 Word dan 10 PDF RPT Sains Tahun 2–6 (Kumpulan A/B), LANDSCAPE A4.\n"
        "Muka depan dan tingkap cuti KPM mengikut Kumpulan A/B disediakan; PdP tidak diberi tarikh.\\n"
        "Cuti negeri/gantian dan jadual waktu sekolah belum disahkan.\\n"
        "342 PdP asal, SK/SP tidak diubah. Tahun 1 KP2027 diasingkan.\n"
        "Ini BUKAN dokumen RPT FINAL atau bahan pengguna.\n",encoding="utf-8")
    print("RPT_SAINS_2027_PREVIEW: years 2-6=5, groups A/B=2, "
          "DOCX=10 PDF_LANDSCAPE_A4=10 source PdP=342 status=DRAF")

if __name__=="__main__":main()
