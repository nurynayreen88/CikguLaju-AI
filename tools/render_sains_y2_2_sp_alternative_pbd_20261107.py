"""Create two ORIGINAL SP-specific individual PBD sheets where Sains Y2 activity
books have only related, different-SP exercises. Staging HOLD only.

Official Year2 DSKP language verified in original KPM PDF. This is not
a workbook page, and its printouts must never be advertised as KPM book.
No AI API calls, DB writes, Telegram/Web production or false approvals.
"""
from __future__ import annotations
import csv
import json
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from pypdf import PdfReader

from tools.sains_buku_aktiviti_mapping_20261107 import ROOT, activity_for, is_direct_sp_match

OUT=ROOT/"build/sains_y2_2_alternative_sp_pbd_DRAF_20261107"
DSKP_URL="https://drive.google.com/file/d/1rr4CjNvhtI13ioiVSTZi65cvap7j1U6Z/view"
TASKS={
 "4.1.7":{
  "pdp":"SCI-Y2-PDP-010",
  "sp_text":"Menjelaskan pemerhatian tentang pembiakan dan tumbesaran melalui lakaran, TMK, penulisan atau lisan.",
  "title":"Kitar Hidup dan Tumbesaran Haiwan — Saya Boleh Menjelaskan",
  "prep":"Guru sediakan empat kad gambar jelas: telur rama-rama, ulat, pupa dan rama-rama dewasa; serta satu contoh gambar anak-induk haiwan lain.",
  "question1":"Susun dan lakar EMPAT peringkat kitar hidup rama-rama menggunakan gambar guru. Tulis satu label di setiap kotak.",
  "question2":"Tulis DUA perubahan yang boleh diperhatikan daripada anak haiwan kepada haiwan dewasa. Gunakan bukti daripada lakaran kamu.",
  "question3":"Ceritakan kepada guru SATU pemerhatian tentang cara haiwan membiak atau membesar. Terangkan bukti daripada gambar. Guru catat jawapan lisan jika murid memilih kaedah lisan.",
  "criteria":[
    "Empat peringkat tumbesaran tersusun dan berlabel munasabah",
    "Dua pemerhatian perubahan disokong gambar/lakaran",
    "Murid sendiri menjelaskan satu dapatan dengan bukti, secara lisan atau bertulis",
  ],
  "safe":"Gunakan kad gambar; tidak perlu mengendalikan haiwan hidup. Jangan meminta kisah pembiakan keluarga murid.",
  "related_page":27,
  "related_sp":"4.1.5",
 },
 "6.1.6":{
  "pdp":"SCI-Y2-PDP-022",
  "sp_text":"Menjelaskan pemerhatian tentang terang dan gelap melalui lakaran, TMK, penulisan atau lisan.",
  "title":"Terang, Gelap dan Bayang-bayang — Pemerhatian Saya",
  "prep":"Guru tunjuk gambar/rajah sumber cahaya, objek legap dan dinding; tunjuk keadaan lampu menyala dan padam tanpa memancar ke mata.",
  "question1":"Lakar DUA keadaan objek di hadapan dinding: (A) lampu suluh menyala dan (B) lampu suluh padam. Tandakan bahagian yang terang, gelap dan sebarang bayang-bayang yang kelihatan.",
  "question2":"Tulis DUA pemerhatian yang berbeza apabila lampu menyala berbanding apabila lampu padam. Jelaskan kaitannya dengan cahaya yang sampai ke objek atau dinding.",
  "question3":"Terangkan secara lisan/bertulis MENGAPA bayang-bayang terbentuk apabila cahaya dihalang oleh objek legap. Guru catat jawapan lisan jika dipilih.",
  "criteria":[
    "Dua lakaran membezakan keadaan terang dan gelap dengan betul",
    "Dua pemerhatian terang/gelap dinyatakan dengan bukti",
    "Murid sendiri menjelaskan kaitan sumber cahaya, halangan dan bayang",
  ],
  "safe":"Gunakan lampu suluh kuasa rendah atau gambar; jangan menghalakan cahaya ke mata. Bukan eksperimen elektrik soket rumah.",
  "related_page":44,
  "related_sp":"6.1.5",
 }
}

