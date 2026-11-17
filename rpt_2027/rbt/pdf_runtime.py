"""RBT 2027: source-validated RPT landscape PDF with title cover (DRAF).

Read-only, Y4–6 only, 32 explicit PdP with same exact RPH titles and SK/SP.
Teaching windows use the paired KPM calendar and the reviewed RBT allocation.
The textbook references retain their draft status.
"""
from __future__ import annotations
import csv
import json
from datetime import date
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[2]
YEAR_SET=frozenset((4,5,6))


def teaching_windows():
    folder = ROOT / "rpt_2027"
    schedule = json.loads((folder / "rbt" / "weekly_2027.json").read_text(encoding="utf-8"))
    weeks = schedule["week_by_pdp"]
    if (len(weeks) != 32 or weeks != sorted(set(weeks))
            or any(type(n) is not int or n not in range(1, 39) or n in {6, 18, 19}
                   for n in weeks)):
        raise ValueError("RBT requires 32 reviewed weeks through M38")
    master = json.loads((folder / "takwim_pdp_2027_ab_draf.json").read_text(encoding="utf-8"))
    rows = {row["minggu"]: row for row in master["minggu"]}
    if any(not rows[n]["boleh_jadualkan_pdp"] for n in weeks):
        raise ValueError("RBT has a session in a reserved week")
    return [rows[n] for n in weeks]


