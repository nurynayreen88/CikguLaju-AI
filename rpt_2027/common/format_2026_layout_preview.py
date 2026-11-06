"""RPT 2027 teacher-first landscape table, modelled on 2026 RPT conventions.

PURE STAGING/PREVIEW renderer. Does not replace any live Telegram/Web PDF or
claim final curriculum/calendar approval. It accepts independently checked
source rows and will not fill unknown weeks, dates, SK or SP with guesses.
"""
from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
import re


SUBJECTS = {
    "psv": "PENDIDIKAN SENI VISUAL",
    "rbt": "REKA BENTUK DAN TEKNOLOGI",
    "moral": "PENDIDIKAN MORAL",
}
GROUP_A = "Kedah, Kelantan, Terengganu"
GROUP_B = "Negeri-negeri lain / Wilayah Persekutuan"
REQUIRED = ("id", "unit", "sk", "sp", "note")


def validate_rows(subject, year, records):
    if subject not in SUBJECTS or type(year) is not int or year not in range(2, 7):
        raise ValueError("Unsupported RPT subject/year")
    if subject == "rbt" and year < 4:
        raise ValueError("RBT only for Year 4-6")
    if not isinstance(records, list) or not records or len(records) > 160:
        raise ValueError("RPT missing or oversized source rows")
    ids = []
    for row in records:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and
                                                 row[k].strip() for k in REQUIRED):
            raise ValueError("Incomplete sourced RPT row")
        if not re.fullmatch(r"\d{3}", row["id"]):
            raise ValueError("Invalid PdP number")
        ids.append(int(row["id"]))
        for key in ("a_start", "a_end", "b_start", "b_end"):
            if row.get(key):
                try:
                    date.fromisoformat(row[key])
                except ValueError as exc:
                    raise ValueError("Invalid actual date range") from exc
    if ids != list(range(1, len(records) + 1)):
        raise ValueError("Missing, out-of-order or duplicate PdP numbers")
    for row in records:
        for prefix in ("a", "b"):
            a, b = row.get(prefix + "_start", ""), row.get(prefix + "_end", "")
            if bool(a) != bool(b) or (a and a > b):
                raise ValueError("Incomplete or reversed group date range")
    return True


