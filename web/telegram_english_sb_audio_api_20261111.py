"""Read-only Web access to the existing Telegram English Year 2–4 materials."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from threading import Lock
from time import monotonic
import re

from flask import Blueprint, Response, jsonify, request
from web.telegram_verified_rpt_rph_bridge import _authorization
from web.english_y4_wrong_book_audio_hold_20261105 import HOLD_LESSONS
from resources.english.y3.student_book_repaired_source import (
    YEAR3_SB_DRIVE_FILE_ID, YEAR3_SB_PAGE_COUNT,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "telegram-english-lesson-locked-assets-v1"
BOOK_PARTS = {
    "Tahun 2": frozenset(("y12_student_041_060.pdf", "y12_student_061_080.pdf",
                         "y12_student_081_120.pdf")),
    "Tahun 4": frozenset(("y4_student_001_020.pdf", "y4_student_021_100.pdf",
                         "y4_student_101_177.pdf")),
}
MAX_PDF = 8 * 1024 * 1024
MAX_AUDIO = 12 * 1024 * 1024
WMA_HEADER = bytes.fromhex("3026b2758e66cf11a6d900aa0062ce6c")
ID = re.compile(r"[A-Za-z0-9_-]{15,100}\Z")
REF = re.compile(r"CD[1-9][0-9]? Track [1-9][0-9]{0,2}\Z")
# Primary Year 4 SK SOW, printed pp. 81, 145 and 203. Match the exact
# legacy reference so a future correction cannot be silently overridden.
YEAR4_STUDENT_BOOK_CORRECTIONS = {
    43: ("27, 28, 29, 30, 31", [121]),
    103: ("73, 74–75", [73]),
    157: ("110", [110, 111]),
}

# Super Minds 1 First Edition. Page ranges and track order must match
# the current Telegram lesson record. File IDs are checked against
# the original Telegram WMA sender by the parity tests.
YEAR2_AUDIO = {
    2: ((58, 58), {"CD2-18": "14nIKU6l5utMudXb9HS8Zc9aZsYOVul1a",
                   "CD2-19": "1xL916QiLasf1dO35exMZ1LgypwNwrkLC"}),
    4: ((60, 60), {"CD2-23": "1NINHVmxH_tX1sO2WGYDAgfmIZh5i-Mqh"}),
    11: ((61, 61), {"CD2-25": "1dZfNW0fnedxJjSARaHw2fIi8x_k0-vO4",
                    "CD2-26": "1vpNkB4OWao5iPQvHzEpemQrlNiNhkX4H"}),
    14: ((64, 64), {"CD2-31": "1bohxCDWg5pwB4IZnpibBlFoM3z6FkPyP"}),
    21: ((66, 66), {"CD2-33": "1bg-g73NV1eIgVL8qKi4BxwDz7dUiQYm9"}),
    23: ((68, 68), {"CD2-34": "1nk3TNOEUIL7gjIuR7LRFoaKHATh46E_P"}),
    26: ((70, 70), {"CD2-35": "1ZxYROG_L291L8WWIq2_J3NZDiW8giBkK",
                    "CD2-36": "1DZnb_IvBrqYfNZqWxuliQlJ-uGPgqIz9"}),
    31: ((71, 71), {"CD2-37": "1lALVLnBi4r9FgV_RXo6vaZIjfmioonEu"}),
    32: ((73, 73), {"CD2-43": "1fiMT41Y9PYMVBaYN5D_adxhrYMoBbr11"}),
    33: ((74, 75), {"CD2-45": "1ZV1aYbfSnulRINSzl2Cd1JJPtqUfAG1X"}),
    35: ((72, 72), {"CD2-40": "1GngRTwaqv-uXxokcGy4rDZW4rAQqDug0",
                    "CD2-42": "1yxRjQaqDAgS5aA9zS_1mcQZvJvMHhyCj"}),
    41: ((75, 75), {"CD2-47": "1gVtRNiGlqST9I43FSNEN4IP-aBhTAPj1"}),
    43: ((77, 77), {"CD2-50": "12dHue3P1j6QrUMY0PJlrVRT-2pqBQ5yh"}),
    51: ((80, 80), {"CD2-51": "1fk-NenI3cLjmN1D8KSvbHyDOzzQRrlsX"}),
    57: ((83, 83), {"CD3-05": "1FM3Y5WOaR2-sAAO9cQUW9jsI3j7hxIcg"}),
    67: ((85, 85), {"CD3-08": "1Y6nG2rpOOGwKZQCwc0GbsxFtRtdOOVdh",
                    "CD3-09": "1SRZv1CganXHWXVD5WXRTQaJgqrNT8sBZ"}),
    77: ((89, 89), {"CD3-14": "1gdfLJPCySLr7czH4pTRu3TWxRYZ-Lr-s"}),
    78: ((90, 90), {"CD3-15": "1cJiT8FzVnxl3YrRIFpESLS-A16aBPC7Z"}),
    86: ((92, 92), {"CD3-16": "12GfEs-yBivczu4stIKMfm8BrS4AyYW2M"}),
    88: ((94, 94), {"CD3-17": "1vRuXvDGVqcPcIwfT3EjfAebwPKk9K8Du",
                    "CD3-18": "1pKoaMY8-6Kg_0hF8jnOBXS7_5mtXCt8a"}),
    89: ((95, 95), {"CD3-19": "1GXJmGrb4OJ6bp9vbrTGLUwbMWrN4Iv6c"}),
    107: ((100, 100), {"CD3-30": "1M01-6uPokXgXnOF78vPQZ5i0apdjDmWt"}),
    109: ((102, 102), {"CD3-32": "1ohHvL4cQ26aNIyp97qexlEOZsYA_OMbp"}),
    129: ((109, 109), {"CD3-41": "1GqLqE6EntsZACqd93g-IX-AfMIqmUwPC"}),
}


def _source_row(runtime, year, lesson, *, year2_rows=None):
    if type(year) is not int or year not in (2, 3, 4) or type(lesson) is not int or not 1 <= lesson <= 160:
        return None
    if year == 2:
        rows = (year2_rows if year2_rows is not None
                else runtime._eng12_rows("Tahun 2"))
    else:
        loader = getattr(runtime, "_en97_units", None)
        if not callable(loader):
            return None
        rows, _ = loader(f"Tahun {year}")
    if not isinstance(rows, list):
        return None
    matched = [r for r in rows if isinstance(r, dict)
               and str(r.get("lesson_no", "")).strip() == str(lesson)]
    if len(matched) != 1:
        return None
    row = matched[0]
    if year == 2 and (row.get("textbook_title") != "Super Minds 1"
                      or row.get("year_label") != "Tahun 2"
                      or row.get("subject") != "Bahasa Inggeris"
                      or "sjk" in str(row.get("notes") or "").casefold()):
        return None
    return row


def _lesson_state(row, year, lesson):
    return {"year": f"Tahun {year}", "subject": "Bahasa Inggeris",
            "lesson_no": lesson, "textbook_lesson_no": lesson,
            "quick_content_v2391": row.get("unit_title") or row.get("unit_name"),
            "_en98_selected_staging_row": row}


def _book_selection(runtime, year, lesson, *, year2_rows=None):
    row = _source_row(runtime, year, lesson, year2_rows=year2_rows)
    if row is None:
        return None
    state = _lesson_state(row, year, lesson)
    if year == 2:
        state["textbook_page_start"] = row.get("textbook_page_start")
        state["textbook_page_end"] = row.get("textbook_page_end")
        pages = runtime._en_book_pages_v25232(state, "textbook")
    elif year == 4:
        reference = runtime._en34_verified_sb_pages_v25230(row, year)
        if not reference:
            return None
        correction = YEAR4_STUDENT_BOOK_CORRECTIONS.get(lesson)
        if correction and reference == correction[0]:
            pages = correction[1]
        elif correction and reference not in (
            str(correction[1][0]), "–".join(map(str, correction[1])),
        ):
            return None
        else:
            pages = runtime._en_book_pages_v25232(state, "textbook")
    else:
        pages = runtime._en_book_pages_v25232(state, "textbook")
    minimum, maximum = {2: (58, 117), 3: (1, YEAR3_SB_PAGE_COUNT), 4: (1, 177)}[year]
    if (not isinstance(pages, list) or not 1 <= len(pages) <= 4
            or not all(type(p) is int and minimum <= p <= maximum for p in pages)
            or pages != list(range(pages[0], pages[-1] + 1))):
        return None
    if year == 3:
        source = runtime._en_book_source_v25232(state, "textbook")
        if not source or source[0] != YEAR3_SB_DRIVE_FILE_ID:
            return None
    return state, pages


def _pdf(runtime, state, pages, *, root=ROOT):
    from pypdf import PdfReader, PdfWriter
    if state["year"] == "Tahun 3":
        path = Path(runtime._drive_pdf_v25232(YEAR3_SB_DRIVE_FILE_ID))
        try:
            with path.open("rb") as source:
                reader = PdfReader(source, strict=True)
                if reader.is_encrypted or len(reader.pages) != YEAR3_SB_PAGE_COUNT:
                    raise ValueError("Unexpected Year 3 Student Book")
                writer = PdfWriter()
                for printed in pages:
                    writer.add_page(reader.pages[printed - 1])
                return _pdf_bytes(writer)
        finally:
            path.unlink(missing_ok=True)
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
                or path.name not in BOOK_PARTS[state["year"]]
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
    return _pdf_bytes(writer)


def _pdf_bytes(writer):
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    if not 400 <= len(data) <= MAX_PDF or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid selected-page PDF")
    return data


def _audio_rows(runtime, year, lesson, *, year2_rows=None):
    row = _source_row(runtime, year, lesson, year2_rows=year2_rows)
    if row is None:
        return []
    if year == 2:
        approved = YEAR2_AUDIO.get(lesson)
        if not approved or row.get("audio_status") != "VERIFIED_AUDIO":
            return []
        pages, tracks = approved
        refs = [ref.strip() for ref in str(row.get("audio_reference") or "").split(";")]
        if ((row.get("textbook_page_start"), row.get("textbook_page_end")) != pages
                or refs != list(tracks)):
            return []
        entries = []
        for ref, file_id in tracks.items():
            disc, number = ref.split("-")
            reference = f"{disc} Track {int(number)}"
            entries.append({"title": f"English Tahun 2 • Lesson {lesson:03d} • {reference}",
                            "reference": reference, "id": file_id})
        return entries
    state = _lesson_state(row, year, lesson)
    if year == 4 and (lesson == 30 or lesson in HOLD_LESSONS
            or not getattr(runtime, "CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE", False)
            or not getattr(runtime, "CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE", False)):
        return []
    # These are the same resolvers used by Telegram's selected-material sender.
    entries = (runtime._en4_audio_rows_v25257(state) if year == 4
               else runtime._lesson_media_rows_v2407(state))
    if not isinstance(entries, list) or not 1 <= len(entries) <= 4:
        return []
    seen, out = set(), []
    for item in entries:
        if not isinstance(item, dict) or item.get("verified") != 1:
            return []
        if year == 3 and (item.get("media_type") != "audio"
                          or item.get("storage_provider") != "google_drive"):
            return []
        ident = item.get("storage_file_id")
        reference = item.get("audio_reference") if year == 4 else item.get("title")
        if (not isinstance(ident, str) or not ID.fullmatch(ident)
                or not isinstance(reference, str) or not REF.fullmatch(reference)
                or ident in seen):
            return []
        seen.add(ident)
        out.append({"title": f"English Tahun {year} • Lesson {lesson:03d} • {reference}",
                    "reference": reference, "id": ident})
    return out


def _original_audio(id_, *, wma=False):
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
        if len(raw) < 1000:
            raise ValueError("Original audio is incomplete")
        if wma:
            valid = raw.startswith(WMA_HEADER)
        else:
            valid = raw.startswith(b"ID3") or (raw[0] == 0xff and (raw[1] & 0xe0) == 0xe0)
        if not valid:
            raise ValueError("Original audio format not confirmed")
        return raw
    finally:
        response.close()


def create_english_book_audio_blueprint(runtime, *, root=ROOT):
    bp = Blueprint("telegram_english_lesson_locked_book_audio", __name__)
    year2_rows, year2_expiry = None, 0.0
    year2_lock = Lock()

    def source_options(year):
        nonlocal year2_rows, year2_expiry
        if year != 2:
            return {}
        with year2_lock:
            if monotonic() >= year2_expiry:
                year2_rows = runtime._eng12_rows("Tahun 2")
                year2_expiry = monotonic() + (120 if year2_rows else 10)
        return {"year2_rows": year2_rows}

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
        if not re.fullmatch(r"[234]", request.args["year"]) or not re.fullmatch(r"[1-9][0-9]{0,2}", request.args["lesson"]):
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
        picked = _book_selection(runtime, *selected, **source_options(selected[0]))
        if not picked:
            return jsonify({"available": False}), 404
        state, pages = picked
        try:
            # Year 3 is stored on Drive. Use the verified mapping for listing
            # and open the original PDF only for a requested excerpt.
            if selected[0] != 3:
                _pdf(runtime, state, pages, root=root)
        except Exception:
            return jsonify({"available": False}), 503
        return jsonify({"source": SOURCE, "available": True,
                        "year": selected[0], "lesson": selected[1],
                        "type": "textbook", "format": "pdf",
                        "pages": pages, "status": "VERIFIED_SOURCE",
                        "title": f"English Tahun {selected[0]} • Lesson {selected[1]:03d} • Student Book m/s " + ", ".join(map(str, pages))})

    @bp.get("/internal/rph/v1/english-extras/student-book.pdf")
    def book_download():
        selected = selection()
        picked = _book_selection(runtime, *selected, **source_options(selected[0])) if selected else None
        if not picked:
            return jsonify({"error": "Student Book page not mapped"}), 404
        try:
            data = _pdf(runtime, *picked, root=root)
        except Exception:
            return jsonify({"error": "Student Book page unavailable"}), 503
        answer = Response(data, mimetype="application/pdf")
        answer.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y{selected[0]}_Lesson_{selected[1]:03d}_Student_Book.pdf"')
        return answer

    @bp.get("/internal/rph/v1/english-extras/audio")
    def audio_metadata():
        selected = selection()
        if not selected:
            return jsonify({"available": False}), 404
        rows = _audio_rows(runtime, *selected, **source_options(selected[0]))
        if not rows:
            return jsonify({"available": False}), 404
        return jsonify({"source": SOURCE, "available": True,
                        "year": selected[0], "lesson": selected[1],
                        "status": "VERIFIED_SOURCE",
                        "tracks": [{"index": i + 1, "title": r["title"],
                                    "reference": r["reference"]}
                                   for i, r in enumerate(rows)]})

    @bp.get("/internal/rph/v1/english-extras/audio.<extension>")
    def audio_download(extension):
        selected = selection(with_track=True)
        if not selected:
            return jsonify({"error": "Invalid track"}), 404
        year, lesson, index = selected
        expected, mime = ("wma", "audio/x-ms-wma") if year == 2 else ("mp3", "audio/mpeg")
        if extension != expected:
            return jsonify({"error": "Wrong original audio format"}), 404
        rows = _audio_rows(runtime, year, lesson, **source_options(year))
        if not 1 <= index <= len(rows):
            return jsonify({"error": "Unverified track"}), 404
        row = rows[index - 1]
        try:
            raw = _original_audio(row["id"], wma=year == 2)
        except Exception:
            return jsonify({"error": "Original audio unavailable"}), 503
        name = re.sub(r"[^A-Za-z0-9_-]", "_", row["reference"])
        answer = Response(raw, mimetype=mime)
        answer.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y{year}_Lesson_{lesson:03d}_{name}.{extension}"')
        return answer

    return bp
