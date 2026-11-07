"""Build 51 Year 2 Sains standalone RPH DRAF in staging from exact old-source IDs.

Never update DB or claim textbook pages, teacher sign-off, 80% or official KP2027.
Reading v25.82 generated review ledger; all original source records preserved.
"""
from __future__ import annotations
import csv
import json
import re
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

from tools.audit_sains_342_pdp_release_gate_20261106 import analyze, ROOT
from web.sains_y2_51_activities_draf_20261107 import BANK
from tools.sains_buku_aktiviti_mapping_20261107 import activity_for, activity_note, activity_short_note, is_direct_sp_match
from tools.render_sains_y2_2_sp_alternative_pbd_20261107 import TASKS as ALT_PBD, doc_file as alt_pbd_doc_file

OUT = ROOT / "build" / "sains_y2_51_rph_DRAF_20261107"
DSKP = "https://drive.google.com/file/d/1rr4CjNvhtI13ioiVSTZi65cvap7j1U6Z/view"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PAGES = ROOT / "audits/sains_y2_51_book_text_page_cues_20261107.json"
KPS = {"1.1.1":"Memerhati", "1.1.2":"Mengelas",
       "1.1.3":"Mengukur dan menggunakan nombor", "1.1.4":"Berkomunikasi"}
Y2_SOURCE_CONFLICTS = {
    "3.1.3": ("Legacy PdP source title is about inheritance, but original DSKP "
              "3.1.3 is 'Mengitlak tumbesaran adalah berbeza antara individu "
              "dengan menjalankan aktiviti'. SP 3.1.4/3.1.5/3.1.6 are not "
              "separate mapped source PdP; requires teacher review."),
    "10.1.6": ("Original KPM DSKP printed text actually says 'campuran' under "
               "10.1 Set Binaan. Teacher-facing lesson focuses on the "
               "construction activity; no silent correction of official wording."),
}
CORRECTED_CANDIDATE_TITLE = {
    "3.1.3": "Manusia — Mengitlak tumbesaran berbeza antara individu berdasarkan data.",
    "10.1.6": "Teknologi — Membentangkan pemerhatian terhadap model set binaan (cadangan).",
}
# The code inventory already verifies exact SP code presence but not semantics.
# Year2-specific KPS is restricted to the four original DSKP process-skill codes.
MEASURE = {"3.1.2","3.1.3","4.1.3","4.1.4","4.1.5","5.1.3",
           "5.1.5","8.1.4"}
CLASSIFY = {"4.1.1","4.1.2","4.1.6","5.1.4","6.1.1","6.1.4",
            "7.1.5","7.1.6","8.1.1","8.1.2","8.1.3","9.1.1","10.1.2"}


def kps_for(sp):
    code = "1.1.3" if sp in MEASURE else "1.1.2" if sp in CLASSIFY else "1.1.1"
    return f"{code} {KPS[code]}; 1.1.4 {KPS['1.1.4']} (cadangan integrasi)"


def book_page_cues():
    data=json.loads(PAGES.read_text(encoding="utf-8"))
    if (data["year"]!=2 or data["status"]!="DRAF_HOLD_TEACHER_VISUAL_REVIEW"
            or data["not_to_be_used_as_certain_pages"] is not True):
        raise ValueError("Year2 book page cues are not approved")
    cues={r["sp"]:r for r in data["items"]}
    if len(cues)!=51 or any(not r["printed_page_candidates"] for r in cues.values()):
        raise ValueError("Year2 book page candidates missing or duplicated")
    return cues


def get_y2_records():
    source, _ = analyze()
    pages=book_page_cues()
    y2 = [r for r in source if r["tahun"] == 2]
    if len(y2) != 51 or {r["sp"] for r in y2} != set(BANK):
        raise ValueError("Year2 Sains source SP set differs from 51 manually authored tasks")
    if [int(r["pdp_number"]) for r in y2] != list(range(1, 52)):
        raise ValueError("Year2 PdP numbering differs from historical baseline")
    result=[]
    for r in y2:
        sp = r["sp"]
        candidate = CORRECTED_CANDIDATE_TITLE.get(sp, r["tajuk"])
        if r["keputusan"] != "HOLD":
            raise ValueError("Readiness status unexpectedly changed")
        result.append({
            **r, **BANK[sp],
            "candidate_title": candidate,
            "kps": kps_for(sp),
            "source_discrepancy": Y2_SOURCE_CONFLICTS.get(sp, ""),
            "book_page_cue": ", ".join(map(str,pages[sp]["printed_page_candidates"])),
            "book_page_status": "TEXT_CUE_ONLY__NOT_VISUALLY_VERIFIED",
            "activity_book": activity_for(2,r["pdp_code"],sp),
            "pbd_alternative":(alt_pbd_doc_file(sp).name if sp in ALT_PBD else ""),
            "quality_score_percent": None,
            "release": "DRAF_HOLD",
        })
    return result


