"""Private, read-only English Workbook material delivery for matched Lessons.

The repository already contains Year 2–6 workbook page maps and split PDF
sources. Never guess a page from a Lesson number or deliver an entire PDF part.
The Web must authenticate the teacher and bind selection to its source catalog;
this internal endpoint additionally requires the service bearer secret.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from flask import Blueprint, Response, jsonify, request
from web.telegram_verified_rpt_rph_bridge import _authorization

ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_SIZE = 30 * 1024 * 1024
PDF_PARTS = {
    3: ((1, 80, "y3_workbook_001_080.pdf"),
        (81, 96, "y3_workbook_081_096.pdf")),
    4: ((2, 60, "y4_workbook_002_060.pdf"),
        (61, 110, "y4_workbook_061_110.pdf")),
}

def _workbook_pages(year, lesson, root):
    if year == 5:
        from resources.english.y5.workbook_pdf_router import resolve_lesson
    else:
        from resources.english.y6.workbook_pdf_router import resolve_lesson
    try:
        rows = resolve_lesson(lesson)
    except ValueError:
        return None
    if not 1 <= len(rows) <= 4:
        return None
    pages = [(Path(root) / row["path"], row["part_page"]) for row in rows]
    printed = ", ".join(str(row["printed_page"]) for row in rows)
    return pages, printed


def _material(year: int, lesson: int, *, root=ROOT):
    if type(year) is not int or year not in range(2, 7):
        return None
    if type(lesson) is not int or not 1 <= lesson <= 160:
        return None

    if year in (5, 6):
        found = _workbook_pages(year, lesson, root)
        if not found:
            return None
        pages, printed = found
    elif year == 2:
        from resources.english.y2.workbook_download_router import resolve_lesson
        matched = resolve_lesson(lesson, root=root)
        if not matched:
            return None
        path = Path(matched["path"])
        first = matched["part_page_start"]
        last = matched["part_page_end"]
        printed = f"{matched['source_page_start']}–{matched['source_page_end']}"
        pages = [(path, number) for number in range(first, last + 1)]
    else:
        if year == 3:
            from resources.english.y3.workbook_verified_map import Y3_WB_VERIFIED_LESSON_MAP as verified
        else:
            from resources.english.y4.workbook_verified_map import EN4_WB_VERIFIED as verified
        rec = verified.get(lesson)
        if not isinstance(rec, dict) or type(rec.get("pdf")) is not int:
            return None
        page = rec["pdf"]
        parts = [v for v in PDF_PARTS[year] if v[0] <= page <= v[1]]
        if len(parts) != 1:
            return None
        start, _, filename = parts[0]
        path = Path(root) / "books" / "english" / filename
        first = last = page - start + 1
        printed = str(rec.get("printed") or "?")
        pages = [(path, first)]
    root_books = (Path(root) / "books" / "english").resolve()
    try:
        if not 1 <= len(pages) <= 4 or any(
            path.is_symlink() or not path.is_file()
            or path.resolve().parent != root_books
            or not 1024 <= path.stat().st_size <= MAX_SOURCE_SIZE
            or type(number) is not int or number < 1
            for path, number in pages
        ):
            return None
    except (OSError, ValueError):
        return None
    return {"pages": pages,
            "label": f"English Tahun {year} • Lesson {lesson:03d} • Buku Aktiviti m/s {printed}"}


def _extract(material):
    """Return only the identified PDF pages, never a whole source book part."""
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    readers = {}
    for path, number in material["pages"]:
        if path not in readers:
            readers[path] = PdfReader(str(path), strict=True)
        reader = readers[path]
        if reader.is_encrypted or number > len(reader.pages):
            raise ValueError("Workbook mapped PDF page absent")
        writer.add_page(reader.pages[number - 1])
    data = BytesIO()
    writer.write(data)
    result = data.getvalue()
    if not 450 <= len(result) <= 8 * 1024 * 1024 or not result.startswith(b"%PDF-"):
        raise ValueError("Workbook PDF output invalid")
    return result


def create_english_workbook_blueprint():
    bp = Blueprint("telegram_english_workbook_extras_v1", __name__)

    @bp.before_request
    def authorized():
        if not _authorization():
            return jsonify({"error": "Unauthorized"}), 401

    @bp.after_request
    def private_headers(response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Authorization"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def selected():
        if (set(request.args) != {"year", "lesson"}
                or any(len(request.args.getlist(k)) != 1 for k in request.args)):
            return None, None, None
        raw_year, raw_lesson = request.args["year"], request.args["lesson"]
        if (not re.fullmatch(r"[2-6]", raw_year)
                or not re.fullmatch(r"[1-9][0-9]{0,2}", raw_lesson)):
            return None, None, None
        year, lesson = int(raw_year), int(raw_lesson)
        return year, lesson, _material(year, lesson)

    @bp.get("/internal/rph/v1/english-extras/workbook")
    def metadata():
        year, lesson, material = selected()
        if not material:
            return jsonify({"available": False}), 404
        try:
            _extract(material)
        except Exception:
            return jsonify({"available": False}), 503
        return jsonify({"source": "telegram-verified-english-workbook-v1",
                        "available": True, "year": year, "lesson": lesson,
                        "title": material["label"], "type": "workbook",
                        "format": "pdf", "status": "VERIFIED_SOURCE"})

    @bp.get("/internal/rph/v1/english-extras/workbook.pdf")
    def download():
        year, lesson, material = selected()
        if not material:
            return jsonify({"error": "Workbook source not mapped"}), 404
        try:
            content = _extract(material)
        except Exception:
            return jsonify({"error": "Workbook PDF source unavailable"}), 503
        response = Response(content, mimetype="application/pdf")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y{year}_Lesson_{lesson:03d}_Workbook.pdf"'
        )
        return response

    return bp
