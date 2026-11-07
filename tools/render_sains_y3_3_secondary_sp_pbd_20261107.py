"""Three original Sains Year3 PBD sheets for SECONDARY SPs in multi-SP source PdP.

SP 3.2.5, 3.3.3 and 3.3.4 are genuine Year3 KSSR 2017 learning standards.
The current activity book mapping in each PdP cites its PRIMARY SP only.
Never present these worksheets as official KPM Buku Aktiviti, and never
mark a source as teacher-approved or update a production runtime/DB.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pypdf import PdfReader

from tools.sains_buku_aktiviti_mapping_20261107 import ROOT,load_activity_books

OUT=ROOT/"build/sains_y3_3_secondary_sp_pbd_DRAF_20261107"
DSKP="https://fliphtml5.com/dhphy/tqdi/DSKP_SAINS_TAHUN_3/"
TASKS={
  "3.2.5":{
    "pdp":"SCI-Y3-PDP-006","primary":"3.2.1",
    "sp_text":"Menjelaskan pemerhatian tentang kelas makanan menerusi lakaran, TMK, penulisan atau lisan secara kreatif.",
    "title":"Kelas Makanan — Terangkan Pilihan Hidangan Saya",
    "prep":"Guru tunjuk foto makanan pelbagai kelas atau kad gambar; sediakan carta rujukan kumpulan makanan.",
    "a1":"Lakar satu pinggan contoh yang mempunyai sekurang-kurangnya empat contoh makanan. Label kelas makanan bagi setiap contoh.",
    "a2":"Terangkan DUA pemerhatian kelas makanan daripada lakaran kamu dan sebab badan memerlukannya.",
    "a3":"Jelaskan kepada guru secara lisan atau bertulis bagaimana kamu menentukan kelas makanan berdasarkan contoh bergambar.",
    "criteria":["Empat contoh dipadankan kepada kelas makanan munasabah",
                "Dua pemerhatian kelas makanan disokong penjelasan fungsi",
                "Murid dapat berkomunikasi secara kreatif dengan bukti sendiri"],
    "safety":"Tiada pendedahan berat, keadaan kesihatan, alahan atau diet peribadi murid. Gunakan menu watak rekaan.",
  },
  "3.3.3":{
    "pdp":"SCI-Y3-PDP-010","primary":"3.3.1",
    "sp_text":"Merumus tentang makanan tercerna yang tidak diperlukan oleh badan.",
    "title":"Apa Jadi kepada Sisa Makanan yang Tidak Diperlukan?",
    "prep":"Guru tunjuk rajah proses pencernaan sesuai umur dengan mulut, esofagus, perut, usus dan dubur.",
    "a1":"Lakar perjalanan makanan melalui sistem pencernaan dan tandakan bahagian makanan yang diserap sebagai nutrien serta sisa yang tidak diperlukan.",
    "a2":"Tuliskan DUA kenyataan daripada rajah: apakah berlaku kepada nutrien dan ke manakah sisa yang tidak diperlukan dibawa.",
    "a3":"Bina rumusan SATU atau DUA ayat tentang sisa makanan yang tidak diperlukan badan dan cara ia dikeluarkan.",
    "criteria":["Arah laluan makanan pada rajah tepat dan bahagian utama dapat dikenal pasti",
                "Perbezaan nutrien diserap dan sisa dinyatakan dengan betul",
                "Rumusan tentang penyingkiran sisa melalui dubur berasaskan bukti"],
    "safety":"Gunakan rajah sahaja; jangan meminta murid membawa sampel najis atau berkongsi masalah pencernaan peribadi.",
  },
  "3.3.4":{
    "pdp":"SCI-Y3-PDP-011","primary":"3.3.2",
    "sp_text":"Menjelaskan pemerhatian tentang pencernaan menerusi lakaran, TMK, penulisan atau lisan secara kreatif.",
    "title":"Proses Pencernaan — Saya Boleh Menerangkan",
    "prep":"Guru sediakan carta alir dan gambar kedudukan organ pencernaan; gunakan istilah saintifik asal DSKP.",
    "a1":"Lakar aliran makanan melalui mulut, esofagus, perut, usus dan dubur mengikut arah yang betul.",
    "a2":"Nyatakan DUA perubahan yang berlaku terhadap makanan semasa pencernaan berdasarkan rajah.",
    "a3":"Jelaskan proses pencernaan menggunakan lakaran, penulisan atau lisan; hubungkan penghancuran makanan dengan penyerapan nutrien.",
    "criteria":["Rajah aliran lima bahagian utama betul",
                "Dua pemerhatian proses pencernaan dinyatakan dengan tepat",
                "Murid menjelaskan pemerhatian melalui lakaran atau komunikasi sendiri"],
    "safety":"Tiada demonstrasi menelan objek, menyentuh tubuh rakan atau mendedahkan sejarah kesihatan peribadi.",
  },
}
ORDER=("3.2.5","3.3.3","3.3.4")

def stem(sp):
    t=TASKS[sp]
    return f"SAINS_T3_PDP_{int(t['pdp'][-3:]):03d}_SP_{sp.replace('.','_')}_PBD_SOKONGAN_DRAF"

def verify_source():
    rows=load_activity_books()[3]
    if set(TASKS)!=set(ORDER) or len(rows)!=45:
        raise RuntimeError("Secondary SP source list changed")
    expected_primary={"3.2.5":"3.2.1","3.3.3":"3.3.1","3.3.4":"3.3.2"}
    for sp,t in TASKS.items():
        entry=rows[t["pdp"]]
        if entry["sp"]!=expected_primary[sp] or t["primary"]!=expected_primary[sp]:
            raise RuntimeError("Secondary SP pairing vs workbook changed: "+sp)
        if not t["a1"] or not t["a2"] or not t["a3"] or len(t["criteria"])!=3:
            raise RuntimeError("Insufficient individual evidence in SP "+sp)
    return True

def build_docx(sp):
    t=TASKS[sp]
    d=Document(); sec=d.sections[0]
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.left_margin=Cm(1.2);sec.right_margin=Cm(1.2)
    sec.top_margin=Cm(1.0);sec.bottom_margin=Cm(1.0)
    st=d.styles["Normal"];st.font.name="Arial";st.font.size=Pt(9.5)
    st.paragraph_format.space_after=Pt(4)
    h=d.add_paragraph()
    h.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=h.add_run("SAINS TAHUN 3 — PENTAKSIRAN INDIVIDU");r.bold=True;r.font.size=Pt(13)
    h=d.add_paragraph()
    h.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=h.add_run("PBD SOKONGAN CIKGULAJU • BUKAN LATIHAN BUKU AKTIVITI RASMI");r.bold=True;r.font.size=Pt(8.5)
    meta=d.add_table(rows=2,cols=2);meta.style="Table Grid"
    meta.cell(0,0).text="Nama: __________________________"
    meta.cell(0,1).text="Kelas: __________  Tarikh: ____/____/______"
    meta.cell(1,0).text=f"PdP: {t['pdp']} • SP sokongan: {sp}"
    meta.cell(1,1).text=f"BA hanya dipadankan dengan SP {t['primary']}"
    h=d.add_paragraph();r=h.add_run(t["title"]);r.bold=True;r.font.size=Pt(11)
    h=d.add_paragraph();r=h.add_run("SP DSKP: ");r.bold=True;h.add_run(t["sp_text"])
    h=d.add_paragraph();r=h.add_run("Persediaan guru: ");r.bold=True;h.add_run(t["prep"])
    for i,key in enumerate(("a1","a2","a3"),1):
        h=d.add_paragraph();r=h.add_run(f"Aktiviti {i} — ");r.bold=True;h.add_run(t[key])
        if i==1:
            tb=d.add_table(rows=1,cols=3);tb.style="Table Grid"
            for j,cell in enumerate(tb.rows[0].cells):
                cell.text=f"{chr(65+j)}\n"+("\n"*11)
        elif i==2:
            for j in range(2):
                d.add_paragraph(f"{j+1}. _______________________________________________________________")
        else:
            d.add_paragraph("Jawapan murid / catatan lisan guru: __________________________________________")
    h=d.add_paragraph();r=h.add_run("Kriteria penilaian guru: ");r.bold=True
    for c in t["criteria"]:d.add_paragraph("☐ "+c)
    h=d.add_paragraph();r=h.add_run("Keselamatan: ");r.bold=True;h.add_run(t["safety"])
    h=d.add_paragraph();r=h.add_run("Status: DRAF/HOLD — belum diluluskan oleh panitia. ");r.bold=True
    h.add_run("Buku Aktiviti rasmi untuk PdP ini hanya dikaitkan dengan SP utama.")
    path=OUT/(stem(sp)+".docx");d.save(path)
    return path

def main():
    verify_source();OUT.mkdir(parents=True,exist_ok=True)
    docs=[build_docx(sp) for sp in ORDER]
    exe=shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:raise RuntimeError("LibreOffice needed for true one-page A4 print QA")
    cmd=[exe,"-env:UserInstallation=file:///tmp/cikgulaju_sains_t3_secondary_pbd_20261107",
         "--headless","--convert-to","pdf","--outdir",str(OUT),*[str(p) for p in docs]]
    r=subprocess.run(cmd,check=False,capture_output=True,text=True,timeout=160)
    if r.returncode!=0:raise RuntimeError("Print export error "+r.stderr[-1000:])
    result=[]
    for sp,word in zip(ORDER,docs):
        pdf=word.with_suffix(".pdf")
        if not pdf.is_file():raise RuntimeError("PBD PDF missing "+sp)
        obj=PdfReader(str(pdf))
        if len(obj.pages)!=1:raise RuntimeError("Extra pages in Year3 PBD "+sp)
        page=obj.pages[0]
        if abs(float(page.mediabox.width)-595.28)>2 or abs(float(page.mediabox.height)-841.89)>2:
            raise RuntimeError("Incorrect A4 PBD sheet size "+sp)
        text=page.extract_text()
        for expected in ("BUKAN LATIHAN BUKU AKTIVITI RASMI","Aktiviti 1","Aktiviti 2",
                         "Aktiviti 3",sp,"Kriteria penilaian guru"):
            if expected not in text:raise RuntimeError("PBD sheet lost source or task "+sp+" "+expected)
        t=TASKS[sp]
        result.append({
            "pdp_code":t["pdp"],"secondary_sp":sp,"primary_sp":t["primary"],
            "source_dskp":DSKP,"document_word":word.name,
            "document_pdf":pdf.name,"official_activity_book":False,
            "rph_primary_workbook_sp_only":True,
            "word_pdf_one_page_A4":"PASS",
            "academic_teacher_approved":False,
            "runtime_available":False,"release":"DRAF_HOLD"
        })
    with (OUT/"T3_TIGA_SP_SOKONGAN_PBD_HOLD.csv").open(
        "w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=list(result[0]))
        writer.writeheader();writer.writerows(result)
    (OUT/"QUALITY_GATE_HOLD.json").write_text(
        json.dumps({"count":3,"PDP":3,"secondary_SP":list(ORDER),
                    "book_sp_complete":False,"academic_approval":False,
                    "staging_only":True,"release":"HOLD"},indent=2,
                   ensure_ascii=False)+"\n",encoding="utf-8")
    print("SAINS_Y3_SECONDARY_PBD: 3 original Word/PDF A4 one-page; no fake BA labels, HOLD")

if __name__=="__main__":
    main()
