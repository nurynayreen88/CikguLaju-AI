#!/usr/bin/env python3
"""Isolated editable Word RPH/RPT previews for Sejarah 2027.
Sources are staging DRAF JSON; no Telegram/API/production imports or writes.
LibreOffice round-trip PDF page counts are a LAYOUT QA, not teacher approval.
"""
from __future__ import annotations
import csv, json, re, shutil, subprocess
from datetime import date
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path
from docx import Document
from docx.shared import Mm, Pt
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"/"sejarah_word_preview_qa"
SECTIONS=(("Set induksi", "set_induksi"),("Aktiviti 1","aktiviti_1"),("Aktiviti 2","aktiviti_2"),("Pengukuhan / PBD","pengukuhan_pbd"),("Penutup","penutup"))

def configure(doc,landscape=False):
    section=doc.sections[0]
    section.page_width=Mm(297 if landscape else 210)
    section.page_height=Mm(210 if landscape else 297)
    section.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.left_margin=section.right_margin=Mm(9 if not landscape else 11)
    section.top_margin=section.bottom_margin=Mm(8 if not landscape else 12)
    section.header_distance=section.footer_distance=Mm(4)
    style=doc.styles["Normal"]
    style.font.name="Arial"
    style.font.size=Pt(9.5 if not landscape else 9.0)
    pf=style.paragraph_format
    pf.space_before=Pt(0);pf.space_after=Pt(1.5);pf.line_spacing=1.03
    return doc

def line(table,heading,body):
    cells=table.add_row().cells
    table.autofit=False
    cells[0].width=Mm(34)
    cells[1].width=Mm(158)
    for idx,words in enumerate((heading,body)):
        c=cells[idx]
        c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        c.text=""
        p=c.paragraphs[0]
        p.paragraph_format.space_after=Pt(0)
        p.paragraph_format.space_before=Pt(0)
        p.paragraph_format.line_spacing=1.08
        run=p.add_run(str(words))
        run.bold=(idx==0)
        run.font.name="Arial"
        run.font.size=Pt(10.2 if idx else 9.7)

def heading(doc,text,size=11):
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after=Pt(3)
    r=p.add_run(text)
    r.bold=True;r.font.name="Arial";r.font.size=Pt(size)

def rph_year(year,obj):
    doc=configure(Document())
    for n,item in enumerate(obj["lessons"]):
        r=item["rph"]
        if n: doc.add_page_break()
        heading(doc,f"RPH SEJARAH TAHUN {year}  •  PdP {item['num']:03d}",14)
        t=doc.add_table(rows=0,cols=2);t.style="Table Grid";t.autofit=False;t.columns[0].width=Mm(34);t.columns[1].width=Mm(158)
        line(t,"Sekolah / Guru","_______________________ / _______________________")
        line(t,"Kelas / Tarikh / Masa","_______________________ / _______________________ / 60 minit")
        line(t,"Unit / Tajuk",r["title"])
        line(t,"SK / SP",r["sk"]+"  |  "+", ".join(r["sp_codes"]))
        line(t,"Objektif","; ".join(r["objective"]))
        line(t,"Kriteria kejayaan",r["success_criteria"])
        line(t,"Buku Teks / BBM",r["bbm"])
        a=doc.add_table(rows=0,cols=2);a.style="Table Grid";a.autofit=False;a.columns[0].width=Mm(34);a.columns[1].width=Mm(158)
        for title,key in SECTIONS: line(a,title+f" ({r[key]['min']} min)",r[key]["activity"])
        line(a,"Refleksi",r["reflection"])
        p=doc.add_paragraph()
        p.paragraph_format.space_before=Pt(2)
        rr=p.add_run("DRAF SEMAKAN • Halaman latihan buku teks belum disahkan • Bukan untuk pengedaran")
        rr.italic=True;rr.font.size=Pt(8.5)
    dest=OUT/f"RPH_SEJARAH_TAHUN_{year}_2027_DRAF_PREVIEW.docx"
    doc.save(str(dest))
    return dest