def source_rows(year):
    if type(year) is not int or year not in YEAR_SET:
        return []
    try:
        with (ROOT/f"rpt_2027/rbt/RPT_RBT_T{year}_2027_DRAF.csv").open(
                encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        doc=json.loads((ROOT/f"rph_standalone/rbt/tahun_{year}/"
                        f"RPH_RBT_T{year}_2027_DRAF.json").read_text(encoding="utf-8"))
        lessons=doc["pelajaran"]
        if (len(rows)!=32 or len(lessons)!=32
                or doc["status"]!="DRAF_STAGING"):
            return []
        for n,(row,l) in enumerate(zip(rows,lessons),1):
            if (row["ID"]!=l["id"] or int(row["PdP"])!=n
                    or row["Unit"]!=l["unit_label"]
                    or row["Tajuk PdP"]!=l["tajuk"]
                    or row["SK"]!=" / ".join(l["sk"])
                    or row["SP"]!=" / ".join(l["sp_codes"])
                    or row["Status"]!="DRAF" or l["review"]["release_ready"] is not False):
                return []
        return rows
    except (OSError,KeyError,ValueError,TypeError,csv.Error,UnicodeError):
        return []


def build_pdf(year,destination):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    rows=source_rows(year)
    if not rows:
        raise ValueError("RPT RBT source incomplete or disagrees with RPH")
    windows = teaching_windows()
    out=Path(destination)
    out.parent.mkdir(parents=True,exist_ok=True)
    w,h=landscape(A4)
    font,bold="Helvetica","Helvetica-Bold"
    path=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    boldpath=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if path.is_file() and boldpath.is_file():
        if "RBTDejaVu" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RBTDejaVu",str(path)))
            pdfmetrics.registerFont(TTFont("RBTDejaVu-Bold",str(boldpath)))
        font,bold="RBTDejaVu","RBTDejaVu-Bold"
    def p(value,size=7.3,leading=10,strong=False,color="#24405A"):
        return Paragraph(escape(str(value or "")),ParagraphStyle(
            "rbt",fontName=bold if strong else font,fontSize=size,leading=leading,
            textColor=colors.HexColor(color)))
    doc=SimpleDocTemplate(str(out),pagesize=(w,h),leftMargin=35,rightMargin=35,
                          topMargin=38,bottomMargin=36,
                          title=f"RPT RBT Tahun {year} 2027 DRAF",author="CikguLaju AI")
    navy=colors.HexColor("#20476a")
    pale=colors.HexColor("#EAF2F6")
    story=[
      Spacer(1,61),p("CIKGULAJU AI  |  2027",11,18,True),Spacer(1,26),
      p("RANCANGAN PENGAJARAN TAHUNAN",23,31,True),Spacer(1,7),
      p(f"REKA BENTUK DAN TEKNOLOGI • TAHUN {year}",16,24,True),Spacer(1,12),
      p("KUMPULAN A / KUMPULAN B  •  32 PdP cadangan",10,17,True),
      Spacer(1,25),
    ]
    t=Table([[p(x,9,13,True),p("_"*70,10,14)]
             for x in ("NAMA SEKOLAH","NAMA GURU","KELAS","NEGERI / KUMPULAN")],
            colWidths=[155,w-225],rowHeights=[33]*4)
    t.setStyle(TableStyle([
      ("BACKGROUND",(0,0),(-1,-1),pale),
      ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
      ("LEFTPADDING",(0,0),(-1,-1),11),
      ("LINEBELOW",(0,0),(-1,-2),0.7,colors.white)
    ]))
    story.extend([t,Spacer(1,23),
       p("32 sesi 60 minit. PdP baharu selesai pada Minggu 38. Minggu 39 hingga 44 untuk pentaksiran, ulang kaji dan aktiviti sekolah. Sahkan slot dengan jadual kelas dan cuti negeri.",8.6,15),
       Spacer(1,10),
       p("DRAF UNTUK SEMAKAN: semua rujukan halaman ialah calon teks; visual aktiviti dan kelulusan guru masih tertangguh.",8.1,13,color="#5B6D78"),
       PageBreak(),p(f"RPT RBT TAHUN {year} | 2027 | KUMPULAN A/B",12,18,True),Spacer(1,11)])
    tab=[[p("PdP",8,12,True),p("MINGGU / A DAN B",8,12,True),p("UNIT / TAJUK",8,12,True),
          p("SK / SP",8,12,True),p("RUJUKAN BUKU TEKS (BELUM SAH)",7,10,True)]]
    for r, window in zip(rows, windows, strict=True):
        labels = [p(f'M{window["minggu"]:02d}', 7.5, 11, True)]
        for group in ("A", "B"):
            first, last = (date.fromisoformat(d).strftime("%d/%m/%Y") for d in window[group])
            labels.append(p(f"Kumpulan {group} {first} - {last}", 7, 10))
        tab.append([
          p(f'{int(r["PdP"]):03d}',8.2,12,True),
          labels,
          [p(r["Unit"],7.5,11,True),Spacer(1,3),p(r["Tajuk PdP"],7,10)],
          [p("SK "+r["SK"],7.4,10),Spacer(1,3),p("SP "+r["SP"],7.2,10)],
          p(r.get("Rujukan Buku Teks m/s",""),6.6,9)
        ])
    table=Table(tab,colWidths=[36,133,240,115,w-70-36-133-240-115],repeatRows=1,hAlign="LEFT")
    table.setStyle(TableStyle([
       ("BACKGROUND",(0,0),(-1,0),pale),
       ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F6F9FA")]),
       ("VALIGN",(0,0),(-1,-1),"TOP"),
       ("BOX",(0,0),(-1,-1),0.5,navy),
       ("INNERGRID",(0,0),(-1,-1),0.3,colors.HexColor("#C2D4DF")),
       ("LEFTPADDING",(0,0),(-1,-1),7),
       ("RIGHTPADDING",(0,0),(-1,-1),7),
       ("TOPPADDING",(0,0),(-1,-1),7),
       ("BOTTOMPADDING",(0,0),(-1,-1),7)
    ]))
    story.append(table)
    def footer(c,report):
        c.saveState()
        c.setStrokeColor(colors.HexColor("#CCDBE5"))
        c.line(35,30,w-35,30)
        c.setFillColor(colors.HexColor("#506678"))
        c.setFont(font,7)
        c.drawString(35,21,"CIKGULAJU  •  RPT RBT 2027  •  DRAF UNTUK SEMAKAN")
        c.drawRightString(w-35,21,f"Halaman {report.page}")
        c.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    if not out.is_file() or out.stat().st_size<4000:
        raise RuntimeError("RBT RPT PDF empty or too small")
    return out


def pdf_ready(year):
    try:
        import reportlab  # noqa
        return bool(source_rows(year) and teaching_windows())
    except (ImportError, OSError, KeyError, TypeError, ValueError):
        return False
