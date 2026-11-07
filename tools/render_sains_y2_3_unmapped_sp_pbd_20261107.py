"""Three ORIGINAL supplementary Sains Year2 Unit3 SP-PBD sheets.

Source KPM DSKP SP3.1.4/3.1.5/3.1.6 are absent as standalone
curriculum source PdP in original 51-PdP v25.82 roster. These do NOT
create or claim new official PdP numbers, official KPM workbook pages,
teacher signoff, or use in Telegram/Web production. All STAGING HOLD.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pypdf import PdfReader

from tools.sains_buku_aktiviti_mapping_20261107 import ROOT
from web.sains_y2_51_activities_draf_20261107 import BANK

SOURCE=ROOT/"audits/sains_y2_unit3_unmapped_sp_semantic_20261107.json"
INVENTORY=ROOT/"audits/sains_dskp_t2_t5_sp_token_inventory_20261106.json"
OUT=ROOT/"build/sains_y2_unit3_3_supplementary_sp_pbd_DRAF_20261107"

TASKS={
 "3.1.4":{
  "title":"Pewarisan Ciri — Memerihalkan Pemerhatian",
  "setup":"Guru sediakan dua kad keluarga REKAAN dengan watak ibu, bapa dan anak. Kad A: ibu rambut ikal, bapa rambut lurus, anak rambut ikal. Kad B: ibu rambut lurus, bapa rambut ikal, anak rambut lurus.",
  "task1":"Catat jenis rambut ibu, bapa dan anak bagi Kad A dan Kad B. Nyatakan DUA persamaan atau perbezaan daripada kad.",
  "task2":"Lengkapkan ayat: 'Sesetengah ciri anak boleh diwarisi daripada ______ atau ______.' Terangkan dengan SATU contoh yang kamu pilih daripada kad.",
  "task3":"Beri satu sebab mengapa kita TIDAK boleh menentukan hubungan keluarga sebenar hanya daripada rupa atau jenis rambut.",
  "criteria":["Dua pemerhatian tepat daripada kad rekaan","Penjelasan bahawa ciri boleh diwarisi daripada ibu/bapa/keturunan","Tidak menganggap ciri fizikal tunggal sebagai bukti hubungan keluarga"],
  "safety":"Kad dan nama semuanya rekaan. Jangan menyoal ibu bapa kandung, asal usul, warna kulit atau sejarah keluarga murid.",
 },
 "3.1.5":{
  "title":"Contoh Ciri yang Boleh Diwarisi",
  "setup":"Guru paparkan kad rekaan berlabel jenis rambut (lurus/ikal), warna mata (coklat/gelap) dan ciri rupa mudah. Tidak membuat perbandingan rupa murid sebenar.",
  "task1":"Daripada kad rekaan, tulis TIGA contoh ciri yang boleh diwarisi daripada ibu, bapa atau keturunan.",
  "task2":"Pilih DUA contoh tadi dan nyatakan bagaimana ciri itu kelihatan dalam keluarga rekaan. Gunakan ayat 'boleh diwarisi', bukan 'mesti sama'.",
  "task3":"Tandakan pernyataan yang wajar: 'Adik-beradik sentiasa mempunyai rupa yang sama' (YA/TIDAK). Beri alasan.",
  "criteria":["Tiga contoh ciri warisan yang relevan dengan DSKP","Dua pemerhatian daripada kad, tanpa mendakwa semua anak mesti sama","Satu alasan bahawa ciri keluarga boleh berbeza antara individu"],
  "safety":"Elakkan ramalan keturunan, identiti keluarga, warna kulit atau pemeriksaan rupa murid dalam kelas.",
 },
 "3.1.6":{
  "title":"Menjelaskan Tumbesaran dan Pewarisan",
  "setup":"Watak rekaan: Ali mempunyai tinggi 98 cm ketika umur 4 tahun dan 118 cm ketika umur 7 tahun. Dalam kad keluarga rekaan, Ali dan ibunya kedua-duanya berambut ikal.",
  "task1":"Lakar atau tulis perubahan tinggi Ali daripada umur 4 tahun ke umur 7 tahun berdasarkan data contoh. Kira perbezaan tinggi.",
  "task2":"Nyatakan satu pemerhatian tentang ciri rambut dalam kad keluarga rekaan. Bezakan ciri itu daripada perubahan tinggi Ali.",
  "task3":"Jelaskan DUA dapatan kamu kepada guru: satu tentang TUMBESARAN dan satu tentang PEWARISAN. Boleh gunakan lakaran, tulisan atau lisan.",
  "criteria":["Bukti tumbesaran daripada data ukuran rekaan dengan unit betul","Pemerhatian ciri keluarga daripada kad rekaan","Penjelasan individu membezakan tumbesaran dengan pewarisan"],
  "safety":"Data ukuran dan keluarga adalah rekaan. Jangan ukur tubuh atau meminta maklumat keluarga sebenar murid.",
 }
}

def load_semantics():
    doc=json.loads(SOURCE.read_text(encoding="utf-8"))
    codes={x["sp"] for x in doc["missing_content_sp"]}
    inventory=json.loads(INVENTORY.read_text(encoding="utf-8"))
    original_year2=set(inventory["years"]["2"]["sp_tokens"])
    if (doc["status"]!="STAGING_HOLD__TEACHER_PANITIA_APPROVAL_PENDING"
        or doc["teacher_approved"] is not False
        or doc["no_new_official_pdp_ids"] is not True
        or codes!=set(TASKS)
        or not codes.issubset(original_year2)
        or codes.intersection(BANK)
        or len(BANK)!=51):
        raise ValueError("Unverified source Year2 Unit3 SP gap; refuse generation")
    for rec in doc["missing_content_sp"]:
        if (rec["scheduled_pdp"] is not None or rec["sk"]!="3.1"
            or rec["staging_action"]!="SUPPLEMENTARY_ORIGINAL_PBD_NOT_AN_OFFICIAL_NEW_PDP"):
            raise ValueError("Unapproved fictitious source/PdP for "+rec["sp"])
    conflicts={x["sp"]:x for x in doc["source_conflicts"]}
    if set(conflicts)!={"3.1.3","10.1.6"}:
        raise ValueError("Official source conflicts must stay visible")
    if ("campuran" not in conflicts["10.1.6"]["printed_dskp_text"]
        or "tumbesaran" not in conflicts["3.1.3"]["printed_dskp_text"]):
        raise ValueError("Official printed DSKP discrepancy silently rewritten")
    return {x["sp"]:x for x in doc["missing_content_sp"]}

def doc_path(sp):
    return OUT/f"SAINS_T2_SP_{sp.replace('.','_')}_PBD_SOKONGAN_BUKAN_PDP_RASMI_DRAF.docx"

def make_doc(sp,official):
    task=TASKS[sp]
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.top_margin=Cm(1.1);sec.bottom_margin=Cm(1.1)
    sec.left_margin=Cm(1.2);sec.right_margin=Cm(1.2)
    normal=doc.styles["Normal"]
    normal.font.name="Arial";normal.font.size=Pt(9)
    normal.paragraph_format.space_after=Pt(4)
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("SAINS TAHUN 2 | PBD SOKONGAN UNIT 3")
    r.bold=True;r.font.size=Pt(12)
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("DRAF CIKGULAJU — BUKAN PDP BAHARU / BUKAN BUKU AKTIVITI KPM")
    r.bold=True;r.font.size=Pt(8)
    t=doc.add_table(rows=2,cols=2);t.style="Table Grid"
    t.cell(0,0).text="Nama: _________________________"
    t.cell(0,1).text="Kelas: __________ Tarikh: ____/____/______"
    t.cell(1,0).text=f"SK 3.1  |  SP {sp}"
    t.cell(1,1).text="Pilihan bukti: tulisan / lakaran / lisan"
    p=doc.add_paragraph()
    rr=p.add_run(task["title"]);rr.bold=True;rr.font.size=Pt(11)
    p=doc.add_paragraph()
    rr=p.add_run("Penyataan SP DSKP asal: ");rr.bold=True;p.add_run(official["official_dskp_text"])
    p=doc.add_paragraph()
    rr=p.add_run("Situasi daripada kad guru: ");rr.bold=True;p.add_run(task["setup"])
    for i in (1,2,3):
        p=doc.add_paragraph()
        rr=p.add_run(f"Aktiviti {i}: ");rr.bold=True
        p.add_run(task[f"task{i}"])
        if i==1:
            grid=doc.add_table(rows=1,cols=2)
            grid.style="Table Grid"
            for col,cell in enumerate(grid.rows[0].cells,1):
                cell.text=f"Catatan / lakaran {col}:\n"+("\n"*7)
        else:
            p=doc.add_paragraph("Jawapan: __________________________________________________________")
            p.paragraph_format.space_after=Pt(1)
            p=doc.add_paragraph("_________________________________________________________________")
            p.paragraph_format.space_after=Pt(1)
    p=doc.add_paragraph()
    rr=p.add_run("Semakan bukti PBD individu oleh guru: ");rr.bold=True
    for criterion in task["criteria"]:
        p=doc.add_paragraph("☐ "+criterion)
        p.paragraph_format.space_after=Pt(0)
    p=doc.add_paragraph()
    rr=p.add_run("Etika/keselamatan: ");rr.bold=True;p.add_run(task["safety"])
    p=doc.add_paragraph()
    rr=p.add_run("Status: ");rr.bold=True
    p.add_run("DRAF/HOLD; SP wujud dalam DSKP tetapi belum dipetakan kepada PdP rasmi dalam 51 sumber asal. Guru/panitia mesti memutuskan sesi dan kesesuaian.")
    path=doc_path(sp);path.parent.mkdir(parents=True,exist_ok=True);doc.save(path)
    check=Document(path)
    if len(check.tables)!=2 or abs(check.sections[0].page_width.cm-21)>0.05:
        raise RuntimeError("DOCX structural A4 invalid "+sp)
    return path

def build():
    sem=load_semantics()
    exe=shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:raise RuntimeError("LibreOffice is required for real Word print QA")
    docs=[make_doc(sp,sem[sp]) for sp in sorted(TASKS)]
    cmd=[exe,"-env:UserInstallation=file:///tmp/cikgulaju_year2_3_unmapped_sp",
         "--headless","--convert-to","pdf","--outdir",str(OUT),*[str(x) for x in docs]]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=160)
    if result.returncode!=0:
        raise RuntimeError("LibreOffice failed: "+result.stderr[-1000:])
    manifest=[]
    for sp,word in zip(sorted(TASKS),docs):
        pdf=word.with_suffix(".pdf")
        if not pdf.exists():raise RuntimeError("PDF not generated "+sp)
        reader=PdfReader(str(pdf))
        if len(reader.pages)!=1:raise RuntimeError("Supplement SP "+sp+" overflowed A4")
        page=reader.pages[0]
        if abs(float(page.mediabox.width)-595.28)>2 or abs(float(page.mediabox.height)-841.89)>2:
            raise RuntimeError("Supplement is not PDF A4 "+sp)
        text=page.extract_text()
        for phrase in (sp,"BUKAN PDP BAHARU","BUKAN BUKU AKTIVITI KPM",
                       "Aktiviti 1","Aktiviti 2","Aktiviti 3","DRAF/HOLD"):
            if phrase not in text:raise RuntimeError(f"PDF missing {phrase} at {sp}")
        manifest.append({
            "subject":"Sains","year":2,"sp":sp,"source_sp_text":sem[sp]["official_dskp_text"],
            "official_pdp_code":"","lesson_assignment":"UNSCHEDULED_NEEDS_PANITIA",
            "word_file":word.name,"pdf_file":pdf.name,
            "print_word_a4_one_page":"PASS","pdf_a4_one_page":"PASS",
            "textbook_page":"UNVERIFIED",
            "original_official_kpm_workbook":False,"teacher_approved":False,
            "runtime_enabled":False,"status":"STAGING_HOLD"
        })
    with (OUT/"Y2_3_UNMAPPED_SP_PBD_MANIFEST_HOLD.csv").open(
            "w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=list(manifest[0]))
        writer.writeheader();writer.writerows(manifest)
    (OUT/"Y2_3_UNMAPPED_SP_PBD_GATE_HOLD.json").write_text(
        json.dumps({"count":3,"sp":[x["sp"] for x in manifest],
                    "original_pdp_source_count_unchanged":51,"teacher_approval":0,
                    "runtime_enabled":False,"source_status":"DSKP_SEMANTIC_VERIFIED__ACADEMIC_HOLD",
                    "manifest":manifest},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_T2_UNIT3: 3 original supplementary SP materials Word/PDF A4 1 page; zero official new PdP; HOLD")
    return manifest

if __name__=="__main__":
    build()