def markdown(item):
    no = int(item["pdp_number"])
    sp = item["sp"]
    caveat = item["source_discrepancy"] or "Semakan halaman buku teks bercetak dan aktiviti asal masih diperlukan."
    return (
        f"# RPH Sains Tahun 2 — PdP {no:03d} (DRAF)\n\n"
        f"**Unit:** {item['unit']}\n"
        f"**Tajuk PdP (cadangan):** {item['candidate_title']}\n"
        f"**SK:** {sp.rsplit('.',1)[0]}\n"
        f"**SP asal sumber:** {sp}\n"
        f"**Rujukan:** DSKP asal Sains Tahun 2; Buku Teks Tahun 2 halaman belum disahkan. "
        f"Petunjuk m/s bercetak: {item['book_page_cue']} (teks PDF, belum disemak secara visual).\n"
        f"**Tempoh:** 60 minit (cadangan; ikut jadual sebenar)\n"
        f"**Objektif:** Murid menghasilkan bukti berikut: {item['pbd']}.\n"
        f"**Kriteria kejayaan/PBD:** {item['pbd']}.\n"
        f"**KPS:** {item['kps']}\n"
        f"**Buku Aktiviti:** {activity_note(item['activity_book'],2,include_url=True)}\n"
        f"**PBD alternatif bukan BA rasmi:** {item['pbd_alternative'] or 'Tidak diperlukan; guru sahkan tugasan BA dahulu.'}\n\n"
        f"**Set induksi (5 minit):** Guru menunjukkan {item['hook'].lower()}. "
        "Murid membuat satu ramalan atau pemerhatian awal.\n\n"
        f"**Aktiviti 1: Penerokaan (18 minit)**\n"
        f"1. Guru {item['teacher1']}.\n"
        f"2. Murid {item['pupil1']}.\n\n"
        f"**Aktiviti 2: Aplikasi (22 minit)**\n"
        f"1. Guru {item['teacher2']}.\n"
        f"2. Murid {item['pupil2']}.\n\n"
        f"**Pengukuhan dan PBD (10 minit):** Guru mengumpul bukti individu: "
        f"{item['pbd']}. Murid menyerahkan jadual, lakaran, respons atau demonstrasi sendiri.\n\n"
        f"**Penutup (5 minit):** Murid menyatakan satu dapatan daripada "
        f"{item['hook'].lower()}; guru merumuskan maksud SP {sp} tanpa "
        "menambah SP rasmi yang tidak dipetakan.\n\n"
        f"**BBM:** {item['materials']}.\n"
        f"**Keselamatan/etika:** {item['safety']}.\n"
        f"**Nota audit (bukan paparan pengguna):** {caveat}\n"
        f"**Status:** DRAF/HOLD — belum disahkan halaman BT, semakan guru dan Telegram/Web sebenar.\n"
    )


def _docx_cell(cell, value, *, strong=False):
    cell.text=""
    p=cell.paragraphs[0]
    p.paragraph_format.space_after=Pt(0)
    parts=str(value).split("\n")
    for i,part in enumerate(parts):
        r=p.add_run(part)
        r.bold=strong
        r.font.size=Pt(7.5)
        if i < len(parts)-1:r.add_break()


