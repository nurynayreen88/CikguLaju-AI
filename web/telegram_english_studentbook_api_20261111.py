"""Read-only Telegram source for verified English Year 4 Student Book PDF excerpts.

Use the SAME in-memory lesson -> page map and local PDF chunk manifest as
Telegram's existing English textbook sender. Never invent a page from a
Lesson number, allow a whole book download, or expose service credentials.
Year 3 repaired Student Book and other years require separate source audits.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from flask import Blueprint, Response, jsonify, request
from web.telegram_verified_rpt_rph_bridge import _authorization

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "telegram-verified-english-studentbook-y4-v1"
MAX_BYTES = 8 * 1024 * 1024
PAGE_PATTERN = re.compile(r"\d{1,3}(?:\s*[–-]\s*\d{1,3})?(?:\s*,\s*\d{1,3}(?:\s*[–-]\s*\d{1,3})?)*")
CHUNK_PATTERN = re.compile(r"books/english/y4_student_book_\d{3}_\d{3}\.pdf")


def _printed_pages(raw):
    if not isinstance(raw, str) or not PAGE_PATTERN.fullmatch(raw.strip()):
        return None
    pages = []
    for part in raw.split(","):
        numbers = [int(p.strip()) for p in re.split(r"[–-]", part)]
        first, last = numbers[0], numbers[-1]
        if not 1 <= first <= last <= 177 or last - first > 3:
            return None
        pages.extend(range(first, last + 1))
    # Avoid publishing a long cut-out / supplementary section as one Lesson.
    if not 1 <= len(pages) <= 4 or len(set(pages)) != len(pages):
        return None
    return pages


def _material(year, lesson, runtime, *, root=ROOT):
    if type(year) is not int or year != 4 or type(lesson) is not int or not 1 <= lesson <= 160:
        return None
    mapping = getattr(runtime, "_Y4_SB_PAGES_V25230", None)
    manifest = getattr(runtime, "_EN_LOCAL_BOOK_CHUNKS_V25234", None)
    physical_page = getattr(runtime, "_book_physical_page_v25237", None)
    if not isinstance(mapping, dict) or not isinstance(manifest, dict) or not callable(physical_page):
        return None
    printed = _printed_pages(mapping.get(lesson))
    if not printed:
        return None
    chunks = manifest.get((4, "textbook"))
    if not isinstance(chunks, list) or len(chunks) > 25:
        return None
    root = Path(root).resolve()
    book_dir = (root / "books" / "english").resolve()
    selection = []
    for page in printed:
        try:
            physical = physical_page({"year": 4, "subject": "English", "lesson_no": lesson}, "textbook", page)
        except Exception:
            return None
        if type(physical) is not int or not 1 <= physical <= 200:
            return None
        hits = []
        for chunk in chunks:
            if not isinstance(chunk, (tuple, list)) or len(chunk) != 3:
                return None
            start, end, relative = chunk
            if (type(start) is not int or type(end) is not int
                    or not isinstance(relative, str) or not CHUNK_PATTERN.fullmatch(relative)):
                return None
            if start <= physical <= end:
                path = root / relative
                if (path.is_symlink() or not path.is_file() or path.resolve().parent != book_dir
                        or not 1024 <= path.stat().st_size <= 30 * 1024 * 1024):
                    return None
                hits.append((path, physical - start))
        if len(hits) != 1:
            return None
        selection.append(hits[0])
    label = ", ".join(str(p) for p in printed)
    return {"selection": selection, "title":
            f"English Tahun 4 • Lesson {lesson:03d} • Student Book m/s {label}"}


def _extract(material):
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    readers = {}
    for path, index in material["selection"]:
        if path not in readers:
            readers[path] = PdfReader(str(path), strict=True)
        reader = readers[path]
        if reader.is_encrypted or not 0 <= index < len(reader.pages):
            raise ValueError("Student Book mapped page absent")
        writer.add_page(reader.pages[index])
    if not 1 <= len(writer.pages) <= 4:
        raise ValueError("Unexpected Student Book page count")
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    if not 450 <= len(data) <= MAX_BYTES or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid Student Book PDF")
    return data


def create_english_studentbook_blueprint(runtime, *, root=ROOT):
    bp = Blueprint("telegram_english_y4_studentbook_extras_v1", __name__)

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
                or any(len(request.args.getlist(k)) != 1 for k in request.args)
                or request.args["year"] != "4"
                or not re.fullmatch(r"[1-9][0-9]{0,2}", request.args["lesson"])):
            return None
        return int(request.args["lesson"])

    @bp.get("/internal/rph/v1/english-extras/studentbook")
    def metadata():
        lesson = selected()
        if lesson is None:
            return jsonify({"available": False}), 404
        try:
            material = _material(4, lesson, runtime, root=root)
            if not material:
                return jsonify({"available": False}), 404
            _extract(material)
        except Exception:
            return jsonify({"available": False}), 503
        return jsonify({"source": SOURCE, "available": True, "year": 4,
                        "lesson": lesson, "title": material["title"],
                        "type": "textbook", "format": "pdf", "status": "VERIFIED_SOURCE"})

    @bp.get("/internal/rph/v1/english-extras/studentbook.pdf")
    def download():
        lesson = selected()
        if lesson is None:
            return jsonify({"error": "Invalid Student Book selection"}), 404
        try:
            material = _material(4, lesson, runtime, root=root)
            if not material:
                return jsonify({"error": "Student Book page not mapped"}), 404
            data = _extract(material)
        except Exception:
            return jsonify({"error": "Student Book source unavailable"}), 503
        response = Response(data, mimetype="application/pdf")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y4_Lesson_{lesson:03d}_StudentBook.pdf"'
        )
        return response

    return bp
