#!/usr/bin/env python3
"""Build a teacher-usable PJPK 2027 PREVIEW bundle from 338 numbered source RPH.

Outputs editable A4 DOCX, one-page A4 PDF and ZIP, without touching DB,
Telegram credits, subscriptions, any READY flag, or original source files.
Numbered candidate lessons are not asserted to be KPM's official 2027 slots.
Usage: python scripts/build_pjpk_2027_preview_bundle.py --out-dir /tmp/pjpk-export
Requires: python-docx, reportlab, pypdf, DejaVuSans font on Linux.
"""
from __future__ import annotations
import argparse
import csv
import html
import json
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from pypdf import PdfReader

from web.pjpk_2027_preview_runtime import _source, ROOT

HEAD = "RANCANGAN PENGAJARAN HARIAN"
PAGE_HEAD = "PJPK 2027 • PRATONTON DRAF • SEMAK SEBELUM GUNA"
LABELS = (
    ("Tajuk", "TAJUK"),
    ("Standard Kandungan", "SK"),
    ("Standard Pembelajaran", "SP"),
    ("Objektif pembelajaran", "OBJEKTIF"),
    ("Set induksi", "SET INDUKSI"),
    ("Aktiviti 1", "AKTIVITI 1"),
    ("Aktiviti 2", "AKTIVITI 2"),
    ("Pengukuhan / PBD", "PBD"),
    ("Penutup", "PENUTUP"),
    ("BBM", "BBM"),
    ("Keselamatan / inklusiviti", "KESELAMATAN"),
)


def _flatten(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def fields(lesson):
    src = lesson["fields"]
    act = lesson["activities"]
    safety = (src.get("keselamatan/inklusif") or src.get("keselamatan/privasi")
              or src.get("keselamatan, sensitiviti dan inklusiviti")
              or "Patuhi peraturan keselamatan sekolah.")
    return [
        ("Tajuk", lesson["title"]),
        ("Standard Kandungan", ", ".join(lesson["sk"])),
        ("Standard Pembelajaran", ", ".join(lesson["sp"])),
        ("Objektif pembelajaran", lesson["objective"]),
        ("Set induksi", src["set induksi"]),
        ("Aktiviti 1", act[0]),
        ("Aktiviti 2", act[1]),
        ("Pengukuhan / PBD", src.get("pengukuhan/pbd") or
         src.get("pengukuhan dan penilaian (pbd)") or src.get("pentaksiran/pbd") or ""),
        ("Penutup", src["penutup"]),
        ("BBM", src.get("bbm") or src.get("bahan") or "Bahan PdP sesuai."),
        ("Keselamatan / inklusiviti", safety),
    ]


def _cell_margin(cell, twips=42):
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.find(qn("w:tcMar"))
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for edge in ("top", "left", "bottom", "right"):
        tag = qn("w:" + edge)
        node = margins.find(tag)
        if node is None:
            node = OxmlElement("w:" + edge)
            margins.append(node)
        node.set(qn("w:w"), str(twips))
        node.set(qn("w:type"), "dxa")


def word(lesson, path):
    doc = Document()
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21)
    section.top_margin = Cm(0.75)
    section.bottom_margin = Cm(0.75)
    section.left_margin = Cm(1)
    section.right_margin = Cm(1)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(8.3)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 0.98

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(HEAD)
    run.bold = True
    run.font.size = Pt(12)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("%s • Tahun %d • PdP %03d" %
                  ("PENDIDIKAN JASMANI" if lesson["subject"] == "pj" else "PENDIDIKAN KESIHATAN",
                   lesson["year"], lesson["lesson"]))
    r.font.size = Pt(9)
    r.bold = True
    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(3.9)
    table.columns[1].width = Cm(15)
    initial = [("Tarikh / Hari", "____________________   /   __________"),
               ("Kelas / Masa", "____________________   /   __________")]
    for label, value in initial + fields(lesson):
        cells = table.add_row().cells
        cells[0].width, cells[1].width = Cm(3.9), Cm(15)
        for cell in cells:
            _cell_margin(cell, 24)
        for ci, text in enumerate((label, value)):
            para = cells[ci].paragraphs[0]
            para.paragraph_format.space_after = Pt(0)
            para.paragraph_format.line_spacing = 0.96
            run = para.add_run(_flatten(text))
            run.font.size = Pt(8)
            run.bold = ci == 0
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    r = p.add_run(PAGE_HEAD)
    r.font.size = Pt(7)
    r.italic = True
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))


def _font():
    candidates = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    )
    for path in candidates:
        if path.is_file():
            pdfmetrics.registerFont(TTFont("DejaVu", str(path)))
            return "DejaVu"
    raise RuntimeError("DejaVu Sans TTF required for safe Unicode PDF export")


