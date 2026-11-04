"""Read-only PSV RPT 2027 PDF generator; original RPH and DB are untouched."""
import csv
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parent
YEARS=frozenset(range(2,7))

def source_rows(year):
    if type(year) is not int or year not in YEARS: return []
    try:
        with (ROOT / ("RPT_PSV_Tahun_%d_2027_DRAF.csv"%year)).open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        if len(rows)!=42: return []
        for n,r in enumerate(rows,1):
            if r.get("PdP")!="%03d"%n or r.get("Tahun")!=str(year) or r.get("Status")!="DRAF_SEMAK": return []
            if not all(r.get(k) for k in ("SK","SP","Objektif","Evidens PBD")): return []
            if not (r.get("Tajuk karya cadangan") or r.get("Tajuk/aktiviti PdP")): return []
        return rows
    except (OSError,ValueError,UnicodeError,csv.Error): return []

def pdf_ready(year):
    try:
        import reportlab
    except ImportError:
        return False
    return bool(source_rows(year))

def build_pdf(year,destination):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    rows=source_rows(year)
    if not rows: raise ValueError("Incomplete PSV RPT source; fail closed")
    out=Path(destination)
    out.parent.mkdir(parents=True,exist_ok=True)
    font,bold="Helvetica","Helvetica-Bold"
    reg=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    regbold=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if reg.is_file() and regbold.is_file():
        if "PSVDejaVu" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("PSVDejaVu",str(reg)))
            pdfmetrics.registerFont(TTFont("PSVDejaVu-Bold",str(regbold)))
        font,bold="PSVDejaVu","PSVDejaVu-Bold"
    def para(txt,size=7,lead=10,strong=False,color="#193954"):
        return Paragraph(escape(str(txt or "")),ParagraphStyle(
            "psv",fontName=bold if strong else font,fontSize=size,leading=lead,
            textColor=colors.HexColor(color)))
    w,h=landscape(A4)
    doc=SimpleDocTemplate(str(out),pagesize=(w,h),leftMargin=32,rightMargin=32,topMargin=48,bottomMargin=43,
        title=f"RPT Pendidikan Seni Visual Tahun {year} 2027",author="CikguLaju AI")
    pale=colors.HexColor("#e9f0f5")
    story=[Spacer(1,64),para("CIKGULAJU AI | RPT 2027",11,15,True),Spacer(1,34),
        para("RANCANGAN PENGAJARAN TAHUNAN",23,31,True),Spacer(1,9),
        para(f"PENDIDIKAN SENI VISUAL TAHUN {year} (SK)",18,25,True),Spacer(1,8),
        para("2027 | 42 PdP | PERANCANGAN CADANGAN",11,18,True),Spacer(1,34)]
    box=Table([[para(k,9,14,True),para("_"*65,10,14)] for k in
        ("NAMA SEKOLAH","ALAMAT SEKOLAH","NAMA GURU","KELAS")],
        colWidths=[145,w-209],rowHeights=[37]*4)
    box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),pale),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),12),
        ("LINEBELOW",(0,0),(-1,-2),0.5,colors.white)]))
    story += [box,Spacer(1,22),
        para("Kumpulan A/B: Tarikh sebenar mengikut takwim negeri, jadual waktu dan cuti sekolah.",9,15),
        Spacer(1,8),para("Susunan PdP adalah perancangan CikguLaju; semakan akhir sumber BT/DSKP dan kalendar masih berjalan.",8,13,color="#527084"),
        PageBreak(),para(f"RPT PENDIDIKAN SENI VISUAL TAHUN {year} | 42 PdP",12,18,True),Spacer(1,12)]
    table=[[para("PdP",8,12,True),para("UNIT / TAJUK / FOKUS",8,12,True),
        para("SK / SP / BT",8,12,True),para("OBJEKTIF / EVIDENS PBD",8,12,True)]]
    for r in rows:
        title=r.get("Tajuk/aktiviti PdP") or r.get("Tajuk karya cadangan","")
        unit=r.get("Tajuk unit") or r.get("Tajuk karya cadangan","")
        area=r.get("Bidang") or r.get("Modul") or ""
        focus=r.get("Fokus","")
        page=r.get("Rujukan BT ms (RPT 2026)") or r.get("BT muka surat","")
        table.append([
            para(r["PdP"],8,12,True),
            [para(unit,8,11,True),Spacer(1,2),para(title if title!=unit else area,7.2,10),
                Spacer(1,3),para("Fokus: "+focus,6.6,9,color="#527084")],
            [para("SK "+r["SK"],7.2,10),Spacer(1,3),para("SP "+r["SP"],7.2,10),
                Spacer(1,3),para("BT: "+page,6.5,9,color="#527084")],
            [para("Objektif: "+r["Objektif"],7,10),Spacer(1,3),
                para("PBD: "+r["Evidens PBD"],6.8,9,color="#527084")]
        ])
    t=Table(table,colWidths=[44,192,140,w-64-376],repeatRows=1,hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),pale),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f7f9fb")]),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("BOX",(0,0),(-1,-1),0.6,colors.HexColor("#193954")),
        ("INNERGRID",(0,0),(-1,-1),0.35,colors.HexColor("#bacad5")),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
    story.append(t)
    def footer(c,d):
        c.saveState()
        c.setStrokeColor(colors.HexColor("#d3e0e9"))
        c.line(32,33,w-32,33)
        c.setFont(font,7)
        c.setFillColor(colors.HexColor("#527084"))
        c.drawString(32,24,"CIKGULAJU AI | RPT PSV 2027 | PERANCANGAN PdP")
        c.drawRightString(w-32,24,f"Halaman {d.page}")
        c.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    if not out.is_file() or out.stat().st_size<8000: raise RuntimeError("PSV RPT PDF failed")
    return out
