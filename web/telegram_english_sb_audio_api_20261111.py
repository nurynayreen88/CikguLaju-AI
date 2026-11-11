"""Read-only English Year 4 Lesson-locked Student Book and audio delivery.

The live Telegram SOW row, page resolver, local book parts and *guarded*
audio map remain authoritative. The service-bearer secret stays server-side.
Never expose a whole book, an unverified track, a Drive file ID or a file path.
Year 3 repaired SB and other years remain untouched until source parity QA.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

from flask import Blueprint, Response, jsonify, request
from web.telegram_verified_rpt_rph_bridge import _authorization
from web.english_y4_wrong_book_audio_hold_20261105 import HOLD_LESSONS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "telegram-english-y4-lesson-locked-assets-20261111"
BOOK_PARTS = frozenset((
    "y4_student_001_020.pdf", "y4_student_021_100.pdf",
    "y4_student_101_177.pdf",
))
MAX_PDF = 8 * 1024 * 1024
MAX_AUDIO = 12 * 1024 * 1024
ID = re.compile(r"[A-Za-z0-9_-]{15,100}\Z")
REF = re.compile(r"CD[1-9][0-9]? Track [1-9][0-9]{0,2}\Z")


def _source_row(runtime, year, lesson):
    if type(year) is not int or year != 4 or type(lesson) is not int or not 1 <= lesson <= 160:
        return None
    loader = getattr(runtime, "_en97_units", None)
    if not callable(loader):
        return None
    rows, _ = loader(f"Tahun {year}")
    if not isinstance(rows, list):
        return None
    matched = [r for r in rows if isinstance(r, dict)
               and str(r.get("lesson_no", "")).strip() == str(lesson)]
    return matched[0] if len(matched) == 1 else None


def _verified_pages(runtime, row):
    resolver = getattr(runtime, "_en34_verified_sb_pages_v25230", None)
    if not callable(resolver):
        return []
    raw = resolver(row, 4)
    if not isinstance(raw, str) or len(raw) > 45:
        return []
    clean = raw.strip().replace("–", "-")
    if not re.fullmatch(r"[0-9]{1,3}(?:\s*-\s*[0-9]{1,3})?(?:\s*,\s*[0-9]{1,3}(?:\s*-\s*[0-9]{1,3})?)*", clean):
        return []
    pages = []
    for chunk in clean.split(","):
        bounds = [int(x.strip()) for x in chunk.split("-")]
        lo, hi = bounds[0], bounds[-1]
        if not 1 <= lo <= hi <= 177 or hi - lo > 3:
            return []
        for page in range(lo, hi + 1):
            if page not in pages:
                pages.append(page)
    # Multiple separate page references are allowed, but never a large
    # cut-out/resource span or an entire book section.
    return pages if 1 <= len(pages) <= 4 else []


def _book_selection(runtime, year, lesson):
    row = _source_row(runtime, year, lesson)
    if row is None:
        return None
    pages = _verified_pages(runtime, row)
    if not pages:
        return None
    state = {"year": f"Tahun {year}", "subject": "English",
             "lesson_no": lesson, "_en98_selected_staging_row": row}
    return state, pages


def _pdf(runtime, state, pages, *, root=ROOT):
    from pypdf import PdfReader, PdfWriter
    folder = (Path(root) / "books" / "english").resolve()
    locate = getattr(runtime, "_local_book_chunk_v25234", None)
    physical = getattr(runtime, "_book_physical_page_v25237", None)
    if not callable(locate) or not callable(physical):
        raise ValueError("Original Telegram PDF-part resolver absent")
    writer, readers = PdfWriter(), {}
    for printed in pages:
        item = locate(state, "textbook", printed)
        if not isinstance(item, (tuple, list)) or len(item) != 3:
            raise ValueError("No verified local Student Book part")
        name, first, last = item
        path = Path(name)
        if (path.is_symlink() or not path.is_file()
                or path.name not in BOOK_PARTS
                or path.resolve().parent != folder
                or not 1024 <= path.stat().st_size <= 30 * 1024 * 1024
                or type(first) is not int or type(last) is not int):
            raise ValueError("Unsafe textbook part")
        actual = physical(state, "textbook", printed)
        if type(actual) is not int or not first <= actual <= last:
            raise ValueError("Unverified printed/physical page mapping")
        if path not in readers:
            readers[path] = PdfReader(str(path), strict=True)
            if readers[path].is_encrypted:
                raise ValueError("Encrypted book part")
        index = actual - first
        if index >= len(readers[path].pages):
            raise ValueError("Book page missing in original PDF")
        writer.add_page(readers[path].pages[index])
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    if not 450 <= len(data) <= MAX_PDF or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid selected-page PDF")
    return data


def _audio_rows(runtime, year, lesson):
    if _source_row(runtime, year, lesson) is None:
        return []
    # Both known Telegram audio safety guards must have installed.
    if (lesson == 30 or lesson in HOLD_LESSONS
            or not getattr(runtime, "CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE", False)
            or not getattr(runtime, "CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE", False)):
        return []
    mapping = getattr(runtime, "_EN4_AUDIO_ALL_V25259", None)
    if not isinstance(mapping, dict):
        return []
    entries = mapping.get(lesson)
    if not isinstance(entries, list) or not 1 <= len(entries) <= 4:
        return []
    seen, out = set(), []
    for item in entries:
        if not isinstance(item, dict) or item.get("verified") != 1:
            return []
        ident = item.get("storage_file_id")
        reference = item.get("audio_reference")
        title = item.get("title")
        if (not isinstance(ident, str) or not ID.fullmatch(ident)
                or not isinstance(reference, str) or not REF.fullmatch(reference)
                or not isinstance(title, str) or len(title) > 180
                or not re.search(rf"\bLesson\s+0*{lesson}\b", title, re.I)
                or ident in seen):
            return []
        seen.add(ident)
        out.append({"title": title, "reference": reference, "id": ident})
    return out


def _mp3(id_):
    import requests
    response = requests.get(
        "https://drive.usercontent.google.com/download",
        params={"id": id_, "export": "download", "confirm": "t"},
        timeout=(10, 50), stream=True, allow_redirects=True,
    )
    try:
        ctype = response.headers.get("Content-Type", "").lower()
        if response.status_code != 200 or "html" in ctype:
            raise ValueError("Original audio cannot be downloaded")
        data = bytearray()
        for chunk in response.iter_content(256 * 1024):
            if chunk:
                data.extend(chunk)
                if len(data) > MAX_AUDIO:
                    raise ValueError("Audio exceeds limit")
        raw = bytes(data)
        if (len(raw) < 1000 or
                not (raw.startswith(b"ID3") or
                     (raw[0] == 0xff and (raw[1] & 0xe0) == 0xe0))):
            raise ValueError("Original MP3 identity not confirmed")
        return raw
    finally:
        response.close()


def create_english_book_audio_blueprint(runtime, *, root=ROOT):
    bp = Blueprint("telegram_english_lesson_locked_book_audio", __name__)

    @bp.before_request
    def authorize():
        if not _authorization():
            return jsonify({"error": "Unauthorized"}), 401

    @bp.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Authorization"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def selection(with_track=False):
        allowed = {"year", "lesson", "track"} if with_track else {"year", "lesson"}
        if set(request.args) != allowed or any(len(request.args.getlist(k)) != 1 for k in allowed):
            return None
        if not re.fullmatch(r"4", request.args["year"]) or not re.fullmatch(r"[1-9][0-9]{0,2}", request.args["lesson"]):
            return None
        year, lesson = int(request.args["year"]), int(request.args["lesson"])
        if not 1 <= lesson <= 160:
            return None
        if with_track:
            track = request.args["track"]
            if not re.fullmatch(r"[1-4]", track):
                return None
            return year, lesson, int(track)
        return year, lesson

    @bp.get("/internal/rph/v1/english-extras/student-book")
    def book_metadata():
        selected = selection()
        if not selected:
            return jsonify({"available": False}), 404
        picked = _book_selection(runtime, *selected)
        if not picked:
            return jsonify({"available": False}), 404
        state, pages = picked
        try:
            _pdf(runtime, state, pages, root=root)
        except Exception:
            return jsonify({"available": False}), 503
        return jsonify({"source": SOURCE, "available": True,
                        "year": selected[0], "lesson": selected[1],
                        "type": "textbook", "format": "pdf",
                        "pages": pages, "status": "VERIFIED_SOURCE",
                        "title": f"English Tahun 4 • Lesson {selected[1]:03d} • Student Book m/s " + ", ".join(map(str, pages))})

    @bp.get("/internal/rph/v1/english-extras/student-book.pdf")
    def book_download():
        selected = selection()
        picked = _book_selection(runtime, *selected) if selected else None
        if not picked:
            return jsonify({"error": "Student Book page not mapped"}), 404
        try:
            data = _pdf(runtime, *picked, root=root)
        except Exception:
            return jsonify({"error": "Student Book page unavailable"}), 503
        answer = Response(data, mimetype="application/pdf")
        answer.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y4_Lesson_{selected[1]:03d}_Student_Book.pdf"')
        return answer

    @bp.get("/internal/rph/v1/english-extras/audio")
    def audio_metadata():
        selected = selection()
        if not selected:
            return jsonify({"available": False}), 404
        rows = _audio_rows(runtime, *selected)
        if not rows:
            return jsonify({"available": False}), 404
        return jsonify({"source": SOURCE, "available": True,
                        "year": selected[0], "lesson": selected[1],
                        "status": "VERIFIED_SOURCE",
                        "tracks": [{"index": i + 1, "title": r["title"],
                                    "reference": r["reference"]}
                                   for i, r in enumerate(rows)]})

    @bp.get("/internal/rph/v1/english-extras/audio.mp3")
    def audio_download():
        selected = selection(with_track=True)
        if not selected:
            return jsonify({"error": "Invalid track"}), 404
        year, lesson, index = selected
        rows = _audio_rows(runtime, year, lesson)
        if not 1 <= index <= len(rows):
            return jsonify({"error": "Unverified track"}), 404
        row = rows[index - 1]
        try:
            raw = _mp3(row["id"])
        except Exception:
            return jsonify({"error": "Original audio unavailable"}), 503
        name = re.sub(r"[^A-Za-z0-9_-]", "_", row["reference"])
        answer = Response(raw, mimetype="audio/mpeg")
        answer.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y4_Lesson_{lesson:03d}_{name}.mp3"')
        return answer

    return bp
