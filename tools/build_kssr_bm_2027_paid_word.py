#!/usr/bin/env python3
"""Create editable KSSR BM Tahun 2–6 Word from the reviewed RPT HTML tables.

This is NOT PDF-to-DOCX conversion. It retains all source SK, SP, PdP, notes,
dates and DRAF disclosures. Original PDFs and HTML are never modified.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
import fitz

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "rpt_2027/bahasa_melayu"
PDF_DIR = ROOT / "rpt_2027/web_2027_pdfs"
OUT_DIR = ROOT / "rpt_2027/kssr_word_premium"
PDF_MANIFEST = PDF_DIR / "manifest.json"
COUNTS = {2: 164, 3: 165, 4: 165, 5: 166, 6: 165}
HEADERS = ("MINGGU", "TEMA / UNIT", "STANDARD KANDUNGAN",
           "STANDARD PEMBELAJARAN", "CATATAN / RUJUKAN")
WIDTHS = (1.45, 4.25, 4.35, 6.55, 11.0)


def _shading(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def _border(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = OxmlElement("w:" + edge)
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), "6")
        tag.set(qn("w:color"), "7893A8")
        borders.append(tag)
    tbl_pr.append(borders)


def _no_split(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))


def _repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:tblHeader"))


def _set_text(cell, text, *, bold=False, size=7.1, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.08
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if "PdP " in text:
        for token in re.split(r"(PdP\s+\d{3})", text):
            if token:
                run = p.add_run(token)
                run.bold = bold or bool(re.fullmatch(r"PdP\s+\d{3}", token))
                run.font.size = Pt(size)
                if color:
                    run.font.color.rgb = RGBColor(*color)
    else:
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(size)
        if color:
            run.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def _current_pdf_text(year, manifest):
    pdf_meta = manifest["files"][f"bahasa_melayu:{year}"]
    pdf = PDF_DIR / pdf_meta["path"]
    content = pdf.read_bytes()
    if sha256(content).hexdigest() != pdf_meta["sha256"]:
        raise AssertionError(f"Tahun {year}: existing PDF checksum mismatch")
    with fitz.open(stream=content, filetype="pdf") as opened:
        text = "\n".join(page.get_text(sort=True) for page in opened)
    seen = {int(x) for x in re.findall(r"\bPdP\s*(\d{3})\b", text)}
    return seen, pdf_meta["sha256"]


def build(year, pdf_manifest):
    src = HTML_DIR / f"RPT_BM_Tahun_{year}_2027_Format_2026_DRAF.html"
    raw = src.read_bytes()
    soup = BeautifulSoup(raw, "html.parser")
    tables = soup.select("body > table")
    if len(tables) != 44:
        raise AssertionError(f"Tahun {year}: expected 44 week tables, got {len(tables)}")
    source_ids = []
    rows_by_week = []
    for index, original in enumerate(tables, start=1):
        rows = original.select("tbody > tr")
        if not rows:
            raise AssertionError((year, index, "no rows"))
        week_cell = rows[0].find_all("td", recursive=False)[0]
        week_marker = week_cell.select_one(".wn")
        if not week_marker or int(week_marker.get_text(strip=True)) != index:
            raise AssertionError((year, index, "week mismatch"))
        week_label = " | ".join(week_cell.stripped_strings)
        expanded = []
        for row in rows:
            cells = row.find_all("td", recursive=False)
            if len(cells) == 5:
                values = [c.get_text(" ", strip=True) for c in cells[1:]]
            elif len(cells) == 4:
                values = [c.get_text(" ", strip=True) for c in cells]
            elif len(cells) == 2 and cells[1].get("colspan") == "4":
                values = [cells[1].get_text(" ", strip=True), "", "", ""]
            else:
                raise AssertionError((year, index, "invalid row shape", len(cells)))
            # Notes may reference a previous lesson; count the canonical
            # PdP marker in the HTML row, not unrelated numbers in notes.
            primary = row.select_one("span.pd")
            if primary is not None:
                match = re.fullmatch(r"PdP\s+(\d{3})", primary.get_text(" ", strip=True))
                if not match:
                    raise AssertionError((year, index, "invalid canonical PdP", primary.get_text()))
                source_ids.append(int(match.group(1)))
            expanded.append(values)
        rows_by_week.append((week_label, expanded))
    expected = list(range(1, COUNTS[year] + 1))
    if source_ids != expected:
        raise AssertionError((year, "source PdP sequence mismatch", len(source_ids), source_ids[:12]))
    pdf_ids, pdf_sha = _current_pdf_text(year, pdf_manifest)
    if set(expected) - pdf_ids:
        raise AssertionError((year, "PDF source is missing PdP identifiers", sorted(set(expected) - pdf_ids)[:20]))

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(29.7), Cm(21)
    section.top_margin, section.bottom_margin = Cm(0.9), Cm(0.9)
    section.left_margin, section.right_margin = Cm(0.9), Cm(0.9)
    section.header_distance, section.footer_distance = Cm(0.35), Cm(0.4)
    core = doc.core_properties
    core.title = f"RPT Bahasa Melayu SK Tahun {year} 2027"
    core.subject = "KSSR Semakan — RPT DRAF SEMAKAN"
    core.author = "CikguLaju"
    core.modified = datetime(2026, 11, 23, 0, 0, tzinfo=timezone.utc)
    style = doc.styles["Normal"]
    style.font.name = "Aptos"
    style.font.size = Pt(8)
    style.paragraph_format.space_after = Pt(0)

    head = section.header.paragraphs[0]
    head.text = f"CIKGULAJU   |   RPT 2027   |   BAHASA MELAYU (SK) TAHUN {year}"
    head.style = doc.styles["Caption"]
    for run in head.runs:
        run.bold = True
        run.font.color.rgb = RGBColor(34, 76, 110)
        run.font.size = Pt(7.5)

    foot = section.footer.paragraphs[0]
    foot.text = "RPT KSSR Semakan 2027   |   DRAF SEMAKAN   |   Sahkan tarikh, SK/SP dan rujukan sebelum guna"
    for run in foot.runs:
        run.font.size = Pt(7)
        run.font.color.rgb = RGBColor(90, 109, 122)

    for idx, (week_label, rows) in enumerate(rows_by_week, start=1):
        if idx > 1:
            doc.add_page_break()
        if idx == 1:
            title = doc.add_paragraph()
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rr = title.add_run("RANCANGAN PENGAJARAN TAHUNAN 2027")
            rr.bold = True
            rr.font.size = Pt(15)
            rr.font.color.rgb = RGBColor(22, 58, 85)
            subtitle = doc.add_paragraph()
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rr = subtitle.add_run(f"BAHASA MELAYU (SK) • TAHUN {year} • KSSR SEMAKAN")
            rr.bold = True
            rr.font.size = Pt(10)
            doc.add_paragraph("NAMA SEKOLAH:                           NAMA GURU:                           KELAS:")
            notice = doc.add_paragraph()
            note_run = notice.add_run("DRAF SEMAKAN — Agihan, tarikh, cuti dan padanan sumber masih tertakluk kepada pengesahan guru.")
            note_run.font.size = Pt(7.5)
            note_run.font.color.rgb = RGBColor(132, 83, 30)

        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(2)
        heading.paragraph_format.space_after = Pt(4)
        heading.paragraph_format.keep_with_next = True
        run = heading.add_run("MINGGU " + week_label)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(27, 67, 102)

        table = doc.add_table(rows=1 + len(rows), cols=5)
        table.autofit = False
        _border(table)
        for col,width in enumerate(WIDTHS):
            table.columns[col].width = Cm(width)
        for col,label in enumerate(HEADERS):
            cell = table.cell(0, col)
            cell.width = Cm(WIDTHS[col])
            _set_text(cell, label, bold=True, size=8.0, color=(22, 57, 83))
            _shading(cell, "D9E9F3")
        _repeat_header(table.rows[0])
        _no_split(table.rows[0])
        for i, values in enumerate(rows, start=1):
            row = table.rows[i]
            _no_split(row)
            _set_text(row.cells[0], f"{idx:02d}" if i == 1 else "", bold=True, size=8)
            _shading(row.cells[0], "EDF4E9")
            for col,val in enumerate(values, start=1):
                cell = row.cells[col]
                cell.width = Cm(WIDTHS[col])
                _set_text(cell, val, size=8.0)
                if i % 2 == 0:
                    _shading(cell, "F8FBFD")
        if len(rows) > 1:
            top = table.cell(1, 0)
            bottom = table.cell(len(rows), 0)
            top.merge(bottom)
        # Leave the source DRAF caveats unchanged; do not promote a week to READY.

    output = OUT_DIR / "bahasa_melayu" / f"tahun_{year}.docx"
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    if not output.read_bytes().startswith(b"PK\x03\x04"):
        raise AssertionError((year, "Word ZIP signature missing"))
    check = Document(output)
    wordtext = "\n".join(
        " ".join(cell.text for row in table.rows for cell in row.cells)
        for table in check.tables
    )
    # The first PdP id in each CATATAN cell is the canonical lesson.
    # Other cited PdPs within notes are cross-references, not extra lessons.
    parsed_ids = []
    for table in check.tables:
        for row in table.rows[1:]:
            match = re.match(r"PdP\s+(\d{3})\b", row.cells[4].text)
            if match:
                parsed_ids.append(int(match.group(1)))
    if parsed_ids != expected:
        raise AssertionError((year, "Word PdP identifiers mismatch", len(parsed_ids), parsed_ids[:12]))
    if len(check.tables) != 44:
        raise AssertionError((year, "Word week table count mismatch"))
    if "DRAF SEMAKAN" not in "\n".join(p.text for p in check.paragraphs):
        raise AssertionError((year, "missing DRAF notice"))
    return {
        "year": year,
        "path": f"bahasa_melayu/tahun_{year}.docx",
        "sha256": sha256(output.read_bytes()).hexdigest(),
        "bytes": output.stat().st_size,
        "source_html": str(src.relative_to(ROOT)),
        "source_html_sha256": sha256(raw).hexdigest(),
        "source_pdf_sha256": pdf_sha,
        "weeks": 44,
        "pdp": len(expected),
        "source_pdf_identifiers": len(pdf_ids),
        "status": "DRAF_SEMAKAN_NOT_ACADEMIC_FINAL",
        "Word_editable": True,
        "PDF_unchanged": True,
    }


def run():
    source = json.loads(PDF_MANIFEST.read_text("utf-8"))
    entries = {str(year): build(year, source) for year in COUNTS}
    if sum(x["pdp"] for x in entries.values()) != 825:
        raise AssertionError("Expected 825 original BM PdP identifiers")
    manifest = {
        "id": "kssr_bm_word_premium_from_native_html_20261123",
        "ready_for_paid_word_download": True,
        "academic_final": False,
        "no_qa_hold_promoted": True,
        "subject": "bahasa_melayu",
        "years": list(COUNTS),
        "files": entries,
        "original_pdf_manifest_untouched": True,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"years": list(COUNTS), "pdp": 825,
                      "sha256": {k:v["sha256"] for k,v in entries.items()}},
                     ensure_ascii=False))


if __name__ == "__main__":
    run()
