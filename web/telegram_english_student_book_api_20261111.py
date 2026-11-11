"""Private Telegram source for exact Year 4 Student's Book Lesson PDF excerpts.

Non-destructive parity bridge for the Web. Source mapping is copied from the
existing verified Telegram Y4 _Y4_SB_PAGES_V25230 manifest, with the main-page
override for Lesson 157 from _EN34_MAIN_SB_V25231. Original PDFs are read-only.
Never infer pages from lesson number, RPH prose or an unverified PDF part.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from flask import Blueprint, Response, jsonify, request
from web.telegram_verified_rpt_rph_bridge import _authorization

ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_SIZE = 30 * 1024 * 1024
PARTS = (
    (1, 20, "y4_student_001_020.pdf"),
    (21, 100, "y4_student_021_100.pdf"),
    (101, 177, "y4_student_101_177.pdf"),
)
# The exact, existing Telegram Year 4 source pages; do not expand to Y1/Y2/Y3/Y5/Y6
# without independently checking their source PDF coordinates.
Y4_VERIFIED_MAIN_PAGES = {
    8: "8",
    11: "12–13",
    12: "14",
    13: "11",
    14: "27",
    17: "15",
    18: "15, 16",
    22: "16–17",
    24: "18–19",
    25: "18",
    27: "19",
    28: "21",
    30: "20",
    33: "118",
    34: "27",
    35: "50",
    38: "29",
    40: "30",
    41: "31",
    43: "27, 28, 29, 30, 31",
    45: "32",
    46: "33",
    48: "36",
    49: "37",
    50: "37",
    51: "38",
    52: "38",
    54: "38–39",
    56: "40",
    57: "40",
    59: "40–41",
    61: "43",
    62: "43",
    64: "48",
    65: "120",
    66: "49",
    67: "51",
    70: "52–53",
    73: "55",
    75: "57",
    76: "54",
    81: "59",
    82: "59",
    83: "60–61",
    87: "61",
    88: "62",
    91: "63",
    92: "65",
    93: "66–67",
    94: "64",
    97: "71",
    98: "71",
    100: "73",
    102: "73",
    103: "73, 74–75",
    105: "75",
    107: "66–67",
    108: "76",
    113: "81",
    115: "82",
    116: "82",
    119: "83",
    120: "84",
    121: "84–85",
    124: "86",
    125: "88–89",
    126: "87",
    129: "93",
    134: "93",
    136: "96",
    137: "97",
    139: "97",
    140: "98",
    141: "100",
    142: "99",
    145: "103",
    146: "103",
    147: "104",
    152: "106–107",
    157: "110",
    158: "109",
}

def _page_numbers(raw):
    if not isinstance(raw, str) or not re.fullmatch(r"\d{1,3}(?:[–-]\d{1,3})?(?:,\s*\d{1,3}(?:[–-]\d{1,3})?)*", raw):
        return ()
    pages = []
    for term in raw.replace("-", "–").split(","):
        bounds = [int(part) for part in term.strip().split("–")]
        lo, hi = (bounds[0], bounds[-1])
        if not 1 <= lo <= hi <= 177 or hi - lo > 3:
            return ()
        pages.extend(range(lo, hi + 1))
    # A lesson can contain several source pages, but five-plus-page citations
    # and duplicates need manual review instead of a guessed bundle.
    if len(pages) > 4 or len(pages) != len(set(pages)):
        return ()
    return tuple(pages)

def _material(year: int, lesson: int, *, root=ROOT):
    if type(year) is not int or year != 4 or type(lesson) is not int or not 1 <= lesson <= 160:
        return None
    pages = _page_numbers(Y4_VERIFIED_MAIN_PAGES.get(lesson))
    if not pages:
        return None
    base = (Path(root) / "books" / "english").resolve()
    locations = []
    try:
        for page in pages:
            segments = [(a, b, filename) for a, b, filename in PARTS if a <= page <= b]
            if len(segments) != 1:
                return None
            a, _, filename = segments[0]
            path = base / filename
            if (path.is_symlink() or not path.is_file() or path.resolve().parent != base
                    or not 1024 <= path.stat().st_size <= MAX_SOURCE_SIZE):
                return None
            locations.append((path, page - a))
    except (OSError, ValueError):
        return None
    shown = Y4_VERIFIED_MAIN_PAGES[lesson]
    return {"locations": locations, "pages": pages,
            "title": f"English Tahun 4 • Lesson {lesson:03d} • Student Book m/s {shown}"}

def _extract(material):
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    readers = {}
    for path, index in material["locations"]:
        if path not in readers:
            reader = PdfReader(str(path), strict=True)
            if reader.is_encrypted:
                raise ValueError("Encrypted textbook source")
            readers[path] = reader
        reader = readers[path]
        if index < 0 or index >= len(reader.pages):
            raise ValueError("Out of range PDF source page")
        writer.add_page(reader.pages[index])
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    if not data.startswith(b"%PDF-") or not 450 <= len(data) <= 8 * 1024 * 1024:
        raise ValueError("Invalid or oversized excerpt")
    return data

def create_english_student_book_blueprint():
    bp = Blueprint("telegram_english_student_book_extras_v1", __name__)

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
        if set(request.args) != {"year", "lesson"} or any(
                len(request.args.getlist(k)) != 1 for k in request.args):
            return None, None, None
        if not re.fullmatch(r"4", request.args["year"]) or not re.fullmatch(
                r"[1-9]\d{0,2}", request.args["lesson"]):
            return None, None, None
        year, lesson = 4, int(request.args["lesson"])
        return year, lesson, _material(year, lesson)

    @bp.get("/internal/rph/v1/english-extras/student-book")
    def metadata():
        year, lesson, material = selected()
        if material is None:
            return jsonify({"available": False}), 404
        try:
            _extract(material)
        except Exception:
            return jsonify({"available": False}), 503
        return jsonify({"source": "telegram-verified-english-y4-student-book-v1",
                        "available": True, "year": year, "lesson": lesson,
                        "title": material["title"], "type": "textbook",
                        "format": "pdf", "status": "VERIFIED_SOURCE"})

    @bp.get("/internal/rph/v1/english-extras/student-book.pdf")
    def download():
        year, lesson, material = selected()
        if material is None:
            return jsonify({"error": "Student Book not mapped"}), 404
        try:
            content = _extract(material)
        except Exception:
            return jsonify({"error": "Student Book excerpt unavailable"}), 503
        response = Response(content, mimetype="application/pdf")
        response.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y{year}_Lesson_{lesson:03d}_Student_Book.pdf"'
        )
        return response

    return bp