def write_docx(path,item):
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Cm(21.0);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(1.0);sec.bottom_margin=Cm(1.0)
    sec.left_margin=Cm(1.2);sec.right_margin=Cm(1.2)
    style=doc.styles["Normal"]
    style.font.name="Arial";style.font.size=Pt(7.7)
    style.paragraph_format.space_after=Pt(0)
    title=doc.add_paragraph()
    title.paragraph_format.space_after=Pt(3)
    r=title.add_run(f"RPH SAINS TAHUN 2 — PdP {int(item['pdp_number']):03d} • DRAF")
    r.bold=True;r.font.size=Pt(11)
    metadata=doc.add_table(rows=3,cols=2);metadata.style="Table Grid"
    for i,(a,b) in enumerate([
        ("Kelas: __________  Tarikh: ____/____/________",
         "Masa: ______ – ______ (60 min cadangan)"),
        (f"Unit: {item['unit']}", f"SK: {item['sp'].rsplit('.',1)[0]}   SP: {item['sp']}"),
        ("Tajuk: "+item["candidate_title"], "KPS: "+item["kps"]),
    ]):
        _docx_cell(metadata.cell(i,0),a)
        _docx_cell(metadata.cell(i,1),b)
    phases=doc.add_table(rows=10,cols=2);phases.style="Table Grid"
    fields=[
      ("Objektif/Kriteria",item["pbd"]),
      ("Set induksi (5m)","Guru menunjukkan "+item["hook"].lower()+". Murid menyatakan pemerhatian."),
      ("Aktiviti 1 (18m)","1. Guru "+item["teacher1"]+".\n2. Murid "+item["pupil1"]+"."),
      ("Aktiviti 2 (22m)","1. Guru "+item["teacher2"]+".\n2. Murid "+item["pupil2"]+"."),
      ("Pengukuhan/PBD (10m)","Guru menilai bukti individu: "+item["pbd"]+"."+
       (" Gunakan lembaran PBD alternatif khusus SP (bukan BA rasmi)." if item["pbd_alternative"] else "")),
      ("Buku Aktiviti/PBD" if is_direct_sp_match(item["activity_book"]) else "BA (rujukan sahaja)",
       activity_short_note(item["activity_book"],2)),
      ("Penutup (5m)","Murid menyatakan satu dapatan; guru merumus kaitan dengan SP "+item["sp"]+"."),
      ("BBM",item["materials"]),
      ("Keselamatan/etika",item["safety"]),
      ("Buku teks / Status",f"Petunjuk m/s {item['book_page_cue']} (belum sah visual) • DRAF/HOLD"),
    ]
    for i,(name,val) in enumerate(fields):
        _docx_cell(phases.cell(i,0),name,strong=True)
        _docx_cell(phases.cell(i,1),val)
    reflection=doc.add_paragraph("Refleksi: ____ / ____ murid mencapai objektif. Tindakan susulan: __________")
    for r in reflection.runs:r.font.size=Pt(7.5)
    doc.save(path)
    chk=Document(path)
    if len(chk.tables)!=2 or abs(chk.sections[0].page_width.cm-21)>0.05:
        raise RuntimeError("DOCX tables or A4 page width missing")
    return True


