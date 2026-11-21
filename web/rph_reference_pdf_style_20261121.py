"""Non-destructive pastel treatment for the existing native RPH PDF.

Never reconstruct, translate, redact, or reflow teacher/curriculum text. Existing
Sains/DLP/PPKI/Arabic renderers are protected by the Word reference style gate.
This is decoration ONLY; the still-pending top-right teacher header redesign
requires a separate, explicit three-table layout review.
"""
from __future__ import annotations

from pathlib import Path
import os

from web.rph_reference_style_20261121 import color_for_state

TITLES = ("RANCANGAN PENGAJARAN HARIAN", "DAILY LESSON PLAN")
LABELS = (
    "MATA PELAJARAN", "TAHUN/TINGKATAN", "KELAS", "TARIKH", "MASA",
    "BILANGAN MURID", "TAJUK", "STANDARD KANDUNGAN",
    "STANDARD PEMBELAJARAN", "OBJEKTIF PEMBELAJARAN",
    "KRITERIA KEJAYAAN", "BAHAN BANTU MENGAJAR", "EMK / NILAI",
    "KBAT / PAK21", "PENTAKSIRAN", "SET INDUKSI", "AKTIVITI UTAMA",
    "PENUTUP", "PEMULIHAN / PENGAYAAN", "REFLEKSI",
    "Subject", "Year / Form", "Class", "Date", "Time", "Number of Pupils",
    "Topic", "Main Content Standard", "Main Learning Standard",
    "Complementary Content Standard", "Complementary Learning Standard",
    "Learning Objectives", "Success Criteria", "Teaching and Learning Materials",
    "Cross-Curricular Elements / Values", "HOTS / 21st Century Learning",
    "Assessment", "Set Induction", "Main Activities", "Closure",
    "Remedial / Enrichment", "Reflection",
)
MARKER = "CikguLaju-RPH-pastel-20261121"


def _palette(code):
    if (not isinstance(code, str) or len(code) != 6
            or any(char not in "0123456789abcdefABCDEF" for char in code)):
        raise ValueError("Invalid pastel color")
    return tuple(int(code[i:i+2], 16) / 255 for i in (0, 2, 4))


def _word_bounds(page, term):
    import fitz
    return [
        fitz.Rect(bound) for bound in page.search_for(term)
        if not fitz.Rect(bound).is_empty and
        9 < fitz.Rect(bound).width < page.rect.width * .85 and
        fitz.Rect(bound).height < 33
    ]


def _existing_label_cell(page, label_box, drawings):
    import fitz
    # Prefer an already-drawn cell, if its geometry safely encloses this label.
    candidates = []
    for d in drawings:
        bounds = d.get("rect")
        if bounds is None:
            continue
        box = fitz.Rect(bounds)
        if (box.contains(label_box) and label_box.width+5 < box.width
                and box.width < page.rect.width * .65
                and label_box.height < box.height < 45
                and box.x0 >= 12 and box.x1 <= page.rect.width - 12):
            candidates.append(box)
    if candidates:
        return min(candidates, key=lambda box: box.get_area())
    # On some native PDFs each two-column row is a single full-width rectangle.
    # Use the EXISTING vertical divider, not a guessed table-column width.
    for d in drawings:
        bounds = d.get("rect")
        if bounds is None:
            continue
        row = fitz.Rect(bounds)
        if (not row.contains(label_box) or not 12 < row.height < 46
                or row.width < page.rect.width * .65):
            continue
        dividers = []
        for line in drawings:
            if line.get("rect") is None:
                continue
            edge = fitz.Rect(line["rect"])
            if (edge.width < 1.5 and edge.height >= row.height-3
                    and row.x0+55 < edge.x0 < min(row.x1-55, row.x0+page.rect.width*.5)
                    and edge.y0 <= row.y0+2 and edge.y1 >= row.y1-2):
                dividers.append(edge.x0)
        if dividers and label_box.x1 < min(dividers):
            return fitz.Rect(row.x0, row.y0, min(dividers), row.y1)
    # ReportLab native RPH often draws the grid with individual line
    # strokes (not closed cell rectangles). Infer ONLY from the real outer
    # horizontal rules and a full-height vertical divider; never guess a
    # column width from label text or shade the activity/value column.
    horizontal = []
    vertical = []
    for shape in drawings:
        if shape.get("rect") is None:
            continue
        line = fitz.Rect(shape["rect"])
        if line.height < 1.5 and line.width >= page.rect.width * .55:
            horizontal.append(line)
        if line.width < 1.5 and line.height >= 12:
            vertical.append(line)
    segments = []
    for top in horizontal:
        if top.y0 > label_box.y0 or top.x0 > label_box.x0 + 3:
            continue
        for bottom in horizontal:
            if not (bottom.y0 >= label_box.y1
                    and top.x0-1 <= bottom.x0 <= top.x0+1
                    and abs(top.x1-bottom.x1) < 2
                    and 12 < bottom.y0-top.y0 < 52):
                continue
            dividers = [
                line.x0 for line in vertical
                if (top.x0+45 < line.x0 < top.x0+page.rect.width*.5
                    and line.y0 <= top.y0+2
                    and line.y1 >= bottom.y0-2)
            ]
            if dividers and label_box.x1 < min(dividers)-2:
                segments.append(fitz.Rect(top.x0, top.y0, min(dividers), bottom.y0))
    # A label may lie between several sets of lines (a multi-row table).
    # Use the smallest enclosing real cell, never shade adjoining rows.
    if segments:
        return min(segments, key=lambda box: box.get_area())
    return fitz.Rect(label_box.x0-3, label_box.y0-1,
                     label_box.x1+3, label_box.y1+1)