def safe_code(sp):
    return sp.replace(".","_")

def doc_file(sp):
    row=TASKS[sp]
    return OUT/f"SAINS_T2_PDP_{int(row['pdp'][-3:]):03d}_SP_{safe_code(sp)}_PBD_ALTERNATIF_DRAF.docx"

def build_sheet(sp):
    task=TASKS[sp]
    ba=activity_for(2,task["pdp"],sp)
    if is_direct_sp_match(ba):
        raise RuntimeError("Alternative PBD only for unmatched exact-SP activity book")
    if ba["workbook_printed_page"]!=task["related_page"] or ba["workbook_printed_sp_codes"]!=[task["related_sp"]]:
        raise RuntimeError("Changed source book: do not quietly reuse alternative PBD")
    OUT.mkdir(parents=True,exist_ok=True)
    doc=Document()
    section=doc.sections[0]
    section.page_width=Cm(21);section.page_height=Cm(29.7)
    section.top_margin=Cm(1.1);section.bottom_margin=Cm(1.1)
    section.left_margin=Cm(1.25);section.right_margin=Cm(1.25)
    normal=doc.styles["Normal"]
    normal.font.name="Arial";normal.font.size=Pt(9)
    normal.paragraph_format.space_after=Pt(3)
    title=doc.add_paragraph()
    title.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=title.add_run("SAINS TAHUN 2 — BUKTI PBD INDIVIDU")
    run.bold=True;run.font.size=Pt(13)
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("TUGASAN ALTERNATIF DRAF • BUKAN LATIHAN BUKU AKTIVITI RASMI")
    r.bold=True;r.font.size=Pt(8)
    t=doc.add_table(rows=2,cols=2);t.style="Table Grid"
    t.cell(0,0).text="Nama murid: __________________________"
    t.cell(0,1).text="Kelas: __________  Tarikh: ____/____/______"
    t.cell(1,0).text=f"PdP: {task['pdp']}   SP: {sp}"
    t.cell(1,1).text="Kaedah bukti: Lakaran / Tulisan / Lisan"
    h=doc.add_paragraph()
    r=h.add_run(task["title"]);r.bold=True;r.font.size=Pt(11)
    p=doc.add_paragraph()
    r=p.add_run("SP DSKP: ");r.bold=True
    p.add_run(task["sp_text"])
    p=doc.add_paragraph()
    r=p.add_run("Persediaan guru: ");r.bold=True
    p.add_run(task["prep"])
    for number,key in ((1,"question1"),(2,"question2"),(3,"question3")):
        p=doc.add_paragraph()
        rr=p.add_run(f"Aktiviti {number} — ");rr.bold=True
        p.add_run(task[key])
        if number==1:
            grid=doc.add_table(rows=1,cols=4 if sp=="4.1.7" else 2)
            grid.style="Table Grid"
            for i,cell in enumerate(grid.rows[0].cells):
                cell.text=f"{chr(65+i)}"+("\n"*16)
        elif number==2:
            for i in range(2):
                p=doc.add_paragraph(f"{i+1}. __________________________________________________________________________")
                p.paragraph_format.space_after=Pt(1)
                extra=doc.add_paragraph("     __________________________________________________________________________")
                extra.paragraph_format.space_after=Pt(2)
        else:
            p=doc.add_paragraph("Jawapan/rekod lisan murid: ______________________________________________________")
            p.paragraph_format.space_after=Pt(1)
    p=doc.add_paragraph()
    r=p.add_run("Rekod PBD oleh guru (tandakan): ");r.bold=True
    for i,criterion in enumerate(task["criteria"],1):
        p=doc.add_paragraph(f"☐ {i}. {criterion}")
        p.paragraph_format.space_after=Pt(1)
    p=doc.add_paragraph()
    rr=p.add_run("Keselamatan: ");rr.bold=True
    p.add_run(task["safe"])
    p=doc.add_paragraph()
    p.add_run(f"BA Sains T2 m/s {task['related_page']} berlabel SP {task['related_sp']}, "
                f"BUKAN SP {sp}; rujukan berkaitan sahaja, tidak dinilai sebagai PBD SP {sp}.").italic=True
    p=doc.add_paragraph()
    rr=p.add_run("Status: DRAF/HOLD • belum disahkan guru/panitia. ");rr.bold=True
    p.add_run("Sumber SP: DSKP Sains Tahun 2 KSSR Semakan 2017.")
    path=doc_file(sp)
    doc.save(path)
    check=Document(path)
    if len(check.tables)!=2 or abs(check.sections[0].page_width.cm-21)>0.05:
        raise RuntimeError("PBD Word A4/table validation failed")
    return path