def build_preview(subject, year, records, destination):
    """Create compact, multi-page landscape PDF using only trusted row content.

    One 5-column table: MINGGU/TARIKH | UNIT/TAJUK/PDp | SK | SP | CATATAN.
    Never claims unknown weeks/tarikh as true. Dates are *guides*, not IDs.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
        TableStyle
    )

    validate_rows(subject, year, records)
    out = Path(destination)
    out.parent.mkdir(parents=True, exist_ok=True)
    reg = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    heavy = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    font, bold = "Helvetica", "Helvetica-Bold"
    if reg.is_file() and heavy.is_file():
        if "RPTStandardRegular" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RPTStandardRegular", str(reg)))
        if "RPTStandardBold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RPTStandardBold", str(heavy)))
        font, bold = "RPTStandardRegular", "RPTStandardBold"

    ink = colors.HexColor("#293944")
    line = colors.HexColor("#adb7ba")
    soft = colors.HexColor("#fff4bb")
    paper = colors.HexColor("#fcfcf8")
    w, h = landscape(A4)
    lm, rm = 29, 29
    usable = w - lm - rm

    def p(text, *, size=7.5, leading=11.3, strong=False, color="#263b4e"):
        style = ParagraphStyle(
            "rpt", fontName=bold if strong else font,
            fontSize=size, leading=leading, textColor=colors.HexColor(color),
            wordWrap="CJK", spaceBefore=0, spaceAfter=0
        )
        return Paragraph(escape(str(text or "")).replace("\n", "<br/>"), style)

    def cell(text, strong=False):
        return p(text, strong=strong)

    def range_text(row, prefix):
        first, last = row.get(prefix + "_start", ""), row.get(prefix + "_end", "")
        if first and last:
            start = date.fromisoformat(first).strftime("%d/%m/%Y")
            end = date.fromisoformat(last).strftime("%d/%m/%Y")
            return start if first == last else start + " - " + end
        return "Belum ditentukan"

    doc = SimpleDocTemplate(
        str(out), pagesize=(w, h),
        leftMargin=lm, rightMargin=rm, topMargin=43, bottomMargin=38,
        title=f"RPT {SUBJECTS[subject]} Tahun {year} 2027 - DRAF",
        author="CikguLaju AI"
    )

    def header(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(line)
        canvas.line(lm, h-32, w-rm, h-32)
        canvas.setFont(bold, 8)
        canvas.setFillColor(ink)
        canvas.drawString(lm, h-24, f"RPT {SUBJECTS[subject]} - TAHUN {year} / 2027")
        canvas.setFont(font, 7)
        canvas.drawRightString(w-rm, h-24, "KUMPULAN A + B  |  DRAF SEMAKAN")
        canvas.line(lm, 31, w-rm, 31)
        canvas.drawString(lm, 20, "Sumber: PdP / DSKP asal. Tarikh dan catatan tertakluk pengesahan sekolah.")
        canvas.drawRightString(w-rm, 20, f"Halaman {doc.page}")
        canvas.restoreState()

    cover = [
        Spacer(1, 40),
        p("RANCANGAN PENGAJARAN TAHUNAN", size=21, leading=29, strong=True),
        Spacer(1, 10),
        p(f"{SUBJECTS[subject]}  |  TAHUN {year}", size=16, leading=24, strong=True),
        Spacer(1, 7),
        p("TAHUN PERSEKOLAHAN 2027  •  KUMPULAN A & KUMPULAN B",
          size=10, leading=17, strong=True),
        Spacer(1, 22),
    ]
    fields = ["NAMA SEKOLAH", "ALAMAT SEKOLAH", "NAMA GURU", "KELAS", "NEGERI / KUMPULAN"]
    cover_rows = [[p(label, size=9, leading=15, strong=True),
                   p("__________________________________________________", size=9, leading=15)]
                  for label in fields]
    form = Table(cover_rows, colWidths=[167, usable - 167], rowHeights=[36]*len(fields))
    form.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1),soft),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),13),
        ("LINEBELOW",(0,0),(-1,-2),0.4,colors.white)
    ]))
    cover += [form,Spacer(1,24),
        p(f"Rujukan Kumpulan A: {GROUP_A}",size=8.5,leading=15),
        p(f"Rujukan Kumpulan B: {GROUP_B}",size=8.5,leading=15),
        Spacer(1,12),
        p("SK = Standard Kandungan. SP = Standard Pembelajaran. Satu baris = satu PdP.",size=8,leading=12,strong=True),
        Spacer(1,6),
        p("DRAF UNTUK SEMAKAN GURU. Minggu dan tarikh dalam jadual ialah panduan "
          "sumber sahaja. Semak cuti negeri/gantian, jadual waktu, DSKP dan "
          "halaman buku sebelum pelaksanaan.",size=8,leading=13,color="#735d36"),
        PageBreak()
    ]
    headings = ("MINGGU / TARIKH", "UNIT / TAJUK / PDP",
                "SK", "SP", "CATATAN / BAHAN")
    table_rows = [[p(t,size=8.0,leading=11.7,strong=True,color="#25323a") for t in headings]]
    for row in records:
        week = row.get("week","").strip() or "Belum ditetapkan"
        weektext = (f"{week}\nKumpulan A:\n{range_text(row,'a')}"
                    f"\nKumpulan B:\n{range_text(row,'b')}")
        unit_lines=[
            p(f"PdP {row['id']}",size=8.1,leading=12,strong=True),
            p(row["unit"].strip(),size=8,leading=12,strong=True),
        ]
        if row.get("topic","").strip():
            unit_lines.append(p(row["topic"].strip(),size=7.8,leading=11.6))
        table_rows.append([
            p(weektext,size=7.0,leading=11.3),
            unit_lines,
            p(row["sk"],size=8,leading=12),
            p(row["sp"],size=7.8,leading=11.8),
            p(row["note"],size=7.6,leading=11.5)
        ])
    widths = [114, 196, 95, 123, usable - 114 - 196 - 95 - 123]
    if any(x < 0 for x in widths) or abs(sum(widths)-usable)>0.2:
        raise ValueError("RPT layout width overflows landscape A4")

    tbl = LongTable(table_rows, colWidths=widths, repeatRows=1, hAlign="LEFT",
                    splitByRow=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),soft),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,paper]),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),7),
        ("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,0),9),
        ("BOTTOMPADDING",(0,0),(-1,0),9),
        ("TOPPADDING",(0,1),(-1,-1),9),
        ("BOTTOMPADDING",(0,1),(-1,-1),9),
        ("LINEBELOW",(0,0),(-1,-1),0.35,line),
        ("LINEBEFORE",(1,0),(-1,-1),0.3,line),
        ("BOX",(0,0),(-1,-1),0.6,ink)
    ]))
    story = cover + [tbl]
    doc.build(story, onFirstPage=header, onLaterPages=header)
    if not out.is_file() or out.stat().st_size < 5000:
        raise ValueError("RPT preview PDF output invalid")
    return out
