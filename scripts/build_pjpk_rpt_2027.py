#!/usr/bin/env python3
"""Build PJPK 2027 editable RPT DOCX + searchable landscape A4 PDFs.

The source of truth for Lesson identities is the 339-record candidate manifest;
all activity/PBD summaries come from corresponding source RPH Markdown, except
the deliberately blocked PJ Year6 PdP033. No source is promoted to READY.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import textwrap
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Cm, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"
YEARS = range(2, 7)
NAMES = {"PJ": "Pendidikan Jasmani", "PK": "Pendidikan Kesihatan"}
HEADER = "CIKGULAJU AI | RPT PJPK 2027"
NOTICE = "DRAF CADANGAN - semak tarikh PdP, cuti negeri, buku teks dan DSKP sebelum guna"
COL_HEADERS = ("PdP", "Komponen", "Unit / Tajuk", "SK / SP", "BT (m/s)", "Aktiviti dan pentaksiran")
COL_WIDTH = [43, 59, 126, 136, 55, 360]
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _short(text, limit=160):
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    return textwrap.shorten(s, width=limit, placeholder=" ...") if len(s) > limit else s


def _fields(path):
    src = path.read_text(encoding="utf-8")
    fields = {}
    for m in re.finditer(r"^\*\*([^*\n]+?):\*\*\s*(.*)$", src, flags=re.M):
        fields[m.group(1).strip().lower()] = m.group(2).strip()
    return fields


def _record_activity(rec):
    if rec["year"] == 6 and rec["subject"] == "PJ" and rec["pdp"] == 33:
        return ("BLOK: SK/SP sumber belum diselaraskan. RPH tidak dikeluarkan.",
                "Jangan jadikan PdP ini sebagai READY.")
    subj = rec["subject"].lower()
    path = ROOT / f"rph_standalone/pjpk/year{rec['year']}_{subj}/lesson_{rec['pdp']:03d}.md"
    if not path.is_file():
        raise ValueError(f"RPH missing: {path}")
    fields = _fields(path)
    actual_sk = re.findall(r"(?<!\d)\d+\.\d+(?![\d.])", fields.get("sk", ""))
    actual_sp = re.findall(r"(?<!\d)\d+\.\d+\.\d+(?![\d.])", fields.get("sp", ""))
    if actual_sk != rec["sk"] or actual_sp != rec["sp"]:
        raise ValueError(f"RPT/RPH SK-SP mismatch: {path}")
    activity = next((v for k, v in fields.items() if k.startswith("aktiviti 1")), "")
    pbd = (fields.get("pengukuhan/pbd") or fields.get("pentaksiran/pbd")
           or fields.get("pengukuhan dan penilaian (pbd)") or
           fields.get("pentaksiran") or "")
    if not activity or not pbd:
        raise ValueError(f"RPH lacking Activity1/PBD: {path}")
    return _short(activity, 180), _short(pbd, 145)


def _data():
    obj = json.loads(SOURCE.read_text(encoding="utf-8"))
    records, weeks = obj["records"], obj["weeks"]
    assert obj["year"] == 2027 and len(records) == 339 and len(weeks) == 38
    seen = set()
    by_year = {year: {} for year in YEARS}
    for rec in records:
        assert rec["ready"] is False
        assert rec["year"] in YEARS and rec["subject"] in NAMES
        assert rec["status"] in ("DRAF_CADANGAN", "BLOK_KONFLIK_SK_SP")
        key = (rec["year"], rec["subject"], rec["pdp"])
        if key in seen:
            raise ValueError(f"Duplicated: {key}")
        seen.add(key)
        week = int(rec["week"])
        if week < 1 or week > 38:
            raise ValueError(f"Invalid week: {key}")
        if rec["subject"] in by_year[rec["year"]].setdefault(week, {}):
            raise ValueError(f"Duplicate subject within week: {key}")
        by_year[rec["year"]][week][rec["subject"]] = dict(rec)
    for year in YEARS:
        count = {k: sum(1 for r in records if r["year"] == year and r["subject"] == k)
                 for k in ("PJ", "PK")}
        assert count == {"PJ": {2: 37, 3: 38, 4: 34, 5: 33, 6: 34}[year],
                         "PK": 35 if year == 2 else 32}
    for rec in records:
        rec["activity"], rec["assessment"] = _record_activity(rec)
        by_year[rec["year"]][rec["week"]][rec["subject"]] = rec
    return obj, by_year


def _setup_fonts():
    if not Path(FONT_REGULAR).is_file() or not Path(FONT_BOLD).is_file():
        raise RuntimeError("DejaVu Sans fonts are required for Malay PDF text.")
    pdfmetrics.registerFont(TTFont("DejaVuRPT", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("DejaVuRPT-Bold", FONT_BOLD))
    pdfmetrics.registerFontFamily("DejaVuRPT", normal="DejaVuRPT", bold="DejaVuRPT-Bold")


def _p(value, style):
    return Paragraph(html.escape(str(value)).replace("\n", "<br/>"), style)


def _pdf(year, out, weeks, records):
    _setup_fonts()
    regular = ParagraphStyle("regular", fontName="DejaVuRPT", fontSize=7, leading=10,
                             spaceAfter=0, allowWidows=0)
    small = ParagraphStyle("small", parent=regular, fontSize=6.85, leading=9.8)
    bold = ParagraphStyle("bold", parent=regular, fontName="DejaVuRPT-Bold")
    title = ParagraphStyle("title", parent=regular, fontName="DejaVuRPT-Bold",
                           fontSize=15, leading=20)
    subtitle = ParagraphStyle("subtitle", parent=regular, fontSize=8.6, leading=12)
    weekstyle = ParagraphStyle("week", parent=regular, fontName="DejaVuRPT-Bold",
                               fontSize=9, leading=12)
    width = sum(COL_WIDTH)
    story = [
        _p(f"{HEADER} | TAHUN {year}", title),
        Spacer(1, 2.5*mm),
        _p("Pendidikan Jasmani dan Pendidikan Kesihatan | Kumpulan A dan B | "
           "PdP bernombor selaras draf RPH CikguLaju", subtitle),
        _p(NOTICE, subtitle),
        Spacer(1, 3.5*mm),
    ]
    for week in weeks:
        number = week["week"]
        chunk = records.get(number, {})
        label = (f"MINGGU PENGAJARAN {number:02d}  |  Kumpulan A: {week['groupA']}  |  "
                 f"Kumpulan B: {week['groupB']}  |  Tahun 2027")
        header = [_p(x, bold) for x in COL_HEADERS]
        data = [header]
        for kind in ("PJ", "PK"):
            rec = chunk.get(kind)
            if not rec:
                continue
            notes = f"Aktiviti: {rec['activity']}\nPBD: {rec['assessment']}"
            if rec["status"] == "BLOK_KONFLIK_SK_SP":
                notes += "\nBLOK - konflik sumber SP 5.2.2, jangan jana RPH PdP ini."
            if (kind == "PJ" and "akuatik" in rec["title"].lower()) or (
                    kind == "PJ" and "selam" in rec["title"].lower()):
                notes += "\nSyarat: kemudahan dan pengawasan aktiviti air mesti disahkan."
            bt = rec["bt"]
            if str(bt).upper().startswith("BELUM"):
                bt = "BELUM SAH"
            entry = [
                _p(f"{kind} {rec['pdp']:03d}", bold),
                _p(NAMES[kind], small),
                _p(rec["title"], regular),
                _p("SK: " + ", ".join(rec["sk"]) + "\nSP: " + ", ".join(rec["sp"]), small),
                _p(bt, small),
                _p(notes, small),
            ]
            data.append(entry)
        if len(data) == 1:
            data.append([_p("—", regular), _p("Pelarasan", small),
                         _p("Tiada PdP baharu untuk slot ini.", regular),
                         _p("—", regular), _p("—", regular),
                         _p("Tentukan pengukuhan berdasarkan keperluan sekolah.", small)])
        t = Table(data, colWidths=COL_WIDTH, repeatRows=1, hAlign="LEFT")
        style = [
            ("VALIGN", (0,0),(-1,-1),"TOP"),
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#eaeef0")),
            ("BOX",(0,0),(-1,-1),.45,colors.HexColor("#aeb5b9")),
            ("INNERGRID",(0,0),(-1,-1),.22,colors.HexColor("#cbd2d6")),
            ("LEFTPADDING",(0,0),(-1,-1),5),
            ("RIGHTPADDING",(0,0),(-1,-1),5),
            ("TOPPADDING",(0,0),(-1,-1),4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]
        t.setStyle(TableStyle(style))
        # Let large week tables paginate by row; never clip, truncate or drop rows.
        story.extend([_p(label, weekstyle), t, Spacer(1, 3.5*mm)])
    story.extend([
        Spacer(1, 5*mm),
        _p("CATATAN PENTING", weekstyle),
        _p("PdP ialah identiti kandungan; minggu ialah slot cadangan. Tarikh A/B "
           "tertakluk kepada jadual guru, perayaan, cuti negeri, cuti gantian dan "
           "takwim sekolah. Tahun 1 KP2027 belum dimasukkan. Empat sisipan Akuatik "
           "Tahun 2 belum disahkan. PJ Tahun 6 PdP 033 disekat kerana konflik SP 5.2.2. "
           "Halaman PJ Tahun 5/6 yang belum disahkan tidak direka.", subtitle),
        _p("Sumber: RPT PJ Tahun 2/3/4–6 2027 dalam Drive CikguLaju, DSKP PK "
           "Tahun 2–6, RPT induk 2027. Sila semak buku teks dan PdP sebelum mengajar.", subtitle)
    ])
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVuRPT", 7)
        canvas.setFillColor(colors.HexColor("#596269"))
        canvas.drawString(23, 13, f"CIKGULAJU AI  |  RPT PJPK Tahun {year} 2027  |  DRAF CADANGAN")
        canvas.drawRightString(landscape(A4)[0]-23,13,f"Halaman {doc.page}")
        canvas.restoreState()
    doc = SimpleDocTemplate(str(out), pagesize=landscape(A4), leftMargin=22,
                             rightMargin=22, topMargin=24, bottomMargin=29,
                             allowSplitting=0, title=f"RPT PJPK Tahun {year} 2027 DRAF")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def _docx(year, out, weeks, records):
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Cm(29.7), Cm(21)
    section.top_margin, section.bottom_margin = Cm(.9), Cm(.9)
    section.left_margin, section.right_margin = Cm(.9), Cm(.9)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(8)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0
    p = doc.add_paragraph()
    r = p.add_run(f"{HEADER} | TAHUN {year}")
    r.bold, r.font.size = True, Pt(14)
    doc.add_paragraph("Kumpulan A/B | PdP selaras RPH | DRAF untuk semakan guru")
    doc.add_paragraph(NOTICE)
    widths = [Cm(w * 0.0352778) for w in COL_WIDTH]
    for week in weeks:
        num = week["week"]
        header = doc.add_paragraph()
        header.paragraph_format.keep_with_next = True
        h = header.add_run(
            f"MINGGU {num:02d}  |  A: {week['groupA']}  |  B: {week['groupB']}")
        h.bold, h.font.size = True, Pt(9)
        table = doc.add_table(rows=1, cols=6)
        table.style = "Table Grid"
        table.autofit = False
        for cell, label, w in zip(table.rows[0].cells, COL_HEADERS, widths):
            cell.width = w
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            run = cell.paragraphs[0].add_run(label)
            run.bold, run.font.size = True, Pt(8)
        for kind in ("PJ", "PK"):
            rec = records.get(num, {}).get(kind)
            if not rec:
                continue
            info = [
                f"{kind} {rec['pdp']:03d}", NAMES[kind], rec["title"],
                "SK: "+", ".join(rec["sk"])+"\nSP: "+", ".join(rec["sp"]),
                rec["bt"], f"Aktiviti: {rec['activity']}\nPBD: {rec['assessment']}"
            ]
            if rec["status"] == "BLOK_KONFLIK_SK_SP":
                info[-1] += "\nBLOK - konflik DSKP/RPT, bukan READY."
            for cell, value, w in zip(table.add_row().cells, info, widths):
                cell.width = w
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
                paragraph = cell.paragraphs[0]
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                rr = paragraph.add_run(str(value))
                rr.font.size = Pt(7.5)
        doc.add_paragraph("")
    doc.add_paragraph("CATATAN: Tarikh A/B hanya cadangan slot; semak jadual, "
                      "cuti negeri dan sumber asal. Tahun 1 dan sisipan Akuatik T2 "
                      "tidak termasuk. PJ T6 PdP033 tidak boleh READY.")
    doc.save(str(out))


def build(outdir):
    obj, by_year = _data()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        dest_pdf = outdir / f"RPT_PJPK_Tahun_{year}_2027_DRAF.pdf"
        dest_docx = outdir / f"RPT_PJPK_Tahun_{year}_2027_DRAF.docx"
        _pdf(year, dest_pdf, obj["weeks"], by_year[year])
        _docx(year, dest_docx, obj["weeks"], by_year[year])
        if not dest_pdf.is_file() or dest_pdf.stat().st_size < 40000:
            raise ValueError(f"Invalid PDF: {dest_pdf}")
        if not dest_docx.is_file() or dest_docx.stat().st_size < 15000:
            raise ValueError(f"Invalid Word: {dest_docx}")
    (outdir / "BACA_DULU.txt").write_text(
        "RPT PJPK 2027 CikguLaju - DRAF UNTUK SEMAKAN GURU\n\n"
        "Lima PDF A4 landscape dan lima fail Word boleh sunting (Tahun 2-6).\n"
        "RPT ini berdasarkan 176 PJ dan 163 PK calon PdP, dipadankan dengan RPH sedia ada.\n"
        "Minggu adalah slot cadangan, bukan identiti PdP; tarikh cuti negeri dan\n"
        "jadual guru perlu ditentukan sekolah. Tahun 1 KP2027 tidak termasuk.\n"
        "Empat sisipan Akuatik T2 tidak termasuk. PJ Tahun 6 PdP 033 BLOK kerana\n"
        "konflik kod 5.2.2 dalam sumber. Halaman buku T5/T6 belum semua disahkan.\n"
        "Semua status DRAF, tidak disahkan sebagai RPT rasmi KPM atau READY.\n",
        encoding="utf-8")
    zipname = outdir.parent / "RPT_PJPK_2027_Tahun_2_6_DRAF_WORD_PDF.zip"
    with zipfile.ZipFile(zipname, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for f in sorted(outdir.iterdir()):
            if f.is_file():
                archive.write(f, arcname=f.name)
    print(json.dumps({
        "count": 5, "pdf": 5, "word": 5, "zip": str(zipname),
        "totals": {str(y): len([r for r in obj["records"] if r["year"] == y])
                   for y in YEARS},
    }, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    build(parser.parse_args().out_dir)