def build():
    exe=shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:raise RuntimeError("LibreOffice required for actual one-page print QA")
    docs=[build_sheet(sp) for sp in TASKS]
    profile="file:///tmp/cikgulaju_sains_y2_unmatched_sp_pbd_20261107"
    command=[exe,f"-env:UserInstallation={profile}","--headless","--convert-to",
             "pdf","--outdir",str(OUT),*[str(x) for x in docs]]
    proc=subprocess.run(command,text=True,capture_output=True,timeout=150)
    if proc.returncode!=0:
        raise RuntimeError("LibreOffice export failed: "+proc.stderr[-1500:])
    manifest=[]
    for sp,p in zip(TASKS,docs):
        pdf=p.with_suffix(".pdf")
        if not pdf.exists():raise RuntimeError("Missing rendered PDF "+str(pdf))
        reader=PdfReader(str(pdf))
        if len(reader.pages)!=1:raise RuntimeError("PBD PDF not one A4 page: "+sp)
        page=reader.pages[0]
        if abs(float(page.mediabox.width)-595.28)>2 or abs(float(page.mediabox.height)-841.89)>2:
            raise RuntimeError("Wrong PDF page size "+sp)
        content=page.extract_text()
        for need in (sp,"BUKAN LATIHAN BUKU AKTIVITI RASMI","Aktiviti 1",
                     "Aktiviti 2","Aktiviti 3","Rekod PBD","DRAF/HOLD"):
            if need not in content:raise RuntimeError("PDF lost text "+sp+" "+need)
        t=TASKS[sp]
        manifest.append({
            "pdp_code":t["pdp"],"sp":sp,
            "official_sp_from_original_kpm_dskp":t["sp_text"],
            "document_type":"ORIGINAL_SCIENCE_PBD_ALTERNATIVE_NOT_OFFICIAL_BA",
            "document_word":p.name,"document_pdf":pdf.name,
            "related_activity_book_printed_page":t["related_page"],
            "related_activity_book_sp":t["related_sp"],
            "related_activity_book_as_sp_pbd":"NO",
            "word_printed_a4_one_page":"PASS","pdf_a4_one_page":"PASS",
            "teacher_academic_approved":False,"live_runtime":False,"status":"DRAF_HOLD"
        })
    with (OUT/"PBD_ALTERNATIF_T2_DUA_SP_HOLD.csv").open(
        "w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(manifest[0]))
        w.writeheader();w.writerows(manifest)
    (OUT/"PBD_ALTERNATIF_T2_DUA_SP_HOLD.json").write_text(
        json.dumps({"total":2,"exact_sp":["4.1.7","6.1.6"],
        "official_dskp_source":DSKP_URL,
        "academic_approval":False,"ready":False,"runtime_enabled":False,
        "worksheet_official_claim":False,"manifest":manifest},indent=2,
        ensure_ascii=False)+"\n",encoding="utf-8")
    print("YEAR2_ALTERNATIVE_PBD: 2/2 original SP-specific Word and PDF one A4 page, STAGING HOLD")
    return manifest

if __name__=="__main__":
    build()
