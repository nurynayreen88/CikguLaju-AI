#!/usr/bin/env python3
"""Offline BA RPH staging preview: Markdown -> one-page A4 DOCX/PDF.
Never reads or writes production DB, Telegram or Web data; does not approve RPH.
"""
from __future__ import annotations
import argparse
import re
import shutil
import subprocess
from pathlib import Path
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")
SECTIONS = (
    ("Set induksi", ("Set induksi",)),
    ("Aktiviti 1", ("Aktiviti 1",)),
    ("Aktiviti 2", ("Aktiviti 2",)),
    ("Pengukuhan / PBD", ("Pengukuhan", "Penilaian (PBD)", "PBD")),
    ("Penutup", ("Penutup",)),
)

def fields(markdown: str) -> tuple[str, dict[str, str]]:
    title = "RPH Bahasa Arab"
    result = {}
    for ln in markdown.splitlines():
        ln = ln.strip()
        if ln.startswith("# "):
            title = ln[2:].split(" (DRAF")[0].strip()
        for part in re.split(r"\s+\|\s+", ln):
            match = re.match(r"^\*\*(.*?)\*\*:?[ \t]*(.*)$", part)
            if match:
                key = match.group(1).strip().rstrip(":")
                value = match.group(2).strip()
                if value:
                    result[key] = value
    return title, result

def first(src: dict[str, str], *candidates: str) -> str:
    for key in candidates:
        if key in src:
            return src[key]
    for key, value in src.items():
        if any(key.startswith(candidate) for candidate in candidates):
            return value
    return ""

def display_sk_sp(raw: str) -> str:
    """Expose only validated numeric codes in teacher-facing Word/PDF.

    The draft/source audit explanations remain available in Markdown and
    audit JSON; they must never leak into a printable teacher RPH.
    """
    match = re.match(r"^\s*(\d+\.\d+)\s*/\s*(\d+\.\d+\.\d+)", str(raw or ""))
    if not match or not match.group(2).startswith(match.group(1) + "."):
        raise ValueError("Invalid or incomplete source SK/SP; refusing printable RPH")
    return match.group(1) + " / " + match.group(2)


def font_run(paragraph, value: str, size=9.0, bold=False):
    """Keep Malay/Latin in a clear sans font; isolate Arabic RTL runs."""
    pieces = re.split(r"([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)", value)
    for segment in pieces:
        if not segment:
            continue
        arabic = bool(ARABIC.search(segment))
        run = paragraph.add_run(segment)
        run.font.size = Pt(size + 0.4 if arabic else size)
        run.bold = bold
        run.font.name = "Amiri" if arabic else "Carlito"
        if arabic:
            rpr = run._element.get_or_add_rPr()
            fonts = rpr.rFonts
            if fonts is None:
                fonts = OxmlElement("w:rFonts")
                rpr.insert(0, fonts)
            fonts.set(qn("w:cs"), "Amiri")
            rtl = OxmlElement("w:rtl")
            rtl.set(qn("w:val"), "1")
            rpr.append(rtl)