def pdf(lesson, path):
    font = _font()
    entries = [
        ("Tarikh / Hari", "____________________   /   __________"),
        ("Kelas / Masa", "____________________   /   __________"),
    ] + fields(lesson)
    path.parent.mkdir(parents=True, exist_ok=True)
    # No truncation: progressively tighten typography until it fits one A4 page.
    for point in (8.6, 8.2, 7.8, 7.4, 7.0):
        body = ParagraphStyle("body", fontName=font, fontSize=point,
                              leading=point * 1.18, spaceAfter=0)
        label = ParagraphStyle("label", parent=body, fontName=font)
        top = ParagraphStyle("top", parent=body, alignment=TA_CENTER,
                             fontSize=11.0, leading=14)
        sub = ParagraphStyle("sub", parent=body, alignment=TA_CENTER,
                             fontSize=8.3, leading=11)
        data = [[Paragraph(html.escape(k), label),
                 Paragraph(html.escape(_flatten(v)), body)] for k, v in entries]
        table = Table(data, colWidths=[40*mm, 148*mm], hAlign="CENTER")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEBELOW", (0, 0), (-1, -1), .28, colors.HexColor("#B9C3CB")),
        ]))
        doc = SimpleDocTemplate(
            str(path), pagesize=A4, leftMargin=10*mm, rightMargin=10*mm,
            topMargin=8*mm, bottomMargin=9*mm, allowSplitting=0)
        story = [
            Paragraph(HEAD, top),
            Paragraph("%s • Tahun %d • PdP %03d" %
                      ("PENDIDIKAN JASMANI" if lesson["subject"] == "pj"
                       else "PENDIDIKAN KESIHATAN", lesson["year"], lesson["lesson"]), sub),
            Spacer(1, 3*mm), table, Spacer(1, 2*mm),
            Paragraph(html.escape(PAGE_HEAD), sub),
        ]
        doc.build(story)
        if len(PdfReader(str(path)).pages) == 1:
            return point
    raise RuntimeError("A4 overflow without truncation: %s" % path)


def build(out_dir, *, root=ROOT, limit=None):
    root = Path(root)
    out_dir = Path(out_dir)
    doc_dir, pdf_dir = out_dir / "Word", out_dir / "PDF"
    manifest = []
    count = 0
    for short_subject in ("pj", "pk"):
        for year in range(2, 7):
            maximum = (37, 38, 34, 33, 34)[year - 2] if short_subject == "pj" else (
                35 if year == 2 else 32)
            for num in range(1, maximum + 1):
                lesson = _source(year, short_subject, num, root=root)
                if lesson is None:
                    if (year, short_subject, num) == (6, "pj", 33):
                        continue  # explicitly blocked source conflict
                    raise RuntimeError("Unexpected missing numbered source %d %s %03d"
                                       % (year, short_subject, num))
                stem = "RPH_PJPK_%s_Tahun%d_PdP%03d" % (
                    short_subject.upper(), year, num)
                word(lesson, doc_dir / (stem + ".docx"))
                font_pt = pdf(lesson, pdf_dir / (stem + ".pdf"))
                manifest.append([year, short_subject.upper(), num, lesson["title"],
                                 stem + ".docx", stem + ".pdf", font_pt, "PRATONTON_DRAF"])
                count += 1
                if limit and count >= limit:
                    break
            if limit and count >= limit:
                break
        if limit and count >= limit:
            break
    if not limit and count != 338:
        raise RuntimeError("Expected 338 printable RPH, got %d" % count)
    out_dir.mkdir(parents=True, exist_ok=True)
    index = out_dir / "MANIFEST_PRATONTON.csv"
    with index.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(("Tahun", "Subjek", "PdP", "Tajuk", "Word", "PDF",
                    "PDF_font_pt", "Status"))
        w.writerows(manifest)
    readme = out_dir / "BACA_DULU.txt"
    readme.write_text(
        "CIKGULAJU PJPK 2027 — PRATONTON DRAF\n\n"
        "338 RPH bernombor; PJ T2–T6 dan PK T2–T6.\n"
        "PJ Tahun 6 PdP 033 tidak disertakan: konflik DSKP/RPT.\n"
        "Sisipan Akuatik Tahun 2 tidak disertakan: keselamatan belum diluluskan.\n"
        "Tahun 1 KP2027 belum disertakan. Semua Lesson PK ialah urutan cadangan.\n"
        "Tarikh, masa dan kelas perlu diisi mengikut jadual guru dan negeri.\n"
        "Semak aktiviti, buku teks dan pentaksiran sebelum digunakan di kelas.\n"
        "Tiada status READY atau pengesahan rasmi KPM didakwa.\n",
        encoding="utf-8")
    output = out_dir.parent / ("PJPK_2027_RPH_%d_PRATONTON.zip" % count)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        for folder in (doc_dir, pdf_dir):
            for path in sorted(folder.iterdir()):
                z.write(path, arcname=path.relative_to(out_dir))
        for path in (index, readme):
            z.write(path, arcname=path.name)
    result = {"count": count, "word": count, "pdf": count,
              "one_page_pdf": count, "zip": str(output),
              "zip_bytes": output.stat().st_size}
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    build(args.out_dir, root=args.root, limit=args.limit)