def _outer_table_horizontal_bounds(page, title, drawings):
    """Find a repeated, full-width existing table span; never guess margins.

    ReportLab native RPH often draws individual table rules. A rectangle-
    based table is supported too. Only reuse a span repeated at least twice
    below the title; labels/text-only PDFs retain their earlier title box.
    """
    import fitz

    spans = {}
    for item in drawings:
        rect = item.get("rect")
        if rect is None:
            continue
        box = fitz.Rect(rect)
        if not (page.rect.width * .63 <= box.width <= page.rect.width * .94
                and page.rect.x0 + 12 <= box.x0
                and box.x1 <= page.rect.x1 - 12
                and title.y1 + 3 < box.y0
                and box.y0 <= page.rect.y1 - 24
                and (box.height <= 1.5 or 12 <= box.height <= 110)):
            continue
        # Group tiny floating-point differences in the same actual grid.
        key = (round(box.x0, 1), round(box.x1, 1))
        spans.setdefault(key, set()).add(round(box.y0, 1))
    choices = sorted(((len(ys), k) for k, ys in spans.items()),
                     key=lambda item: (item[0], item[1][1]-item[1][0]),
                     reverse=True)
    if not choices or choices[0][0] < 2:
        return None
    left, right = choices[0][1]
    return (left, right)


def style_pdf_bytes(original, fill):
    """Return a pastel PDF with byte-identical extracted text and page geometry."""
    if not isinstance(original, bytes) or not original.startswith(b"%PDF-"):
        return original
    import fitz
    palette = _palette(fill)
    with fitz.open(stream=original, filetype="pdf") as pdf:
        if not 1 <= len(pdf) <= 4 or pdf.is_encrypted:
            return original
        if MARKER in (pdf.metadata.get("keywords") or ""):
            return original
        first = pdf[0]
        titles = [box for phrase in TITLES for box in _word_bounds(first, phrase)]
        if not titles:
            return original
        source_text = [p.get_text(sort=False) for p in pdf]
        source_sizes = [(p.rect.width, p.rect.height) for p in pdf]
        source_links = [len(p.get_links()) for p in pdf]
        title = titles[0]
        # Align the title frame with the actual outer table rules whenever
        # their geometry is sufficiently grounded. This draws decoration only:
        # every original text glyph, table and PDF link stays in place.
        drawings = first.get_drawings()
        outer = _outer_table_horizontal_bounds(first, title, drawings)
        if outer is None:
            border = fitz.Rect(title.x0-8, title.y0-4, title.x1+8, title.y1+4)
        else:
            border = fitz.Rect(outer[0], title.y0-4, outer[1], title.y1+4)
        if not first.rect.contains(border):
            return original
        first.draw_rect(border, color=(.22, .22, .22),
                        fill=palette, width=.7, overlay=False)
        for page in pdf:
            drawings = page.get_drawings()
            styled = 0
            for phrase in LABELS:
                for label in _word_bounds(page, phrase):
                    if styled >= 90:
                        break
                    if label.x0 > page.rect.width * .55:
                        continue
                    box = _existing_label_cell(page, label, drawings)
                    if not page.rect.contains(box):
                        continue
                    page.draw_rect(box, color=None, fill=palette, overlay=False)
                    styled += 1
        if ([p.get_text(sort=False) for p in pdf] != source_text
                or [(p.rect.width, p.rect.height) for p in pdf] != source_sizes
                or [len(p.get_links()) for p in pdf] != source_links):
            raise ValueError("RPH PDF content or pagination unexpectedly changed")
        meta = dict(pdf.metadata)
        meta["keywords"] = (meta.get("keywords") or "") + " " + MARKER
        pdf.set_metadata(meta)
        return pdf.tobytes(garbage=2, deflate=True)


def style_pdf_path(path, fill):
    target = Path(path)
    if target.suffix.casefold() != ".pdf" or not target.is_file():
        return False
    old = target.read_bytes()
    new = style_pdf_bytes(old, fill)
    if new == old:
        return False
    temp = target.with_name(target.name + ".style.tmp")
    try:
        temp.write_bytes(new)
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    return True


def install(runtime):
    """Wrap only the RPH PDF file output; all other generator functions remain."""
    if getattr(runtime, "_CIKGULAJU_REFERENCE_PDF_STYLE_20261121", False):
        return True
    previous = getattr(runtime, "create_pdf_file", None)
    if not callable(previous):
        return False

    def premium_pdf(state, *args, **kwargs):
        path = previous(state, *args, **kwargs)
        color = color_for_state(state)
        if color and isinstance(path, (str, os.PathLike)):
            try:
                style_pdf_path(path, color)
            except Exception as exc:
                # A cosmetic failure must not block a validated teacher download.
                print("RPH native PDF pastel skipped:",
                      type(exc).__name__, flush=True)
        return path

    runtime.create_pdf_file = premium_pdf
    runtime._CIKGULAJU_REFERENCE_PDF_STYLE_20261121 = True
    return True
