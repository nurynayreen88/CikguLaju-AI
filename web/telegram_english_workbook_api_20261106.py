"""Private, read-only English Workbook material delivery for matched Lessons.

The repository already contains Year 2–4 workbook page maps and split PDF
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


def _material(year: int, lesson: int, *, root=ROOT):
    if type(year) is not int or year not in (2, 3, 4):
        return None
    if type(lesson) is not int or not 1 <= lesson <= 160:
        return None

    if year == 2:
        from resources.english.y2.workbook_download_router import resolve_lesson
        matched = resolve_lesson(lesson, root=root)
        if not matched:
            return None
        path = Path(matched["path"])
        first = matched["part_page_start"]
        last = matched["part_page_end"]
        printed = f"{matched['source_page_start']}–{matched['source_page_end']}"
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
    root_books = (Path(root) / "books" / "english").resolve()
    try:
        if (path.is_symlink() or not path.is_file()
                or path.resolve().parent != root_books
                or not 1024 <= path.stat().st_size <= MAX_SOURCE_SIZE
                or type(first) is not int or type(last) is not int
                or not 1 <= first <= last or last - first > 3):
            return None
    except (OSError, ValueError):
        return None
    return {"path": path, "first": first, "last": last,
            "label": f"English Tahun {year} • Lesson {lesson:03d} • Buku Aktiviti m/s {printed}"}


def _extract(material):
    """Return only the identified PDF pages, never a whole source book part."""
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(str(material["path"]), strict=True)
    if reader.is_encrypted or material["last"] > len(reader.pages):
        raise ValueError("Workbook mapped PDF page absent")
    writer = PdfWriter()
    for page in range(material["first"], material["last"] + 1):
        writer.add_page(reader.pages[page - 1])
    data = BytesIO()
    writer.write(data)
    result = data.getvalue()
    if not 450 <= len(result) <= 8 * 1024 * 1024 or not result.startswith(b"%PDF-"):
        raise ValueError("Workbook PDF output invalid")
    return result



def _student_book_material(runtime, year: int, lesson: int, *, root=ROOT):
    """Resolve only Telegram's VERIFIED Y4 main Student Book pages.

    Keep the Telegram main/supplementary page distinction, page-offset
    overrides, and local source-chunk manifest; do not infer pages from Lesson.
    """
    if (year != 4 or type(lesson) is not int or not 1 <= lesson <= 160
            or runtime is None):
        return None
    resolver = getattr(runtime, "_en34_verified_sb_pages_v25230", None)
    numbers = getattr(runtime, "_v25232_nums", None)
    physical_page = getattr(runtime, "_book_physical_page_v25237", None)
    catalog = getattr(runtime, "_EN_LOCAL_BOOK_CHUNKS_V25234", None)
    if (not all(callable(fn) for fn in (resolver, numbers, physical_page))
            or not isinstance(catalog, dict)):
        return None
    try:
        printed = resolver({"lesson_no": lesson}, 4)
        pages = numbers("m/s " + str(printed)) if printed else []
        # A main SB activity should never result in the entire book or a
        # supplementary cut-out being exposed as a Lesson download.
        if (not isinstance(pages, list) or not 1 <= len(pages) <= 4
                or any(type(p) is not int or p < 1 for p in pages)
                or pages != list(range(pages[0], pages[-1] + 1))):
            return None
        chunks = catalog.get((4, "textbook"))
        if not isinstance(chunks, (list, tuple)):
            return None
        books = (Path(root) / "books" / "english").resolve()
        selected = []
        for page in pages:
            physical = int(physical_page({"year": "Year 4", "subject": "English"},
                                         "textbook", page))
            matches = [row for row in chunks
                       if isinstance(row, (tuple, list)) and len(row) == 3
                       and type(row[0]) is int and type(row[1]) is int
                       and row[0] <= physical <= row[1]]
            if len(matches) != 1:
                return None
            start, end, rel = matches[0]
            if (not isinstance(rel, str)
                    or not re.fullmatch(r"books/english/y4_student_book_[0-9]{3}_[0-9]{3}\.pdf", rel)):
                return None
            path = Path(root) / rel
            if (path.is_symlink() or not path.is_file()
                    or path.resolve().parent != books
                    or not 1024 <= path.stat().st_size <= 70 * 1024 * 1024):
                return None
            selected.append((path, physical - start))
        span = str(pages[0]) if len(pages) == 1 else f"{pages[0]}–{pages[-1]}"
        return {"parts": selected,
                "label": f"English Tahun 4 • Lesson {lesson:03d} • Student Book m/s {span}"}
    except (OSError, TypeError, ValueError, OverflowError, KeyError, IndexError):
        return None


def _extract_student_book(material):
    from pypdf import PdfReader, PdfWriter
    readers, writer = {}, PdfWriter()
    for path, index in material["parts"]:
        if path not in readers:
            reader = PdfReader(str(path), strict=True)
            if reader.is_encrypted:
                raise ValueError("Encrypted Student Book source")
            readers[path] = reader
        reader = readers[path]
        if not 0 <= index < len(reader.pages):
            raise ValueError("Student Book source page unavailable")
        writer.add_page(reader.pages[index])
    output = BytesIO()
    writer.write(output)
    raw = output.getvalue()
    if not 450 <= len(raw) <= 8 * 1024 * 1024 or not raw.startswith(b"%PDF-"):
        raise ValueError("Student Book excerpt invalid")
    return raw


def create_english_workbook_blueprint(runtime=None):
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
        if (not re.fullmatch(r"[2-4]", raw_year)
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
        except (OSError, ValueError, ImportError, Exception):
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


    @bp.get("/internal/rph/v1/english-extras/student-book")
    def student_book_metadata():
        year, lesson, _ = selected()
        material = _student_book_material(runtime, year, lesson)
        if not material:
            return jsonify({"available": False}), 404
        try:
            _extract_student_book(material)
        except Exception:
            return jsonify({"available": False}), 503
        return jsonify({"source": "telegram-verified-english-studentbook-y4-v1",
                        "available": True, "year": year, "lesson": lesson,
                        "title": material["label"], "type": "student_book",
                        "format": "pdf", "status": "VERIFIED_SOURCE"})

    @bp.get("/internal/rph/v1/english-extras/student-book.pdf")
    def student_book_download():
        year, lesson, _ = selected()
        material = _student_book_material(runtime, year, lesson)
        if not material:
            return jsonify({"error": "Student Book source not mapped"}), 404
        try:
            content = _extract_student_book(material)
        except Exception:
            return jsonify({"error": "Student Book excerpt unavailable"}), 503
        response = Response(content, mimetype="application/pdf")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y4_Lesson_{lesson:03d}_Student_Book.pdf"'
        )
        return response

    return bp
