"""Build 45 Year3 Sains Word/PDF RPH REVIEW PACK from source-locked activities.

No import of app.py, no Telegram, no quotas, no database writes.
Output only to the CI workspace. The PDFs are mechanically checked as exactly
one A4 page; DOCX are compact A4 templates pending visual Word-render QA.
ALL files stamped DRAF, never upload as user-facing approved materials.
"""
from tools.render_sains_y3_3_secondary_sp_pbd_20261107 import TASKS as SECONDARY_PBD, stem as secondary_stem
from __future__ import annotations
import csv
import io
import os
import re
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from web.sains_y3_rph_activity_preview_20261106 import adapt_rows, source_ledgers

OUTPUT=ROOT/"build"/"sains_y3_45_rph_REVIEW_ONLY_20261106"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LABELS={"TAJUK":"Tajuk","OBJEKTIF PEMBELAJARAN":"Objektif",
        "KRITERIA KEJAYAAN":"Kriteria kejayaan","BAHAN BANTU MENGAJAR":"Bahan",
        "SET INDUKSI":"Set induksi","AKTIVITI UTAMA":"Aktiviti utama",
        "PENTAKSIRAN":"Penilaian/PBD","PENUTUP":"Penutup"}

def skill_summary(rows):
    """Compact DSKP science process and hands-on skill evidence for one-page RPH."""
    out=rows["KEMAHIRAN PROSES SAINS"]
    manip=rows.get("KEMAHIRAN MANIPULATIF DAN KESELAMATAN","")
    if manip:
        out+="\nManipulatif/peraturan: "+manip
    return out

def source_state(rec):
    sp=rec["sp_code"]
    return {"subject":"Sains","year":"Tahun 3","year_label":"Tahun 3",
            "pdp_sequence_code":rec["pdp_code"],"sk_code":sp.rsplit(".",1)[0],
            "sp_code":sp}

def science_unit(sp):
    x=int(sp.split(".",1)[0])
    names={3:"Manusia",4:"Haiwan",5:"Tumbuh-tumbuhan",6:"Pengukuran",
           7:"Ketumpatan",8:"Asid dan Alkali",9:"Sistem Suria",10:"Mesin"}
    return f"Unit {x}: {names[x]}"

def sample_rows(rec):
    state=source_state(rec)
    original={"REFLEKSI":"____/____ murid mencapai objektif.",
              "TARIKH":"____/____/________","MATA PELAJARAN":"Sains"}
    data=adapt_rows(state,original)
    if data is original or "AKTIVITI UTAMA" not in data:
        raise ValueError("No approved-source activity draft for "+rec["pdp_code"])
    for sp,task in SECONDARY_PBD.items():
        if task["pdp"]==rec["pdp_code"]:
            if state["sp_code"]!=task["primary"]:
                raise ValueError("Changed source primary-SP for Year3 multi-SP "+rec["pdp_code"])
            note=(f" PBD bagi SP tambahan {sp}: gunakan lembaran CikguLaju "
                  f"{secondary_stem(sp)}.pdf (bukan Buku Aktiviti rasmi; "
                  "semakan panitia masih diperlukan).")
            data["PENTAKSIRAN"]+=note
            data["BUKU AKTIVITI / LATIHAN"]+=(" SP tambahan "+sp+" menggunakan "
                "lembaran PBD asli berasingan, bukan m/s Buku Aktiviti untuk SP utama.")
    return state,data

def _set_doc_cell(cell,text,bold=False):
    cell.text=""
    p=cell.paragraphs[0]
    p.paragraph_format.space_after=Pt(1)
    p.paragraph_format.space_before=Pt(0)
    run=p.add_run(text)
    run.bold=bold
    run.font.size=Pt(8)