def rpt_year(year,rows):
    doc=configure(Document(),landscape=True)
    from docx.shared import RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT
    kicker=doc.add_paragraph()
    kicker.alignment=WD_ALIGN_PARAGRAPH.CENTER
    kicker.paragraph_format.space_before=Pt(28)
    k=kicker.add_run("CIKGULAJU AI  |  KURIKULUM STANDARD SEKOLAH RENDAH")
    k.bold=True;k.font.name="Arial";k.font.size=Pt(12)
    k.font.color.rgb=RGBColor(16,111,131)
    for _ in range(2): doc.add_paragraph(" ")
    heading(doc,"RANCANGAN PENGAJARAN TAHUNAN",24)
    heading(doc,f"SEJARAH  •  TAHUN {year}",22)
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("TAHUN AKADEMIK 2027")
    r.bold=True;r.font.size=Pt(16);r.font.color.rgb=RGBColor(16,111,131)
    doc.add_paragraph(" ")
    logo=doc.add_table(rows=1,cols=1)
    logo.style="Table Grid";logo.alignment=WD_TABLE_ALIGNMENT.CENTER;logo.autofit=False
    logo.columns[0].width=Mm(62);logo.cell(0,0).width=Mm(62)
    p=logo.cell(0,0).paragraphs[0]
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run("\n\nLOGO SEKOLAH\n(DARIPADA PROFIL PENGGUNA)\n\n")
    r.bold=True;r.font.size=Pt(10);r.font.color.rgb=RGBColor(90,110,120)
    doc.add_paragraph(" ")
    for v in (
        "NAMA SEKOLAH: ___________________________________________________",
        "NAMA GURU: _______________________________________________________",
        "KUMPULAN A / B   •   36 PdP CADANGAN   •   KSSR SEMAKAN 2017",
        "DRAF: Minggu perancangan sahaja. Sahkan takwim negeri dan jadual kelas sebelum guna.",
    ):
        p=doc.add_paragraph(v)
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(7)
        r=p.runs[0];r.font.name="Arial";r.font.size=Pt(11)
        if v.startswith("DRAF"):r.italic=True;r.font.color.rgb=RGBColor(129,88,38)
    for group in ("A","B"):
        doc.add_page_break()
        heading(doc,f"RPT SEJARAH TAHUN {year} · KUMPULAN {group}",11)
        p=doc.add_paragraph("Minggu cadangan, bukan hari mengajar individu. SP dan PBD mengikut RPH sepadan.")
        p.paragraph_format.space_after=Pt(3)
        tbl=doc.add_table(rows=1,cols=5);tbl.style="Table Grid";tbl.autofit=False
        widths=(12,46,44,64,109)
        for j,w in enumerate(widths): tbl.columns[j].width=Mm(w)
        # Repeat the table labels at the top of every continuation page.
        trPr=tbl.rows[0]._tr.get_or_add_trPr()
        if trPr.find(qn("w:tblHeader")) is None:
            header=OxmlElement("w:tblHeader")
            header.set(qn("w:val"),"true")
            trPr.append(header)
        hdr=("PdP","Minggu mula–akhir","Unit","SK / SP","Evidens PBD")
        for i,v in enumerate(hdr):
            tbl.rows[0].cells[i].width=Mm(widths[i])
            run=tbl.rows[0].cells[i].paragraphs[0].add_run(v);run.bold=True;run.font.size=Pt(9)
        for row in rows:
            cells=tbl.add_row().cells
            vals=(
                row["PdP"],date.fromisoformat(row[f"Kumpulan {group} minggu mula"]).strftime("%d/%m/%Y")+" – "+date.fromisoformat(row[f"Kumpulan {group} minggu akhir"]).strftime("%d/%m/%Y"),
                row["Unit Buku Teks"],row["SK"]+" | "+row["SP"],row["Evidens PBD RPH"],
            )
            for i,value in enumerate(vals):
                cells[i].width=Mm(widths[i])
                cells[i].text=""
                r=cells[i].paragraphs[0].add_run(str(value))
                r.font.name="Arial";r.font.size=Pt(9.0 if i==4 else 8.7)
    dest=OUT/f"RPT_SEJARAH_TAHUN_{year}_2027_DRAF_PREVIEW.docx"
    doc.save(str(dest))
    return dest

def convert_to_pdf(path):
    lo=shutil.which("libreoffice") or shutil.which("soffice")
    if not lo:
        raise RuntimeError("LibreOffice required for Word rendering QA")
    cmd=[lo,"-env:UserInstallation=file://"+str((OUT/"lo_profile").resolve()),"--headless","--convert-to","pdf:writer_pdf_Export","--outdir",str(OUT),str(path)]
    done=subprocess.run(cmd,check=False,text=True,capture_output=True,timeout=150)
    if done.returncode:
        raise RuntimeError(done.stdout+done.stderr)
    pdf=path.with_suffix(".pdf")
    if not pdf.is_file() or pdf.stat().st_size<10000:
        raise AssertionError("Word converted PDF missing/too small: "+str(pdf))
    return pdf

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for year in (4,5,6):
        obj=json.loads((ROOT/f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json").read_text(encoding="utf-8"))
        with (ROOT/f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.csv").open(encoding="utf-8",newline="") as inp:
            rows=list(csv.DictReader(inp))
        assert len(obj["lessons"])==len(rows)==36
        for kind,docx_path in (("RPH",rph_year(year,obj)),("RPT",rpt_year(year,rows))):
            d=Document(str(docx_path))
            assert len(d.sections)==1
            assert (d.sections[0].orientation==WD_ORIENT.LANDSCAPE)==(kind=="RPT")
            pdf_path=convert_to_pdf(docx_path)
            reader=PdfReader(str(pdf_path),strict=True)
            pages=len(reader.pages)
            text="\n".join((p.extract_text() or "") for p in reader.pages)
            if kind=="RPH":
                assert pages==36,("RPH_WORD_NOT_ONE_PAGE_EACH",year,pages)
                assert text.count("RPH SEJARAH TAHUN")==36,("missing RPH page title",year)
                assert all(float(p.mediabox.width)<float(p.mediabox.height) for p in reader.pages)
            else:
                assert 3<=pages<=30,(year,kind,pages)
                assert "RANCANGAN PENGAJARAN TAHUNAN" in text
                assert "KUMPULAN A" in text and "KUMPULAN B" in text
                assert all(float(p.mediabox.width)>float(p.mediabox.height) for p in reader.pages)
            records.append({"year":year,"kind":kind,"docx":docx_path.name,"pdf":pdf_path.name,"pages":pages,"word_pdf_checked":True,"ready":False})
            print(f"{kind} Year {year}: Word to PDF {pages} pages; format and extraction validated",flush=True)
    (OUT/"manifest.json").write_text(json.dumps({"state":"DRAF_WORD_LAYOUT_QA_ONLY","records":records},indent=2)+"\n",encoding="utf-8")
if __name__=="__main__": run()