def cell_text(cell, value: str, size=8.8, bold=False):
    p = cell.paragraphs[0]
    if ARABIC.search(value) and not re.search(r"[A-Za-z]", value):
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    font_run(p, value, size, bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    tcPr = cell._tc.get_or_add_tcPr()
    margins = tcPr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tcPr.append(margins)
    for side in ("top", "left", "bottom", "right"):
        tag = qn("w:" + side)
        item = margins.find(tag)
        if item is None:
            item = OxmlElement("w:" + side)
            margins.append(item)
        item.set(qn("w:w"), "65")
        item.set(qn("w:type"), "dxa")

def render_one(text: str, dest: Path) -> dict:
    title, d = fields(text)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(1.05)
    sec.bottom_margin = Cm(1.05)
    sec.left_margin = Cm(1.15)
    sec.right_margin = Cm(1.15)
    sec.header_distance = Cm(0.5)
    sec.footer_distance = Cm(0.5)
    normal = doc.styles["Normal"]
    normal.font.name = "Carlito"
    normal.font.size = Pt(9)
    normal.paragraph_format.space_after = Pt(0)
    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.paragraph_format.space_after = Pt(3)
    font_run(heading, title, 11.3, True)
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    table.autofit = False
    table.columns[0].width = Cm(3.2)
    table.columns[1].width = Cm(15.35)
    data = [
        ("Tahun", first(d, "Tahun")),
        ("Subjek", first(d, "Subjek")),
        ("Unit / Tajuk", first(d, "Unit")),
        ("Fokus PdP", first(d, "Fokus PdP", "Fokus")),
        ("SK / SP", display_sk_sp(first(d, "DSKP SK/SP", "Kod SK/SP", "SK/SP cadangan"))),
        ("Tarikh / Masa / Kelas", "Tarikh: ____ / ____ / ______    Mula: ______    Tamat: ______    Kelas: ______________"),
        ("Objektif", first(d, "Objektif PdP", "Objektif pembelajaran", "Objektif")),
        ("Kriteria kejayaan", first(d, "Kriteria kejayaan")),
    ]
    if first(d, "Kosa kata / ayat"):
        data.append(("Kosa kata / ayat", first(d, "Kosa kata / ayat")))
    lessons = []
    for label, keys in SECTIONS:
        value = first(d, *keys)
        if value:
            lessons.append((label, value))
    if first(d, "BBM"):
        lessons.append(("BBM", first(d, "BBM")))
    if first(d, "Refleksi guru", "Refleksi"):
        lessons.append(("Refleksi", first(d, "Refleksi guru", "Refleksi")))
    for label, value in data + lessons:
        row = table.add_row()
        row.cells[0].width = Cm(3.2)
        row.cells[1].width = Cm(15.35)
        cell_text(row.cells[0], label, 8.6, True)
        cell_text(row.cells[1], value, 8.6)
    doc.core_properties.comments = "STAGING ONLY: pedagogical approval required"
    doc.save(dest)
    return {"file": dest.name, "rows": len(data) + len(lessons),
            "arabic": bool(ARABIC.search(text)), "valid_struct": len(lessons) >= 6}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pdf-check", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(args.input_dir.rglob("lesson_*.md"))
    if not paths:
        raise SystemExit("No draft MD RPH found; refusing empty build")
    results = []
    for path in paths:
        dest = args.output_dir / (path.parent.name + "_" + path.stem + ".docx")
        results.append(render_one(path.read_text(encoding="utf-8"), dest))
    if any(not r["valid_struct"] or not r["arabic"] for r in results):
        raise SystemExit("Incomplete RPH or missing Arabic data")
    if args.pdf_check:
        if not shutil.which("libreoffice") or not shutil.which("pdfinfo"):
            raise SystemExit("LibreOffice and pdfinfo required for PDF validation")
        pdfdir = args.output_dir / "_pdf_previews"
        pdfdir.mkdir(exist_ok=True)
        # LibreOffice can silently omit files when hundreds of input paths are
        # supplied in a single invocation, even with returncode 0.
        # Convert bounded batches with isolated profiles, then retry any omissions
        # individually. This is an offline, staging-only renderer.
        docx_files = sorted(args.output_dir.glob("*.docx"))
        batch_size = 24
        for batch_start in range(0, len(docx_files), batch_size):
            batch_num = batch_start // batch_size
            cmd = [
                "libreoffice",
                f"-env:UserInstallation=file:///tmp/lo_arabic_rph_staging_batch_{batch_num}",
                "--headless", "--convert-to", "pdf",
                "--outdir", str(pdfdir),
                *[str(p) for p in docx_files[batch_start:batch_start + batch_size]],
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if res.returncode:
                raise SystemExit(
                    f"PDF batch {batch_num} failed ({res.returncode}): "
                    + (res.stderr or res.stdout)[-2000:]
                )
        missing = [
            p for p in docx_files
            if not (pdfdir / p.with_suffix(".pdf").name).exists()
        ]
        for retry_no, source in enumerate(missing):
            cmd = [
                "libreoffice",
                f"-env:UserInstallation=file:///tmp/lo_arabic_rph_retry_{retry_no}",
                "--headless", "--convert-to", "pdf",
                "--outdir", str(pdfdir), str(source),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode or not (pdfdir / source.with_suffix(".pdf").name).exists():
                raise SystemExit(
                    "Missing PDF after individual retry: " + str(source)
                    + "; stdout: " + res.stdout[-1000:]
                    + "; stderr: " + res.stderr[-1000:]
                )
        for row in results:
            pdf = pdfdir / Path(row["file"]).with_suffix(".pdf")
            if not pdf.exists():
                raise SystemExit("PDF missing: " + str(pdf))
            info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
            match = re.search(r"^Pages:\s*(\d+)", info, re.MULTILINE)
            row["pages"] = int(match.group(1)) if match else 0
        errors = [(r["file"], r["pages"]) for r in results if r["pages"] != 1]
        if errors:
            raise SystemExit("One A4 page gate failed: " + repr(errors))
    print(f"RPH_STAGING_RENDER_PASS files={len(results)} Arabic=True A4=True pdf_one_page={args.pdf_check}")

if __name__ == "__main__":
    main()