def word_doc(path,number,unit,state,rows):
    doc=Document()
    section=doc.sections[0]
    section.page_width=Cm(21)
    section.page_height=Cm(29.7)
    section.top_margin=Cm(1.0);section.bottom_margin=Cm(1.0)
    section.left_margin=Cm(1.15);section.right_margin=Cm(1.15)
    base=doc.styles["Normal"]
    base.font.name="Arial";base.font.size=Pt(8.5)
    base.paragraph_format.space_after=Pt(2)
    h=doc.add_paragraph()
    h.alignment=WD_ALIGN_PARAGRAPH.CENTER
    h.paragraph_format.space_after=Pt(3)
    run=h.add_run("RANCANGAN PENGAJARAN HARIAN — SAINS")
    run.bold=True;run.font.size=Pt(12)
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("DRAF SEMAKAN SUMBER • BELUM DILULUSKAN UNTUK PENGGUNA")
    r.bold=True;r.font.size=Pt(8)
    tb=doc.add_table(rows=3,cols=4);tb.style="Table Grid";tb.autofit=False
    meta=[
        ("Tahun","3","PdP",f"{number:03d}"),
        ("Subjek","Sains","Kelas","________________"),
        ("Tarikh","____/____/________","Masa","__:__ – __:__"),
    ]
    for ri,line in enumerate(meta):
        for ci,v in enumerate(line):
            _set_doc_cell(tb.cell(ri,ci),v,bold=ci%2==0)
    details=doc.add_table(rows=5,cols=2);details.style="Table Grid"
    det=[
        ("Unit",unit),
        ("Tajuk",rows["TAJUK"]),
        ("SK / SP",f'{state["sk_code"]}  /  {rows.get("STANDARD PEMBELAJARAN", state["sp_code"])}'),
        ("KPS diintegrasi",skill_summary(rows)),
        ("Objektif / Kriteria",rows["OBJEKTIF PEMBELAJARAN"]+"\n"+rows["KRITERIA KEJAYAAN"]),
    ]
    for ri,(k,v) in enumerate(det):
        _set_doc_cell(details.cell(ri,0),k,True)
        _set_doc_cell(details.cell(ri,1),v)
    phases=doc.add_table(rows=6,cols=2);phases.style="Table Grid"
    for ri,(k,v) in enumerate([
        ("Set induksi",rows["SET INDUKSI"]),
        ("Aktiviti utama",rows["AKTIVITI UTAMA"]),
        ("Penilaian/PBD",rows["PENTAKSIRAN"]),
        ("Buku Aktiviti",rows["BUKU AKTIVITI / LATIHAN"]),
        ("Penutup",rows["PENUTUP"]),
        ("BBM",rows["BAHAN BANTU MENGAJAR"]),
    ]):
        _set_doc_cell(phases.cell(ri,0),k,True)
        _set_doc_cell(phases.cell(ri,1),v)
    p=doc.add_paragraph("Refleksi: "+rows.get("REFLEKSI","__________________"))
    p.paragraph_format.space_before=Pt(2)
    for r in p.runs:r.font.size=Pt(8)
    doc.save(path)
    chk=Document(path)
    if abs(chk.sections[0].page_width.cm-21)>0.05 or abs(chk.sections[0].page_height.cm-29.7)>0.05:
        raise RuntimeError("Incorrect Word page size")
    if len(chk.tables)!=3:
        raise RuntimeError("Word table missing")

def pdf_doc(path,number,unit,state,rows):
    if not Path(FONT).is_file():
        raise FileNotFoundError("DejaVu Unicode font missing")
    if "SainsReview" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("SainsReview",FONT))
    normal=ParagraphStyle("body",fontName="SainsReview",fontSize=8.3,
        leading=11.6,spaceAfter=1)
    strong=ParagraphStyle("label",parent=normal,fontSize=8.0,leading=10)
    heading=ParagraphStyle("heading",parent=normal,fontSize=12,leading=16,
        alignment=1,spaceAfter=3)
    notice=ParagraphStyle("notice",parent=normal,fontSize=7.5,leading=10,
        alignment=1,spaceAfter=5,textColor=colors.darkred)
    def p(value):
        return Paragraph(escape(str(value)).replace("\n","<br/>"),normal)
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=31,rightMargin=31,
        topMargin=29,bottomMargin=26,title=f"Sains Tahun 3 PdP {number:03d} DRAF")
    stack=[Paragraph("RANCANGAN PENGAJARAN HARIAN — SAINS",heading),
           Paragraph("DRAF SEMAKAN SUMBER • BELUM DILULUSKAN UNTUK PENGGUNA",notice)]
    info=[
        [p("Tahun 3"),p("Sains"),p("PdP "+f"{number:03d}"),p("Kelas: __________")],
        [p("Tarikh: ____/____/________"),p("Masa: __:__ – __:__"),p("SK: "+state["sk_code"]),p("SP: "+rows.get("STANDARD PEMBELAJARAN", state["sp_code"]))],
    ]
    t=Table(info,colWidths=[136,125,135,136],hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.4,colors.grey),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    stack.extend([t,Spacer(1,4)])
    fields=[
        ("Unit",unit),
        ("Tajuk",rows["TAJUK"]),
        ("KPS diintegrasi",skill_summary(rows)),
        ("Objektif",rows["OBJEKTIF PEMBELAJARAN"]),
        ("Kriteria kejayaan",rows["KRITERIA KEJAYAAN"]),
        ("Set induksi",rows["SET INDUKSI"]),
        ("Aktiviti utama",rows["AKTIVITI UTAMA"]),
        ("Penilaian/PBD",rows["PENTAKSIRAN"]),
        ("Buku Aktiviti",rows["BUKU AKTIVITI / LATIHAN"]),
        ("Penutup",rows["PENUTUP"]),
        ("BBM / Buku Teks",rows["BAHAN BANTU MENGAJAR"]),
        ("Refleksi","____/____ murid mencapai objektif."),
    ]
    content=[[Paragraph(escape(k),strong),p(v)] for k,v in fields]
    content_width=532
    f=Table(content,colWidths=[105,content_width-105],hAlign="LEFT")
    f.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.33,colors.grey),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),
        ("LEFTPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)
    ]))
    stack.append(f);doc.build(stack)
    pdf=PdfReader(str(path))
    if len(pdf.pages)!=1:
        raise RuntimeError(f"RPH {number} PDF {len(pdf.pages)} pages, expected 1 A4")
    page=pdf.pages[0]
    if abs(float(page.mediabox.width)-A4[0])>2 or abs(float(page.mediabox.height)-A4[1])>2:
        raise RuntimeError("Non-A4 PDF")
    extracted=page.extract_text()
    for required in (state["sp_code"],"Aktiviti 1","Aktiviti 2","PBD"):
        if required not in extracted:
            raise RuntimeError(f"PDF lost content {required} at PdP {number}")