def write_pdf(path,item):
    if not Path(FONT).is_file():
        raise FileNotFoundError("DejaVu Sans is required for Malay QA PDF")
    if "SainsY2Review" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("SainsY2Review",FONT))
    body=ParagraphStyle("sains_body",fontName="SainsY2Review",fontSize=7.55,
                        leading=10,spaceAfter=0)
    title=ParagraphStyle("sains_title",parent=body,fontSize=10,leading=13,alignment=1)
    def p(value,style=body):
        return Paragraph(escape(str(value)).replace("\n","<br/>"),style)
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=24,rightMargin=24,
                          topMargin=24,bottomMargin=24,
                          title=f"Sains Year2 PdP {item['pdp_number']} DRAF")
    content=[p(f"RPH SAINS TAHUN 2 — PDP {int(item['pdp_number']):03d} • DRAF",title),
             Spacer(1,5)]
    fields=[
      ("Kelas/Tarikh/Masa","________  ____/____/________  ______–______"),
      ("Unit/Tajuk",item["unit"]+" • "+item["candidate_title"]),
      ("SK / SP",item["sp"].rsplit(".",1)[0]+" / "+item["sp"]),
      ("Objektif / Kriteria",item["pbd"]),
      ("KPS",item["kps"]),
      ("Set induksi 5m","Guru menunjukkan "+item["hook"].lower()+". Murid menyatakan pemerhatian."),
      ("Aktiviti 1 18m","1. Guru "+item["teacher1"]+".\n2. Murid "+item["pupil1"]+"."),
      ("Aktiviti 2 22m","1. Guru "+item["teacher2"]+".\n2. Murid "+item["pupil2"]+"."),
      ("Pengukuhan/PBD 10m","Guru menyemak bukti individu: "+item["pbd"]+"."+
       (" Gunakan lembaran PBD alternatif khusus SP (bukan BA rasmi)." if item["pbd_alternative"] else "")),
      ("Buku Aktiviti/PBD" if is_direct_sp_match(item["activity_book"]) else "BA (rujukan sahaja)",
       activity_short_note(item["activity_book"],2)),
      ("Penutup 5m","Murid menyatakan dapatan; guru merumus SP "+item["sp"]+"."),
      ("BBM",item["materials"]),
      ("Keselamatan",item["safety"]),
      ("Rujukan/Status",f"DSKP asal; BT m/s calon {item['book_page_cue']} belum sah visual • DRAF/HOLD"),
      ("Refleksi","____ / ____ murid mencapai objektif."),
    ]
    cells=[[p(a),p(b)] for a,b in fields]
    table=Table(cells,colWidths=[111,432],hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.3,colors.grey),
        ("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))
    content.append(table)
    doc.build(content)
    pdf=PdfReader(str(path))
    if len(pdf.pages)!=1:
        raise RuntimeError(f"Y2 PdP {item['pdp_number']} must be 1 PDF page")
    if abs(float(pdf.pages[0].mediabox.width)-A4[0])>2:
        raise RuntimeError("Non A4 PDF")
    txt=pdf.pages[0].extract_text()
    for needle in ("Aktiviti 1", "Aktiviti 2", "PBD", item["sp"]):
        if needle not in txt:
            raise RuntimeError("PDF missing "+needle)
    return True


def main():
    import shutil
    if OUT.exists():shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    items=get_y2_records()
    report=[]
    for item in items:
        num=int(item["pdp_number"])
        stem=f"SAINS_T2_PDP_{num:03d}_DRAF"
        (OUT/(stem+".md")).write_text(markdown(item),encoding="utf-8")
        write_docx(OUT/(stem+".docx"),item)
        write_pdf(OUT/(stem+".pdf"),item)
        report.append({
            "pdp_code":item["pdp_code"],"sp":item["sp"],
            "source_title":item["tajuk"],"candidate_title":item["candidate_title"],
            "source_conflict":item["source_discrepancy"],
            "book_page_cue":item["book_page_cue"],
            "activity_book_page":item["activity_book"]["workbook_printed_page"],
            "activity_book_pdf_page":item["activity_book"]["workbook_pdf_page"],
            "activity_book_exercise":item["activity_book"]["activity_title"],
            "activity_book_url":item["activity_book"]["workbook_url"],
            "activity_book_status":item["activity_book"]["matching_status"],
            "activity_book_printed_sp_codes":",".join(item["activity_book"]["workbook_printed_sp_codes"]),
            "activity_book_can_be_sp_pbd":False,
            "activity_book_teacher_signoff":"MISSING",
            "pbd_alternative_document":item["pbd_alternative"],
            "pbd_alternative_claims_official_book":False,
            "word_a4":"DOCX_A4_NO_PAGINATION_PROOF",
            "pdf_a4":"ONE_PAGE_PASS",
            "textbook_page":"NOT_VISUALLY_VERIFIED",
            "curriculum_approval":"HOLD",
            "runtime":"STAGING_ONLY",
        })
    with (OUT/"RPH_Y2_51_MANIFEST_DRAF.csv").open(
        "w",newline="",encoding="utf-8-sig") as fp:
        wr=csv.DictWriter(fp,fieldnames=list(report[0]))
        wr.writeheader();wr.writerows(report)
    (OUT/"SOURCE_CONFLICTS_HOLD.json").write_text(json.dumps({
        "year":2,"total_draft_rph":51,"status":"DRAF_HOLD",
        "year1":"KP2027_NOT_MIXED_WITH_KSSR",
        "source":"KPM DSKP Year2 original Drive PDF and v25.82 staged PdP",
        "explicit_source_conflicts":Y2_SOURCE_CONFLICTS,
        "source_sp_3_1_4_through_3_1_6":"NOT_IN_51_SOURCE_PDP",
        "academic_quality_percent":None,
        "ready":False,
        "teacher_book_page_signoff":False,
        "no_runtime_or_db_changes":True,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SCIENCE_Y2_51_DRAFT: 51 distinct source SP, 51 Markdown, "
          "51 DOCX A4, 51 PDF one-page A4; 2 source discrepancies HOLD")


if __name__=="__main__":
    main()
