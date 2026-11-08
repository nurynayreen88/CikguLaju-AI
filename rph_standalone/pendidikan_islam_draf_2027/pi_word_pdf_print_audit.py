"""PHYSICAL WORD -> PDF layout audit for PI 2027 DRAFTS (editor only).

Creates *temporary* DOCX per source record with preserved Unicode fields,
converts via LibreOffice with Amiri font and reports physical A4 page counts.
NOT the production Telegram/Flask renderer; NOT approval of Arabic shaping,
Jawi orthography, source citations, book/activity linkage, or academic quality.

No teaching documents are uploaded by the workflow, and no writes to live DB.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from pi_quality_audit import COUNT, HELD, REQUIRED, ROOT

LABELS = (
    ("sk", "STANDARD KANDUNGAN"),
    ("sp", "STANDARD PEMBELAJARAN"),
    ("objektif", "OBJEKTIF"),
    ("set_induksi", "SET INDUKSI"),
    ("aktiviti_utama", "AKTIVITI UTAMA"),
    ("pentaksiran", "PENTAKSIRAN / PBD"),
    ("penutup", "PENUTUP"),
    ("bahan", "BAHAN"),
)
A4 = (595.28, 841.89)
SCRIPT_REVIEW_HELD = {(4, 83), (6, 137), (6, 141)}
REPORT_FIELDS = ("id", "year", "lesson", "scope", "status", "pdf_pages",
                 "all_pages_a4", "one_page_a4", "pdf_bytes", "word_bytes",
                 "original_field_characters", "pdf_extracted_characters",
                 "warning_codes")


def collect_records(root=ROOT):
    all_records = []
    for year, expected in COUNT.items():
        source = json.loads((Path(root) / f"year{year}.json").read_text(encoding="utf-8"))
        if source["year"] != year or source["ready"] is not False or len(source["records"]) != expected:
            raise ValueError("Invalid year source: " + str(year))
        for record in source["records"]:
            key = (year, record["lesson"])
            if (key in HELD) != record["withheld"]:
                raise ValueError("Held record mismatch: " + record["id"])
            if key in HELD:
                all_records.append((record, "HELD_NO_CONTENT"))
                continue
            if key in SCRIPT_REVIEW_HELD:
                if record.get("staging_source_review_required") is not True:
                    raise ValueError("Critical source was silently unheld: " + record["id"])
                all_records.append((record, "CRITICAL_SOURCE_HOLD"))
                continue
            fields = record["fields"]
            if not all(isinstance(fields.get(k), str) and fields[k].strip() for k in REQUIRED):
                raise ValueError("Empty source field: " + record["id"])
            if record["verified_ready"] is not False:
                raise ValueError("Unexpected published draft: " + record["id"])
            all_records.append((record, "RENDER_PREVIEW_ONLY"))
    if len(all_records) != 696:
        raise ValueError("Catalog size drift")
    return all_records


def rtl_preferred(line):
    arabic = sum(0x0600 <= ord(ch) <= 0x08FF for ch in line)
    latin = sum(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in line)
    return arabic > latin


def set_rtl(paragraph, run):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    ppr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    ppr.append(bidi)
    rpr = run._r.get_or_add_rPr()
    rtl = OxmlElement("w:rtl")
    rtl.set(qn("w:val"), "1")
    rpr.append(rtl)


NUMERIC_RANGE_BIDI = re.compile(r"(?<![0-9])(?:[0-9]{1,3})[ \\t]*[-–][ \\t]*(?:[0-9]{1,3})(?![0-9])")

def display_bidi_safe(line):
    """Keep numeric ranges in logical order when displaying Arabic/Jawi in Word.

    LibreOffice/Word can VISUALLY invert 1-3 to 3-1 in RTL paragraphs.
    Invisible LRM markers are added only to the diagnostic document's
    display text, not to the original lesson JSON or stored ayat ranges.
    They prevent teachers from seeing 3-1 for a 1-3 Quran assignment.
    """
    if not rtl_preferred(line):
        return line
    return NUMERIC_RANGE_BIDI.sub(lambda m: "\u200e" + m.group(0) + "\u200e", line)


def add_lines(cell, text, *, base_font=8.1):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt
    from docx.oxml.ns import qn
    for i, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        # Preserve all visible source characters; add invisible LRM for ranges
        # only in Word/PDF preview to prevent visual reversal of ayat 1-3.
        run = p.add_run(display_bidi_safe(line))
        run.font.name = "Amiri" if rtl_preferred(line) else "Liberation Sans"
        run.font.size = Pt(base_font + (0.35 if rtl_preferred(line) else 0))
        run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Amiri")
        run._element.get_or_add_rPr().rFonts.set(qn("w:cs"), "Amiri")
        if rtl_preferred(line):
            set_rtl(p, run)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def make_docx(record, target):
    """One-pass diagnostic layout, not a substitute for the real bot builder."""
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.left_margin = Cm(1.0)
    sec.right_margin = Cm(1.0)
    sec.top_margin = Cm(0.8)
    sec.bottom_margin = Cm(0.75)
    sec.header_distance = Cm(0.2)
    sec.footer_distance = Cm(0.2)
    doc.styles["Normal"].font.size = Pt(8)
    doc.styles["Normal"].paragraph_format.space_after = Pt(0)

    header = doc.add_paragraph()
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.paragraph_format.space_after = Pt(2)
    rr = header.add_run(f"RPH PENDIDIKAN ISLAM  |  TAHUN {record['tahun']}  |  LESSON {record['lesson']:03d}")
    rr.bold = True
    rr.font.size = Pt(11)

    note = doc.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note.paragraph_format.space_after = Pt(3)
    rr = note.add_run("DRAF STAGING / SEMAKAN EDITOR SAHAJA — BUKAN RPH DILULUSKAN")
    rr.bold = True
    rr.font.size = Pt(6.8)

    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.columns[0].width = Cm(3.6)
    table.columns[1].width = Cm(15.2)
    source = record["fields"]
    for key, label in LABELS:
        row = table.add_row()
        row.cells[0].width = Cm(3.6)
        row.cells[1].width = Cm(15.2)
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            tcpr = cell._tc.get_or_add_tcPr()
            mar = OxmlElement("w:tcMar")
            for side in ("top", "left", "bottom", "right"):
                element = OxmlElement("w:" + side)
                element.set(qn("w:w"), "35")
                element.set(qn("w:type"), "dxa")
                mar.append(element)
            tcpr.append(mar)
        lp = row.cells[0].paragraphs[0]
        lp.paragraph_format.space_after = Pt(0)
        r = lp.add_run(label)
        r.bold = True
        r.font.size = Pt(7.2)
        # Only print the first source materials line: all remaining paragraphs
        # are kept in editor metadata, NOT claimed as actual classroom resources.
        val = source[key].splitlines()[0] if key == "bahan" else source[key]
        add_lines(row.cells[1], val, base_font=8.1)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("CikguLaju QA: Word/PDF percubaan; kelulusan akademik/Jawi belum ada")
    run.font.size = Pt(6.2)
    doc.save(str(target))


def inspect_pdf(pdf):
    from pypdf import PdfReader
    p = PdfReader(str(pdf))
    boxes = []
    chars = 0
    for page in p.pages:
        media = page.mediabox
        w, h = float(media.width), float(media.height)
        boxes.append((w, h))
        chars += len(page.extract_text() or "")
    a4 = bool(boxes) and all(abs(w - A4[0]) < 2.1 and abs(h - A4[1]) < 2.1 for w, h in boxes)
    return len(boxes), a4, chars


def render_and_check(root=ROOT, *, output, sample=0, batch_size=25):
    exe = shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:
        raise RuntimeError("LibreOffice required; cannot call this physical Word/PDF QA complete")
    rows = collect_records(root)
    if sample:
        # Selection is deterministic across year, domain, and critical lengths.
        eligible = [(r, st) for r, st in rows if st == "RENDER_PREVIEW_ONLY"]
        picked = set()
        for y in COUNT:
            items = [r for r, _ in eligible if r["tahun"] == y]
            chosen = sorted(items, key=lambda r: -sum(len(r["fields"][k]) for k in REQUIRED))[:2]
            picked.update(r["id"] for r in chosen)
            picked.update(r["id"] for r in items[:2])
        for r, _ in eligible[:max(0, sample - len(picked))]:
            picked.add(r["id"])
        rows = [(r, "NOT_IN_SAMPLE" if st == "RENDER_PREVIEW_ONLY" and r["id"] not in picked else st)
                for r, st in rows]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = []
    conversion_errors = []
    with tempfile.TemporaryDirectory(prefix="cikgulaju_pi_print_") as tmp:
        root_temp = Path(tmp)
        word_dir, pdf_dir = root_temp / "word", root_temp / "pdf"
        word_dir.mkdir()
        pdf_dir.mkdir()
        work = []
        for rec, status in rows:
            item = {
                "id": rec["id"], "year": rec["tahun"], "lesson": rec["lesson"],
                "scope": "REVIEW_ONLY_WORD_TO_LIBREOFFICE_PDF_NOT_RUNTIME",
                "status": status, "pdf_pages": None,
                "all_pages_a4": None, "one_page_a4": False,
                "pdf_bytes": 0, "word_bytes": 0,
                "original_field_characters": 0, "pdf_extracted_characters": 0,
                "warning_codes": "",
            }
            if status == "RENDER_PREVIEW_ONLY":
                word_file = word_dir / (rec["id"] + ".docx")
                make_docx(rec, word_file)
                item["word_bytes"] = word_file.stat().st_size
                item["original_field_characters"] = sum(len(rec["fields"][k]) for k in REQUIRED)
                work.append((word_file, item))
            report.append(item)
        for offset in range(0, len(work), batch_size):
            batch = work[offset:offset + batch_size]
            cmd = [exe, "-env:UserInstallation=file://" + str(root_temp / "profile"),
                   "--headless", "--convert-to", "pdf", "--outdir", str(pdf_dir)]
            cmd.extend(str(path) for path, _ in batch)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=360)
            if result.returncode != 0:
                conversion_errors.append({
                    "offset": offset,
                    "returncode": result.returncode,
                    "stderr_tail": result.stderr[-600:],
                })
            for word_file, item in batch:
                pdf_path = pdf_dir / (word_file.stem + ".pdf")
                if not pdf_path.is_file():
                    item["status"] = "FAILED_TO_CONVERT"
                    item["warning_codes"] = "NO_PDF"
                    continue
                try:
                    pages, a4, chars = inspect_pdf(pdf_path)
                    item["pdf_pages"] = pages
                    item["all_pages_a4"] = a4
                    item["one_page_a4"] = pages == 1 and a4
                    item["pdf_bytes"] = pdf_path.stat().st_size
                    item["pdf_extracted_characters"] = chars
                    warnings = []
                    if not a4:
                        warnings.append("NOT_A4")
                    if pages != 1:
                        warnings.append("PAGE_COUNT_" + str(pages))
                    if chars == 0:
                        warnings.append("NO_EXTRACTABLE_TEXT_REVIEW_VISUALLY")
                    item["warning_codes"] = "|".join(warnings)
                except Exception as exc:
                    item["status"] = "PDF_READ_ERROR"
                    item["warning_codes"] = type(exc).__name__ + ":" + str(exc)[:120]
    stats = Counter(x["status"] for x in report)
    count_rendered = sum(1 for x in report if x["status"] == "RENDER_PREVIEW_ONLY")
    passed = sum(1 for x in report if x["one_page_a4"])
    result = {
        "purpose": "Physical layout & Word/PDF generation audit; isolated review, NOT production builder",
        "academic_quality_certified": False,
        "jawi_shaping_visual_approval": "NOT_PERFORMED",
        "teacher_publication": "NO_GO",
        "full_catalog": 696,
        "held": stats["HELD_NO_CONTENT"],
        "critical_source_hold": stats["CRITICAL_SOURCE_HOLD"],
        "rendered": count_rendered,
        "one_page_a4": passed,
        "one_page_percent_of_rendered": round(100 * passed / count_rendered, 2) if count_rendered else None,
        "multi_page": sum(1 for x in report if isinstance(x["pdf_pages"], int) and x["pdf_pages"] > 1),
        "conversion_failures": sum(1 for x in report if x["status"] in ("FAILED_TO_CONVERT", "PDF_READ_ERROR")),
        "conversion_error_batches": conversion_errors,
        "by_year": {
            str(y): {
                "rendered": sum(1 for x in report if x["year"] == y and x["status"] == "RENDER_PREVIEW_ONLY"),
                "one_page_a4": sum(1 for x in report if x["year"] == y and x["one_page_a4"]),
                "non_one_page_ids": [x["id"] for x in report
                                     if x["year"] == y and x["status"] == "RENDER_PREVIEW_ONLY"
                                     and not x["one_page_a4"]],
            } for y in COUNT
        },
        "rows": report,
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with output.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as dest:
        writer = csv.DictWriter(dest, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(report)
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "by_year")},
                     ensure_ascii=False, indent=2), flush=True)
    print("PI_PRINT_QA_YEAR_COUNTS", json.dumps(result["by_year"], ensure_ascii=False), flush=True)
    if not sample and count_rendered != 687:
        raise ValueError("Expected 687 preview records after six held and three critical source holds")
    if result["conversion_failures"]:
        raise RuntimeError("Word/PDF conversion failed; inspect report artifact")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=25)
    args = parser.parse_args()
    render_and_check(output=args.output, sample=args.sample, batch_size=args.batch_size)