def main():
    import shutil
    if OUTPUT.exists():shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    source,fixes=source_ledgers()
    manifest=[]
    for n in range(1,46):
        code=f"SCI-Y3-PDP-{n:03d}"
        if code not in source:raise RuntimeError("Missing RPH source "+code)
        row=source[code]
        state,fields=sample_rows(row)
        unit=science_unit(state["sp_code"])
        w=OUTPUT/f"SAINS_T3_PDP_{n:03d}_DRAF.docx"
        pdf=OUTPUT/f"SAINS_T3_PDP_{n:03d}_DRAF.pdf"
        word_doc(w,n,unit,state,fields)
        pdf_doc(pdf,n,unit,state,fields)
        manifest.append({
            "pdp":code,"sp":state["sp_code"],"unit":unit,"title":fields["TAJUK"],
            "word_file":w.name,"pdf_file":pdf.name,
            "pdf_a4_one_page":"PASS","docx_a4":"PASS_NO_PAGINATION_PROOF",
            "textbook_source":"CANDIDATE_NOT_VISUALLY_APPROVED",
            "activity_book_ref":fields["BUKU AKTIVITI / LATIHAN"],
            "activity_book_url":fields["BUKU AKTIVITI URL"],
            "activity_book_review_status":"PRINTED_SP_CODE_MATCH__TEACHER_SIGNOFF_PENDING",
            "secondary_sp":next((sp for sp,t in SECONDARY_PBD.items() if t["pdp"]==code),""),
            "secondary_sp_pbd_pdf":next((secondary_stem(sp)+".pdf" for sp,t in SECONDARY_PBD.items() if t["pdp"]==code),""),
            "secondary_sp_pbd_status":"DRAF__NOT_OFFICIAL_BA" if code in {t["pdp"] for t in SECONDARY_PBD.values()} else "",
            "rph_academic_status":"DRAF_NOT_APPROVED",
        })
    with (OUTPUT/"MANIFEST_DRAF.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(manifest[0]))
        writer.writeheader();writer.writerows(manifest)
    (OUTPUT/"README_DRAF.txt").write_text(
        "45 RPH SAINS TAHUN 3 — DRAF SEMAKAN, BUKAN UNTUK PENGGUNA\n"
        "Bahan daripada sumber v25.82, teks DSKP 2017 dan petunjuk BT Tahun 3.\n"
        "PDF disahkan satu halaman A4; DOCX A4 tetapi tidak diuji pagination\n"
        "melalui LibreOffice. 12 tajuk diperbetulkan dalam pratinjau sahaja.\n"
        "Halaman BT calon dan 23 boundary pending; bukan FINAL READY.\n"
        "Tiada DB, akaun, Telegram, Web atau quota berubah.\n",encoding="utf-8")
    print("SAINS_Y3_DRAFT_WORD",45,"PDF_ONE_PAGE_A4",45,
          "TITLE_FIXES",len(fixes),"OUTPUT",OUTPUT)

if __name__=="__main__": main()
