"""Presentation-only cover for existing Moral RPT. No curriculum or DB edits."""
from io import BytesIO
from pathlib import Path

def prepend_cover(year, group, original_pdf, output_pdf):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen.canvas import Canvas
    from pypdf import PdfReader, PdfWriter
    if type(year) is not int or year not in range(2,7) or group not in ("A","B","A/B"):
        raise ValueError("Invalid Moral RPT year/group")
    source=Path(original_pdf)
    dest=Path(output_pdf)
    if not source.is_file() or source.resolve()==dest.resolve():
        raise ValueError("Source missing or output overwrites original")
    dest.parent.mkdir(parents=True,exist_ok=True)
    w,h=landscape(A4)
    buf=BytesIO()
    c=Canvas(buf,pagesize=(w,h))
    c.setAuthor("CikguLaju AI")
    c.setTitle(f"RPT Pendidikan Moral Tahun {year} Kumpulan {group} 2027")
    ink=colors.HexColor("#193954")
    c.setFillColor(ink)
    c.rect(0,h-110,w,110,fill=1,stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold",11)
    c.drawString(46,h-43,"CIKGULAJU AI  |  RPT 2027")
    c.setFont("Helvetica-Bold",22)
    c.drawString(46,h-80,"RANCANGAN PENGAJARAN TAHUNAN")
    c.setFillColor(ink)
    c.setFont("Helvetica-Bold",19)
    c.drawString(46,h-170,f"PENDIDIKAN MORAL TAHUN {year} (SK)")
    c.setFont("Helvetica-Bold",12)
    c.drawString(46,h-196,f"2027  |  KUMPULAN {group}  |  96 SESI")
    labels=("NAMA SEKOLAH","ALAMAT SEKOLAH","NAMA GURU","KELAS")
    for i,key in enumerate(labels):
        yy=h-268-i*47
        c.setFillColor(colors.HexColor("#e9f0f5"))
        c.rect(45,yy-9,w-90,43,fill=1,stroke=0)
        c.setFillColor(ink)
        c.setFont("Helvetica-Bold",10)
        c.drawString(60,yy+9,key)
        c.setFont("Helvetica",10)
        c.drawString(240,yy+9,"_"*62)
    c.setFillColor(colors.HexColor("#527084"))
    c.setFont("Helvetica",9)
    c.drawString(46,90,"42 PdP teras + 54 sesi pengukuhan. Tarikh sesi mengikut takwim dan jadual sekolah.")
    c.drawString(46,74,"Agihan PdP CikguLaju boleh disesuaikan dengan cuti dan keperluan sekolah.")
    c.showPage()
    c.save()
    buf.seek(0)
    original=PdfReader(str(source))
    writer=PdfWriter()
    writer.append_pages_from_reader(PdfReader(buf))
    writer.append_pages_from_reader(original)
    with dest.open("wb") as f:
        writer.write(f)
    built=PdfReader(str(dest))
    if len(built.pages)!=len(original.pages)+1:
        raise RuntimeError("Moral cover changed PDF body page count")
    return dest
