"""Sains Tahun 5 — 83 source-locked DRAF RPH (Word/PDF/Markdown).

No artificial textbook pages: the original Year5 textbook extract in Drive is partial and not visually validated. Original v25.82 SK/SP/PdP identities are immutable.
No Telegram/Web import, no DB write, no automatic 80% certification.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Cm, Pt
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT, analyze
from web.sains_y5_83_activity_bank_draf_20261107 import BANK
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import checked_book_pages, SHA as BOOK_SOURCE_SHA

OUT = ROOT / "build" / "sains_y5_83_rph_DRAF_20261107"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DSKP_SOURCE = "https://drive.google.com/file/d/1YkiK-pVo4UUzyOUvv_Vrico58eQyddCz/view"
BOOK_SOURCE = "https://drive.google.com/file/d/1m5k8gVkNImT8QEdw6fCEVpQh_tNkUKUT/view"
TEXTBOOK_STATUS = "ORIGINAL_3PART_83_SP_PAGE_TOKENS_VERIFIED__PEDAGOGY_APPROVAL_PENDING"
BOOK_SOURCE_PARTS = (
    "https://drive.google.com/file/d/1m5k8gVkNImT8QEdw6fCEVpQh_tNkUKUT/view",
    "https://drive.google.com/file/d/1xvpW8HgqrTdrl8QJCHUx0pDIiyuBLjIJ/view",
    "https://drive.google.com/file/d/1YnwPPyyLoGCzP_m3izeB_PFn3w7XGsPt/view",
)

KPS = {
    "1.1.1":"Memerhati",
    "1.1.2":"Mengelas",
    "1.1.3":"Mengukur dan menggunakan nombor",
    "1.1.4":"Membuat inferens",
    "1.1.5":"Meramal",
    "1.1.6":"Berkomunikasi",
    "1.1.7":"Menggunakan perhubungan ruang dan masa",
    "1.1.8":"Mentafsir data",
    "1.1.9":"Mendefinisi secara operasi",
    "1.1.10":"Mengawal pemboleh ubah",
    "1.1.11":"Membuat hipotesis",
    "1.1.12":"Mengeksperimen",
}
MEASURE={"5.2.3","5.2.4","5.2.5","6.1.2","6.1.3","6.1.4"}
EXPERIMENT={"5.2.4","5.2.5","6.1.3","7.1.3"}
CLASSIFY={"3.1.2","3.1.3","3.3.2","4.2.1","4.2.2",
          "5.2.1","8.1.2","8.1.3"}
INFER={"2.1.4","2.2.3","2.3.2","3.2.2","3.3.6","6.1.6",
       "7.1.5","10.1.3"}
DATA={"3.3.6","5.3.1","6.1.4","7.1.3","9.1.3"}

def kps_for(sp):
    code=("1.1.12" if sp in EXPERIMENT else
          "1.1.3" if sp in MEASURE else
          "1.1.2" if sp in CLASSIFY else
          "1.1.4" if sp in INFER else
          "1.1.8" if sp in DATA else
          "1.1.1")
    extra="1.1.10 Mengawal pemboleh ubah; " if sp in EXPERIMENT else ""
    return f"{code} {KPS[code]}; {extra}1.1.6 {KPS['1.1.6']} (cadangan aktiviti)"

def get_y5_records():
    rows, summary=analyze()
    selected=[r for r in rows if r["tahun"]==5]
    if len(selected)!=83 or len(BANK)!=83:
        raise ValueError("Year5 source count and activity bank no longer agree")
    if [int(r["pdp_number"]) for r in selected]!=list(range(1,84)):
        raise ValueError("Year5 source sequence changed")
    if {r["sp"] for r in selected}!=set(BANK):
        missing={r["sp"] for r in selected}-set(BANK)
        extra=set(BANK)-{r["sp"] for r in selected}
        raise ValueError(f"Year5 DSKP SP mismatch missing={missing} extra={extra}")
    if summary["decision"]!="HOLD":
        raise ValueError("Source audit release gate unexpectedly lifted")
    textbook=checked_book_pages()
    result=[]
    for row in selected:
        if row["keputusan"]!="HOLD":
            raise ValueError("Unapproved source treated as ready")
        book=textbook.get(row["sp"])
        if (not book or book["teacher_academic_approved"] is not False
            or book["page_sp_evidence"]!="ORIGINAL_PDF_TEXT_HAS_EXACT_SP_TOKEN"):
            raise ValueError("Year5 SP source page cannot be verified: "+row["pdp_code"])
        result.append({
            **row, **BANK[row["sp"]],
            "kps":kps_for(row["sp"]),
            "subject":"Sains",
            "year":5,
            "curriculum_quality_percent":None,
            "textbook_pages":book["printed_pages"],
            "textbook_page_primary":book["primary_page"],
            "textbook_reference_status":"83_SP_PRINTED_TEXT_LABEL_MATCH__ACTIVITY_CONTENT_TEACHER_HOLD",
            "status":"DRAF_HOLD",
        })
    return result


def markdown(item):
    sp=item["sp"]
    return (
        f"# RPH Sains Tahun 5 — PdP {int(item['pdp_number']):03d} (DRAF/HOLD)\n\n"
        f"**Unit:** {item['unit']}\n"
        f"**Tajuk:** {item['tajuk']}\n"
        f"**SK:** {item['sk']}\n"
        f"**SP:** {sp}\n"
        f"**Rujukan:** DSKP Sains Tahun 5 KSSR Semakan 2017; Buku Teks SK 2020 m/s "
        f"{', '.join(map(str,item['textbook_pages']))} (kod SP didapati dalam tiga bahagian "
        "PDF buku asal; kesesuaian isi dan PBD belum disahkan panitia).\n"
        "**Tempoh cadangan:** 60 minit (ikut jadual sebenar)\n"
        f"**Objektif dan kriteria kejayaan:** {item['pbd']}.\n"
        f"**KPS diintegrasi:** {item['kps']}\n\n"
        f"**Set induksi (5 minit):** Guru menunjukkan {item['hook'].lower()}. "
        "Murid menyatakan satu idea awal.\n\n"
        f"**Aktiviti 1: Penerokaan (18 minit)**\n"
        f"1. Guru {item['teacher1']}.\n"
        f"2. Murid {item['pupil1']}.\n\n"
        f"**Aktiviti 2: Aplikasi (22 minit)**\n"
        f"1. Guru {item['teacher2']}.\n"
        f"2. Murid {item['pupil2']}.\n\n"
        f"**Pengukuhan / PBD (10 minit):** Guru menyemak secara individu: "
        f"{item['pbd']}. Murid menyerahkan bukti pemerhatian, jadual, model "
        "atau penjelasan mengikut hasil PdP.\n\n"
        f"**Penutup (5 minit):** Murid menyatakan dapatan; guru merumus kaitannya "
        f"dengan SP {sp}.\n"
        f"**BBM:** {item['materials']}.\n"
        f"**Keselamatan / etika:** {item['safety']}.\n"
        "**Refleksi:** ____ / ____ murid mencapai kriteria; tindakan susulan: ______.\n"
        "**Status:** DRAF/HOLD — belum lulus buku teks, akademik, Web/Telegram.\n"
    )


def _cell(cell, text, bold=False):
    cell.text=""
    paragraph=cell.paragraphs[0]
    paragraph.paragraph_format.space_after=Pt(0)
    for index, line in enumerate(str(text).split("\n")):
        run=paragraph.add_run(line)
        run.bold=bold
        run.font.size=Pt(8.15)
        if index<len(str(text).split("\n"))-1:run.add_break()


def word_doc(path,item):
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(0.9);sec.bottom_margin=Cm(0.9)
    sec.left_margin=Cm(1.1);sec.right_margin=Cm(1.1)
    normal=doc.styles["Normal"]
    normal.font.name="Arial";normal.font.size=Pt(8.15)
    normal.paragraph_format.space_after=Pt(0)
    headline=doc.add_paragraph()
    headline.paragraph_format.space_after=Pt(3)
    rr=headline.add_run(f"RPH SAINS TAHUN 5 — PdP {int(item['pdp_number']):03d} • DRAF")
    rr.bold=True;rr.font.size=Pt(11)
    meta=doc.add_table(rows=3,cols=2)
    meta.style="Table Grid"
    for i,(left,right) in enumerate([
       ("Kelas: __________ Tarikh: ____/____/________", "Masa: ______–______ (cadangan 60 min)"),
       (item["unit"],f"SK {item['sk']}   SP {item['sp']}"),
       ("Tajuk: "+item["tajuk"],"KPS: "+item["kps"]),
    ]):
        _cell(meta.cell(i,0),left);_cell(meta.cell(i,1),right)
    phases=doc.add_table(rows=9,cols=2);phases.style="Table Grid"
    fields=[
      ("Objektif/Kriteria",item["pbd"]),
      ("Set induksi (5m)","Guru menunjukkan "+item["hook"].lower()+". Murid menyatakan pemerhatian/ramalan."),
      ("Aktiviti 1 (18m)","1. Guru "+item["teacher1"]+".\n2. Murid "+item["pupil1"]+"."),
      ("Aktiviti 2 (22m)","1. Guru "+item["teacher2"]+".\n2. Murid "+item["pupil2"]+"."),
      ("Pengukuhan/PBD (10m)","Guru menilai bukti individu: "+item["pbd"]+"."),
      ("Penutup (5m)","Murid menyatakan dapatan; guru merumus SP "+item["sp"]+"."),
      ("BBM",item["materials"]),
      ("Keselamatan",item["safety"]),
      ("Buku teks/Status",f"BT m/s {item['textbook_page_primary']} (label SP pada buku asal disemak; isi/PBD tunggu panitia) • DRAF/HOLD"),
    ]
    for i,(label,body) in enumerate(fields):
        _cell(phases.cell(i,0),label,bold=True)
        _cell(phases.cell(i,1),body)
    p=doc.add_paragraph("Refleksi: ____/____ murid mencapai objektif. Susulan: ____________________")
    for run in p.runs:run.font.size=Pt(8)
    doc.save(path)
    verify=Document(path)
    if len(verify.tables)!=2 or abs(verify.sections[0].page_width.cm-21)>0.05:
        raise RuntimeError("Year5 Word A4/table integrity failure")


def pdf_doc(path,item):
    if not Path(FONT).exists():
        raise RuntimeError("Unicode Malay font unavailable")
    if "SainsYear5" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("SainsYear5",FONT))
    if "SainsYear5Bold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("SainsYear5Bold",BOLD_FONT))
    body=ParagraphStyle("y5_body",fontName="SainsYear5",fontSize=8.5,leading=12.1)
    label=ParagraphStyle("y5_label",parent=body,fontName="SainsYear5Bold",
                         fontSize=8.3,leading=12)
    headline=ParagraphStyle("y5_headline",parent=body,fontSize=13,leading=16,
                             alignment=1,spaceAfter=5)
    def p(v,style=body):
        return Paragraph(escape(str(v)).replace("\n","<br/>"),style)
    fields=[
      ("Kelas/Tarikh/Masa","___________    ____/____/________    _____–_____"),
      ("Unit",item["unit"]),
      ("Tajuk",item["tajuk"]),
      ("SK / SP",item["sk"]+" / "+item["sp"]),
      ("Objektif/Kriteria",item["pbd"]),
      ("KPS",item["kps"]),
      ("Set induksi 5m","Guru menunjukkan "+item["hook"].lower()+". Murid menyatakan satu idea."),
      ("Aktiviti 1 18m","1. Guru "+item["teacher1"]+".\n2. Murid "+item["pupil1"]+"."),
      ("Aktiviti 2 22m","1. Guru "+item["teacher2"]+".\n2. Murid "+item["pupil2"]+"."),
      ("Pengukuhan/PBD 10m","Bukti individu: "+item["pbd"]+"."),
      ("Penutup 5m","Murid menyatakan dapatan; guru merumus SP "+item["sp"]+"."),
      ("BBM",item["materials"]),
      ("Keselamatan",item["safety"]),
      ("Rujukan/Status",f"DSKP KPM; BT m/s {item['textbook_page_primary']} (kod SP buku disemak; isi/PBD belum sah panitia) • DRAF/HOLD"),
      ("Refleksi","____/____ murid mencapai objektif."),
    ]
    rows=[[p(k,label),p(v)] for k,v in fields]
    tbl=Table(rows,colWidths=[117,426],hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.27,colors.grey),
        ("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),4.8),
        ("BOTTOMPADDING",(0,0),(-1,-1),4.8),
    ]))
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=24,rightMargin=24,
                          topMargin=24,bottomMargin=24,
                          title="Science Year5 RPH staged review")
    doc.build([p(f"RPH SAINS TAHUN 5 — PDP {int(item['pdp_number']):03d} • DRAF",headline),
               Spacer(1,7),tbl])
    pdf=PdfReader(str(path))
    if len(pdf.pages)!=1:
        raise RuntimeError("Year5 PDF overflow "+item["pdp_code"]+" : "+str(len(pdf.pages)))
    box=pdf.pages[0].mediabox
    if abs(float(box.width)-A4[0])>2 or abs(float(box.height)-A4[1])>2:
        raise RuntimeError("Year5 PDF non-A4 "+item["pdp_code"])
    extracted=pdf.pages[0].extract_text()
    for key in ("Aktiviti 1","Aktiviti 2","PBD",item["sp"]):
        if key not in extracted:
            raise RuntimeError("Year5 PDF lost "+key+" in "+item["pdp_code"])


def main():
    import shutil
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    records=get_y5_records()
    manifest=[]
    for entry in records:
        n=int(entry["pdp_number"])
        stem=f"SAINS_T5_PDP_{n:03d}_DRAF"
        (OUT/(stem+".md")).write_text(markdown(entry),encoding="utf-8")
        word_doc(OUT/(stem+".docx"),entry)
        pdf_doc(OUT/(stem+".pdf"),entry)
        manifest.append({
            "pdp_code":entry["pdp_code"],"sk":entry["sk"],"sp":entry["sp"],
            "unit":entry["unit"],"title":entry["tajuk"],
            "word_file":stem+".docx","pdf_file":stem+".pdf",
            "pdf_one_page_a4":"PASS","word_a4":"SIZE_PASS__PRINT_PAGE_COUNT_PENDING",
            "dsKP_source":"TEXT_TOKEN_VERIFIED_NOT_FULL_SP_SEMANTICS",
            "textbook_pages":",".join(map(str,entry["textbook_pages"])),
            "textbook_primary_page":entry["textbook_page_primary"],
            "textbook_sp_code_source_status":entry["textbook_reference_status"],
            "textbook_source_sha256_parts":";".join(BOOK_SOURCE_SHA),
            "lesson_activities":"SOURCE_SPECIFIC_DRAFT",
            "academic_score": "NOT_CERTIFIED",
            "release":"HOLD",
        })
    with (OUT/"SAINS_Y5_83_MANIFEST_DRAF.csv").open(
        "w",newline="",encoding="utf-8-sig") as fp:
        writer=csv.DictWriter(fp,fieldnames=list(manifest[0]))
        writer.writeheader();writer.writerows(manifest)
    (OUT/"QUALITY_GATE_HOLD.json").write_text(json.dumps({
        "source":"v25.82 staged read-only ledger + original Year5 DSKP",
        "dsKP_url":DSKP_SOURCE,"original_book_url":BOOK_SOURCE,
        "original_book_3_part_urls":BOOK_SOURCE_PARTS,
        "original_book_3_part_sha256":BOOK_SOURCE_SHA,
        "original_book_status":TEXTBOOK_STATUS,
        "year":5,"pdp":len(records),"docx":len(records),"pdf":len(records),
        "markdown":len(records),"status":"DRAF/HOLD",
        "academic_quality_percent":None,"approved_by_teacher":False,
        "source_page_code_evidence_verified_count":83,
        "source_page_reference_verified":False,  # full pedagogical page suitability still HOLD
        "source_pedagogical_matching_approved":False,"native_telegram_web_e2e":False,
        "no_production_db_or_runtime_write":True,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_T5_83_DRAF: 83 source-locked RPH; 83 Markdown + 83 Word A4 "
          "+ 83 PDF A4 single page; 83 original book SP code/page refs checked; academic HOLD")


if __name__=="__main__":
    main()
