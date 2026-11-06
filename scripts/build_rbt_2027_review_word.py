#!/usr/bin/env python3
"""Generate RBT Y4-Y6 2027 Word RPH and Word RPT review bundles.

Staging-only QA. It does not publish to Telegram, Web or the production DB.
All documents are visibly watermarked DRAF and carry release_ready=False.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
BLUE=RGBColor(28,60,89)
DARK=RGBColor(34,49,62)
GREY=RGBColor(94,110,125)
PALE="EAF1F6"

def format_cell(cell,fill=False):
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    tc=cell._tc
    props=tc.get_or_add_tcPr()
    mar=props.first_child_found_in("w:tcMar")
    if mar is None:
        mar=OxmlElement("w:tcMar");props.append(mar)
    for side in ["top","start","bottom","end"]:
        el=OxmlElement("w:"+side);el.set(qn("w:w"),"95" if side in ("top","bottom") else "85")
        el.set(qn("w:type"),"dxa");mar.append(el)
    if fill:
        sh=OxmlElement("w:shd");sh.set(qn("w:fill"),PALE);props.append(sh)
    for p in cell.paragraphs:
        p.paragraph_format.space_before=Pt(0)
        p.paragraph_format.space_after=Pt(0)
        p.paragraph_format.line_spacing=1.11
        for r in p.runs:r.font.size=Pt(9.45)

def para(doc,text="",bold=False,size=9.4,space=2,color=DARK,align=None):
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(space)
    p.paragraph_format.line_spacing=1.0
    if align:p.alignment=align
    r=p.add_run(str(text));r.bold=bold;r.font.size=Pt(size);r.font.name="Aptos";r.font.color.rgb=color
    return p

def init_doc(landscape=False):
    d=Document()
    sec=d.sections[0]
    sec.page_width=Cm(29.7 if landscape else 21)
    sec.page_height=Cm(21 if landscape else 29.7)
    sec.top_margin=Cm(0.7)
    sec.bottom_margin=Cm(0.7)
    sec.left_margin=Cm(0.82)
    sec.right_margin=Cm(0.82)
    sec.header_distance=Cm(0.25)
    sec.footer_distance=Cm(0.25)
    normal=d.styles["Normal"]
    normal.font.name="Aptos"
    normal.font.size=Pt(9.45)
    normal.paragraph_format.space_after=Pt(0)
    normal.paragraph_format.line_spacing=1.11
    return d

def rph_doc(lesson):
    assert lesson["review"]["release_ready"] is False
    y=lesson["tahun"]
    d=init_doc(False)
    para(d,"CIKGULAJU  •  RANCANGAN PENGAJARAN HARIAN  •  DRAF UNTUK SEMAKAN",True,10.4,2,BLUE)
    para(d,"REKA BENTUK DAN TEKNOLOGI  |  TAHUN "+str(y)+"  |  "+lesson["id"],True,9.7,4,BLUE)
    t=d.add_table(rows=0,cols=2)
    t.autofit=False;t.columns[0].width=Cm(3.65);t.columns[1].width=Cm(15.48)
    values=[
      ("Tarikh / Hari / Kelas / Masa","____/____/2027   /   __________   /   __________   /   ______–______"),
      ("Unit / PdP",lesson["unit_label"]+" | "+lesson["tajuk"]),
      ("SK / SP",", ".join(lesson["sk"])+"  /  "+", ".join(lesson["sp_codes"])),
      ("Objektif",lesson["objektif"]),
      ("Kriteria Kejayaan",lesson["kriteria_kejayaan"]),
      ("BBM",lesson["bbm"]),
      ("Rujukan Buku Teks",
       "Calon rujukan: "+("; ".join(
            ref["sp"]+" (hlm. "+"–".join(map(str,ref["muka_surat_bercetak_calon"]))+")"
            for ref in lesson["rujukan_buku_teks"].get("calon_muka_surat_mengikut_sp",[])
        ) or ", ".join(str(x) for x in lesson["rujukan_buku_teks"].get("calon_muka_surat_teks_digital",[])))+
       " — belum sah aktiviti visual" if lesson["rujukan_buku_teks"].get("calon_muka_surat_teks_digital") else
       "Halaman Buku Teks masih perlu pengesahan")
    ]
    for k,v in values:
        c=t.add_row().cells
        c[0].text=k
        c[1].text=v
        format_cell(c[0],fill=True);format_cell(c[1])
        for p in c[0].paragraphs:
            for r in p.runs:r.bold=True
    para(d,"LANGKAH PENGAJARAN & PEMBELAJARAN  •  60 MINIT",True,9.3,2,BLUE)
    a=d.add_table(rows=0,cols=2)
    a.autofit=False;a.columns[0].width=Cm(3.65);a.columns[1].width=Cm(15.48)
    for key,label in [
       ("set_induksi","Set Induksi"),("aktiviti_1","Aktiviti 1"),
       ("aktiviti_2","Aktiviti 2"),("pengukuhan_penilaian","PBD / Pengukuhan"),
       ("penutup","Penutup")]:
       step=lesson["langkah"][key]
       c=a.add_row().cells
       c[0].text=label+"\n("+str(step["minit"])+" minit)"
       c[1].text=step["aktiviti"]
       format_cell(c[0],fill=True);format_cell(c[1])
       for p in c[0].paragraphs:
           for r in p.runs:r.bold=True
    para(d,"Keselamatan: "+lesson["keselamatan"],False,8.1,3,DARK)
    para(d,"Refleksi: ____ / ____ murid mencapai objektif. Susulan: ______________________________",False,8.1,2,GREY)
    para(d,"DRAF STAGING  •  Belum disahkan secara individu / belum dilepaskan kepada pengguna.",False,7.8,0,GREY)
    return d

def rpt_doc(year,rows):
    d=init_doc(True)
    para(d,"CIKGULAJU  |  RANCANGAN PENGAJARAN TAHUNAN",True,13,8,BLUE,WD_PARAGRAPH_ALIGNMENT.CENTER)
    para(d,"REKA BENTUK DAN TEKNOLOGI",True,24,9,BLUE,WD_PARAGRAPH_ALIGNMENT.CENTER)
    para(d,f"TAHUN {year}   •   SESI 2027",True,20,12,BLUE,WD_PARAGRAPH_ALIGNMENT.CENTER)
    para(d,"KUMPULAN A / KUMPULAN B",True,13,14,DARK,WD_PARAGRAPH_ALIGNMENT.CENTER)
    for x in ["NAMA SEKOLAH  :  __________________________________________________",
              "NAMA GURU         :  __________________________________________________",
              "NEGERI / KUMPULAN :  _____________________________________________"]:
        para(d,x,False,11,12)
    para(d,"Berasaskan DSKP KSSR (Semakan 2017). 32 jam minimum setahun; "+
         "susunan 32 PdP ini ialah susunan cadangan CikguLaju, bukan bilangan rasmi KPM.",False,10,8)
    para(d,"Tarikh, minggu Kumpulan A/B, cuti negeri dan halaman aktiviti Buku Teks mesti disahkan "+
        "sebelum RPT ini digunakan dalam sistem.",False,10,8)
    para(d,"DRAF STAGING — SEMAKAN, BUKAN UNTUK PENERBITAN",True,10,2,GREY)
    d.add_page_break()
    para(d,f"RPT RBT TAHUN {year}  •  2027  |  KUMPULAN A/B",True,13,6,BLUE)
    para(d,"Kalendar tarikh kelas belum diisi kerana jadual waktu dan cuti negeri bergantung profil guru.",False,9.2,7,DARK)
    t=d.add_table(rows=1,cols=6)
    t.autofit=False
    widths=[Cm(1.25),Cm(5.6),Cm(10.15),Cm(1.55),Cm(3.5),Cm(5.3)]
    for col,w in zip(t.columns,widths):col.width=w
    headers=["PdP","Unit","Tajuk","SK","SP","Rujukan Buku"]
    for c,val in zip(t.rows[0].cells,headers):
        c.text=val;format_cell(c,True)
        for p in c.paragraphs:
            for r in p.runs:r.bold=True
    for row in rows:
        vals=[row.get("PdP",""),row.get("Unit",""),row.get("Tajuk PdP",""),
             row.get("SK",""),row.get("SP",""),row.get("Rujukan Buku Teks m/s","")]
        cells=t.add_row().cells
        for c,val in zip(cells,vals):
            c.text=str(val);format_cell(c)
    para(d,"NOTA: Peruntukan mata pelajaran 32 jam/tahun. Tarikh PdP mengikut takwim sekolah dan jadual guru; "+
         "penggunaan modul dan projek memerlukan ketersediaan peralatan.",False,8,2,GREY)
    return d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--year",choices=("4","5","6","all"),default="all")
    args=ap.parse_args()
    root=args.out.resolve()
    root.mkdir(parents=True,exist_ok=True)
    total=0
    years=[4,5,6] if args.year=="all" else [int(args.year)]
    for y in years:
        src=ROOT/f"rph_standalone/rbt/tahun_{y}/RPH_RBT_T{y}_2027_DRAF.json"
        data=json.loads(src.read_text(encoding="utf-8"))
        lessons=data["pelajaran"]
        assert data["status"]=="DRAF_STAGING" and data["bukan_modul_pengguna"] is True
        assert len(lessons)==32 and all(not l["review"]["release_ready"] for l in lessons)
        folder=root/f"tahun_{y}";folder.mkdir(exist_ok=True)
        for l in lessons:
            p=folder/("RPH_"+l["id"].replace("-","_")+"_DRAF.docx")
            rph_doc(l).save(p)
            total+=1
        with (ROOT/f"rpt_2027/rbt/RPT_RBT_T{y}_2027_DRAF.csv").open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        assert len(rows)==32
        rpt_doc(y,rows).save(folder/f"RPT_RBT_T{y}_2027_DRAF.docx")
        print(f"T{y}: 32 RPH Word dan 1 RPT landscape Word (DRAF)")
    assert total==32*len(years)
    print("TOTAL RPH DOCX",total,"(belum disahkan layout PDF)")
if __name__=="__main__":
    main()
