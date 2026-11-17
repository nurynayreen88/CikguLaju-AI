"""Selected-page and original audio delivery for verified English lessons."""
from __future__ import annotations

from io import BytesIO
from functools import lru_cache
from hashlib import file_digest, sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from time import monotonic
import json
import os
import re

from flask import Blueprint, Response, jsonify, request
from web.english_book_view_links import english_book_view_link, year6_sow_book_pages
from web.telegram_verified_rpt_rph_bridge import _authorization
from web.english_y4_wrong_book_audio_hold_20261105 import HOLD_LESSONS
from resources.english.y4.paired_student_book import YEAR4_SB_PAIRED_PAGES
from resources.english.y4.verified_class_audio import (
    LESSON_TRACKS as YEAR4_VERIFIED_LESSONS, RECORDINGS as YEAR4_RECORDINGS,
)
from resources.english.y3.student_book_repaired_source import (
    YEAR3_SB_DRIVE_FILE_ID, YEAR3_SB_PAGE_COUNT, YEAR3_SB_PAIRED_PAGES,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "telegram-english-lesson-locked-assets-v1"
BOOK_PARTS = {
    "Tahun 1": frozenset(("y12_student_001_040.pdf",)),
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
YEAR5_BOOK_ID = "13B4s4HacQgWn3M2QkzwHif6JdrBqc1Fw"
YEAR5_BOOK_SHA = "0f1b0263ccec6689e896ba375690e4d0cb900e00f52a86832e16411c759eff96"
YEAR5_BOOK_SIZE = 44_060_870
YEAR5_BOOK_PDF_PAGES = 122
_year5_book_lock = Lock()
YEAR6_BOOK_SIZE = 229_949_822
YEAR6_BOOK_PDF_PAGES = 145
YEAR6_EXCERPT_LIMIT = 16 * 1024 * 1024
YEAR6_BOOK_SHA = "731017be1c0b9d32ea38f3cdb641ea578eb0131467f88625a4e85f00a103b0d6"
_year6_book_lock = Lock()
# Super Minds 1 KSSR BOT_READY index, original Telegram sender IDs, and
# SHA-256 of the original WMA files for the two reviewed Web lessons.
YEAR1_AUDIO = {
    18: (("CD1 Track 12", "1eaoHB3Mv1yZWj53KaVJNY_9q7M3ag3C1",
          "54b8781eb3ea70333c3ad4ec7867a8e7454764aed871a9686bf4bd9683968e85"),
         ("CD1 Track 13", "1XHx5n_Ajd8uhnm-0kV7TzGcOu510_WBH",
          "3d36a6efe970d745e4ef57c2c55606b92ed108a954a17594806949a21bc8816c")),
    19: (("CD1 Track 14", "1y6f44jqrqq2sBSRk54qvlbntWmfx7GaK",
          "565c237f4a0bde1f2c712542a09564e1835530af9ff29867b8bae2112712e3eb"),),
}
# Primary Year 4 SK SOW, printed pp. 81, 145 and 203. Match the exact
# legacy reference so a future correction cannot be silently overridden.
YEAR4_STUDENT_BOOK_CORRECTIONS = {
    43: ("27, 28, 29, 30, 31", [121]),
    103: ("73, 74–75", [73]),
    157: ("110", [110, 111]),
}

# Super Minds 1 First Edition. Match the exact runtime lesson record before
# serving audio. File IDs are checked against the original Telegram WMA sender.
YEAR2_AUDIO = {
    2: ((58, 58), {"CD2-18": "14nIKU6l5utMudXb9HS8Zc9aZsYOVul1a",
                   "CD2-19": "1xL916QiLasf1dO35exMZ1LgypwNwrkLC"}),
    3: ((59, 59), {"CD2-20": "1T8j14lzwH_gDMg-3fHFAYAhbhIUSX61U",
                   "CD2-21": "1tytx8H50xtmemOXI-Vh0YERcy9HI5CGH",
                   "CD2-22": "1aUGlOIiWw4-lFvOtfgoJTna4NXGG5jbc"}),
    4: ((60, 60), {"CD2-23": "1NINHVmxH_tX1sO2WGYDAgfmIZh5i-Mqh"}),
    11: ((61, 61), {"CD2-25": "1dZfNW0fnedxJjSARaHw2fIi8x_k0-vO4",
                    "CD2-26": "1vpNkB4OWao5iPQvHzEpemQrlNiNhkX4H"}),
    12: ((62, 62), {"CD2-27": "10g7LyS5-rGCPgoOgPoYfw-zpBrUZVt9-",
                    "CD2-28": "1EMV_qy19Ktx3F_lPWtt3JFHPibyHt5du"}),
    13: ((63, 63), {"CD2-29": "1s-eJwkUYYRbPOBNjXRKhkuUsT1yj3C3o",
                    "CD2-30": "16LfOMCkuY-PfaToO932aSE35yGJ5jYXJ"}),
    14: ((64, 64), {"CD2-31": "1bohxCDWg5pwB4IZnpibBlFoM3z6FkPyP"}),
    20: ((65, 65), {"CD2-32": "1t44G8OrP3Zj4Rb7kWUAV_u08PUxl4HhU"}),
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
    42: ((76, 76), {"CD2-49": "1UGmgoS-CtYZLVrjna_yjqz3AbXadbVH6"}),
    43: ((77, 77), {"CD2-50": "12dHue3P1j6QrUMY0PJlrVRT-2pqBQ5yh"}),
    51: ((80, 80), {"CD2-51": "1fk-NenI3cLjmN1D8KSvbHyDOzzQRrlsX"}),
    56: ((82, 82), {"CD3-02": "1CWEtMxq1EITbN9LG_tzxESe6ETkoeUrZ",
                    "CD3-03": "17lqds1s5vGojKpMacwczirCDXWXAPyeU"}),
    57: ((83, 83), {"CD3-05": "1FM3Y5WOaR2-sAAO9cQUW9jsI3j7hxIcg"}),
    66: ((84, 84), {"CD3-06": "1Of8zmJv5QoSFsxM9mMG3mArtxhpnh19a"}),
    67: ((85, 85), {"CD3-08": "1Y6nG2rpOOGwKZQCwc0GbsxFtRtdOOVdh",
                    "CD3-09": "1SRZv1CganXHWXVD5WXRTQaJgqrNT8sBZ"}),
    68: ((86, 87), {"CD3-10": "1x7LIPuPvbl9oGZXg3fDROUVE0H-cjg_2",
                    "CD3-11": "1aFRRk2mzGa1BLhVe7kzhfqRCnCp3ZWpt"}),
    71: ((87, 87), {"CD3-12": "1PjQuJwy8SVrh4Y8sZYdFJKxKTCmtRjsh",
                    "CD3-13": "1JAfqE_ieNNsEYbhDCMH8f-rj449a23Du"}),
    77: ((89, 89), {"CD3-14": "1gdfLJPCySLr7czH4pTRu3TWxRYZ-Lr-s"}),
    78: ((90, 90), {"CD3-15": "1cJiT8FzVnxl3YrRIFpESLS-A16aBPC7Z"}),
    86: ((92, 92), {"CD3-16": "12GfEs-yBivczu4stIKMfm8BrS4AyYW2M"}),
    88: ((94, 94), {"CD3-17": "1vRuXvDGVqcPcIwfT3EjfAebwPKk9K8Du",
                    "CD3-18": "1pKoaMY8-6Kg_0hF8jnOBXS7_5mtXCt8a"}),
    89: ((95, 95), {"CD3-19": "1GXJmGrb4OJ6bp9vbrTGLUwbMWrN4Iv6c"}),
    96: ((96, 96), {"CD3-21": "1Qa9AfemBu-etancAHnryknAC1XZNK0FR",
                    "CD3-23": "1-I0iGq290CG99f0ZBMnkMPnZkuuMQzSU"}),
    97: ((97, 97), {"CD3-24": "1bns47o67HLRpXpfHXjBwY-lU3Vb8lV2p",
                    "CD3-25": "1iA-FDSGoydonKqSnOXMdfyxerMWCVXSV"}),
    98: ((98, 99), {"CD3-26": "1ZRcaKXVwlBn94woeQOX20EWyVijloFE6",
                    "CD3-27": "1ydVjR7Z9XBL5s3c47PwMkvJrg-etKOXu"}),
    106: ((99, 99), {"CD3-28": "1UKcSHeY_s6Sc5Su859fDSHD0bthksXs2",
                     "CD3-29": "1jfzvwPt92qebONMhoQMABhaPcChmG0pF"}),
    107: ((100, 100), {"CD3-30": "1M01-6uPokXgXnOF78vPQZ5i0apdjDmWt"}),
    108: ((101, 101), {"CD3-31": "1wyhMvVojLHvfhcuWQDxlPzEIjdDp69ZL"}),
    109: ((102, 102), {"CD3-32": "1ohHvL4cQ26aNIyp97qexlEOZsYA_OMbp"}),
    117: ((104, 104), {"CD3-33": "1vWg2Dw-1Vbm19JsUuqgEy21yuQyH2zOb"}),
    126: ((106, 106), {"CD3-34": "1sY7S0EVVbENv5gmUnMb0SFIujfg6XGpK",
                       "CD3-35": "1CYkpnETZJAQxFk8xacljNQD-TBS4danc"}),
    127: ((107, 107), {"CD3-36": "1UnG0RwD8flFNz0UpFgNWqJ8BgT8XzTM5",
                       "CD3-37": "1Kd0kLZo4lwM5ZbxliJHoHgn0e3PKsfvz"}),
    128: ((108, 108), {"CD3-38": "173GIORr-aUO2Iww7j9rCsOiWW3XNhXVk",
                       "CD3-40": "1uO3orq4gonX_YBzxOGI5EX3F9y_NpfbB"}),
    129: ((109, 109), {"CD3-41": "1GqLqE6EntsZACqd93g-IX-AfMIqmUwPC"}),
    136: ((110, 111), {"CD3-43": "1Lwu3pgFWQsfn5u67ErKgSs0LGtKah6Uq",
                       "CD3-44": "1rpmMiue_pZkAKTsPeTLYZZpc2ALy-wXL"}),
    137: ((111, 111), {"CD3-45": "1OZNkiZYvdD5_Cp-pywsB530Hk_QLLdzb",
                       "CD3-46": "1SRGmGyKu9cDmQyyi2RD5SjfevpaR11F5"}),
    138: ((112, 112), {"CD3-47": "1f_1TRT0kI34tYGX_VvxIJUyw8tGQttWo",
                       "CD3-48": "1rTGk7reWr8ES0kGR4-jHX_ojIens-uQj"}),
}

# Primary Year 2 SK SOW and Super Minds 1 Teacher's Book T59–T112.
# Match the exact v15 references and Workbook pages before publishing the
# audited tracks, including cases where the original reference is stale.
YEAR2_AUDIO_BOOK_EVIDENCE = {
    3: ("CD2-20; CD2-21; CD2-22", (59, 59), ("Student Book p. 59 Activity 1", "Student Book p. 59 Activity 2", "Workbook p. 59 Activity 1")),
    12: ("CD2-27; CD2-28", (62, 62), ("Student Book pp. 62–63 Activity 1", "Workbook p. 62 Activity 1")),
    13: ("CD2-29; CD2-30", (63, 63), ("Student Book p. 63 Activity 4", "Workbook p. 63 Activity 2")),
    20: ("CD2-32", (65, 65), ("Workbook p. 65 Activity 1",)),
    42: ("CD2-48", (76, 76), ("Workbook p. 76 Activity 1",)),
    56: ("CD3-01; CD3-02", (82, 82), ("Student Book p. 82 Activity 1", "Student Book p. 82 Activity 2")),
    66: ("CD3-06; CD3-07", (84, 84), ("Student Book p. 84 Activity 1",)),
    68: ("CD3-10; CD3-11", (86, 87), ("Student Book pp. 86–87 Activity 1", "Workbook p. 86 Activity 1")),
    71: ("CD3-12; CD3-13", (87, 87), ("Student Book p. 87 Activity 4", "Workbook p. 87 Activity 2")),
    96: ("CD3-20", (96, 96), ("Student Book p. 96 Activity 1", "Student Book p. 96 Activity 2")),
    97: ("CD3-21", (97, 97), ("Student Book p. 97 Activity 1", "Student Book p. 97 Activity 2")),
    98: ("CD3-27", (98, 99), ("Student Book pp. 98–99 Activity 1", "Workbook p. 98 Activity 1")),
    106: ("CD3-29", (99, 99), ("Student Book p. 99 Activity 4", "Workbook p. 99 Activity 2")),
    108: ("CD3-31", (101, 101), ("Workbook p. 101 Activity 1",)),
    117: ("CD3-34", (104, 104), ("Student Book p. 104 Activity 1",)),
    126: ("CD3-37; CD3-38", (106, 106), ("Student Book p. 106 Activity 1", "Student Book p. 106 Activity 2")),
    127: ("CD3-39", (107, 107), ("Student Book p. 107 Activity 1", "Student Book p. 107 Activity 2")),
    128: ("CD3-40", (108, 108), ("Student Book p. 108 Activity 1", "Student Book p. 108 Activity 2")),
    136: ("CD3-44", (110, 111), ("Student Book pp. 110–111 Activity 1", "Workbook p. 110 Activity 1")),
    137: ("CD3-46", (111, 111), ("Student Book p. 111 Activity 4", "Workbook p. 111 Activity 2")),
    138: ("CD3-48", (112, 112), ("Student Book p. 112 Activity 2", "Workbook p. 112 Activity 1")),
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


def _book_selection(runtime, year, lesson, *, year2_rows=None, paired_reference=False):
    if year == 1:
        from web.english_y1_kssr_rph import PLANS

        plan = PLANS.get(lesson)
        return ({"year": "Tahun 1"}, [plan.page]) if plan else None
    if year == 5:
        from resources.english.y5.verified_extras_20261117 import STUDENT_BOOK_PAGES

        pages = STUDENT_BOOK_PAGES.get(lesson)
        return ({"year": "Tahun 5"}, list(pages)) if pages else None
    if year == 6:
        pages = year6_sow_book_pages().get(lesson)
        path = _year6_book_path() if pages else None
        return ({"year": "Tahun 6", "book_path": path}, pages) if path else None
    row = _source_row(runtime, year, lesson, year2_rows=year2_rows)
    if row is None:
        return None
    state = _lesson_state(row, year, lesson)
    if year == 4 and paired_reference:
        verified_pages = YEAR4_SB_PAIRED_PAGES.get(lesson)
        return (state, list(verified_pages)) if verified_pages else None
    if year == 3 and paired_reference and lesson in YEAR3_SB_PAIRED_PAGES:
        source = runtime._en_book_source_v25232(state, "textbook")
        if source and source[0] == YEAR3_SB_DRIVE_FILE_ID:
            return state, list(YEAR3_SB_PAIRED_PAGES[lesson])
        return None
    if year == 2:
        state["textbook_page_start"] = row.get("textbook_page_start")
        state["textbook_page_end"] = row.get("textbook_page_end")
        pages = runtime._en_book_pages_v25232(state, "textbook")
        # Primary Year 2 SK SOW p. 51 and Super Minds 1 pp. 62–63, Activity 1.
        if lesson == 12 and pages == [62]:
            pages = [62, 63]
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


@lru_cache(maxsize=1)
def _verified_year5_book(download):
    """Retain one exact verified source per worker without keeping a PDF in RAM."""
    path = Path(download(YEAR5_BOOK_ID))
    try:
        if path.stat().st_size != YEAR5_BOOK_SIZE:
            raise ValueError("Unexpected Year 5 Student Book size")
        with path.open("rb") as source:
            if file_digest(source, "sha256").hexdigest() != YEAR5_BOOK_SHA:
                raise ValueError("Unexpected Year 5 Student Book revision")
        cache = TemporaryDirectory(prefix="cikgulaju-english-y5-")
        path.replace(Path(cache.name) / "student_book.pdf")
        return cache
    finally:
        path.unlink(missing_ok=True)


@lru_cache(maxsize=1)
def _year6_book_matches(path, file_revision):
    """Recheck the exact file when its filesystem identity changes."""
    with path.open("rb") as source:
        return file_digest(source, "sha256").hexdigest() == YEAR6_BOOK_SHA


def _year6_book_path():
    location = os.environ.get("CIKGULAJU_Y6_PUPIL_BOOK_PATH")
    if not location:
        return None
    path = Path(location)
    try:
        if path.is_file() and not path.is_symlink():
            with _year6_book_lock:
                stat = path.stat()
                revision = (stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_ctime_ns)
                if stat.st_size == YEAR6_BOOK_SIZE and _year6_book_matches(path, revision):
                    return path
    except OSError:
        pass
    return None


def _pdf(runtime, state, pages, *, root=ROOT):
    from pypdf import PdfReader, PdfWriter
    if state["year"] == "Tahun 6":
        with state["book_path"].open("rb") as source:
            reader = PdfReader(source, strict=True)
            if reader.is_encrypted or len(reader.pages) != YEAR6_BOOK_PDF_PAGES:
                raise ValueError("Unexpected Year 6 Pupil's Book")
            writer = PdfWriter()
            for printed in pages:
                writer.add_page(reader.pages[printed - 1])
            return _pdf_bytes(writer, limit=YEAR6_EXCERPT_LIMIT)
    if state["year"] == "Tahun 5":
        with _year5_book_lock:
            cache = _verified_year5_book(runtime._drive_pdf_v25232)
        with (Path(cache.name) / "student_book.pdf").open("rb") as source:
            reader = PdfReader(source, strict=True)
            if reader.is_encrypted or len(reader.pages) != YEAR5_BOOK_PDF_PAGES:
                raise ValueError("Unexpected Year 5 Student Book")
            writer = PdfWriter()
            for printed in pages:
                # The English Plus 1 scan places printed page N on PDF page N+1.
                writer.add_page(reader.pages[printed])
            return _pdf_bytes(writer)
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


def _pdf_bytes(writer, *, limit=MAX_PDF):
    output = BytesIO()
    writer.write(output)
    data = output.getvalue()
    if not 400 <= len(data) <= limit or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid selected-page PDF")
    return data


def _audio_rows(runtime, year, lesson, *, year2_rows=None):
    if year == 1:
        return [
            {"title": f"English Tahun 1 • Lesson {lesson:03d} • {reference}",
             "reference": reference, "id": ident, "sha256": digest}
            for reference, ident, digest in YEAR1_AUDIO.get(lesson, ())
        ]
    if year == 5:
        from resources.english.y5.verified_extras_20261117 import AUDIO, LESSON_AUDIO

        return [
            {"title": f"English Tahun 5 • Lesson {lesson:03d} • {reference}",
             "reference": reference, "id": AUDIO[reference][0], "sha256": AUDIO[reference][1]}
            for reference in LESSON_AUDIO.get(lesson, ())
        ]
    if year == 6:
        return _year6_publisher_audio().get(lesson, [])
    row = _source_row(runtime, year, lesson, year2_rows=year2_rows)
    if row is None:
        return []
    if year == 2:
        approved = YEAR2_AUDIO.get(lesson)
        if not approved or row.get("audio_status") != "VERIFIED_AUDIO":
            return []
        pages, tracks = approved
        refs = [ref.strip() for ref in str(row.get("audio_reference") or "").split(";")]
        if (row.get("textbook_page_start"), row.get("textbook_page_end")) != pages:
            return []
        evidence = YEAR2_AUDIO_BOOK_EVIDENCE.get(lesson)
        labels = ("",) * len(tracks)
        if evidence:
            legacy_ref, workbook_pages, labels = evidence
            if ("; ".join(refs) != legacy_ref or row.get("workbook_status") != "LINKED_VERIFIED"
                    or (row.get("workbook_page_start"), row.get("workbook_page_end")) != workbook_pages):
                return []
        elif refs != list(tracks):
            return []
        entries = []
        for (ref, file_id), label in zip(tracks.items(), labels, strict=True):
            disc, number = ref.split("-")
            reference = f"{disc} Track {int(number)}"
            title = f"English Tahun 2 • Lesson {lesson:03d} • {reference}"
            if label:
                title += f" • {label}"
            entries.append({"title": title, "reference": reference, "id": file_id})
        return entries
    state = _lesson_state(row, year, lesson)
    if year == 4:
        if (lesson == 30
                or not getattr(runtime, "CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE", False)
                or not getattr(runtime, "CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE", False)):
            return []
        if lesson in YEAR4_VERIFIED_LESSONS:
            return [
                {"title": f"English Tahun 4 • Lesson {lesson:03d} • {reference}",
                 "reference": reference, "id": YEAR4_RECORDINGS[reference][0],
                 "sha256": YEAR4_RECORDINGS[reference][1]}
                for reference in YEAR4_VERIFIED_LESSONS[lesson]
            ]
        if lesson in HOLD_LESSONS:
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


@lru_cache(maxsize=1)
def _year6_publisher_audio():
    manifest = json.loads((ROOT / "audits/english_y6_itbm_publisher_audio_20261117.json")
                          .read_text(encoding="utf-8"))
    tracks = {row["track"]: row for row in manifest["tracks"]}
    lessons = {}
    for match in manifest["lesson_reference_checks"]:
        lesson, reference = match["lesson"], match["track"]
        recording = tracks[reference]
        disc, track = reference.split(".")
        label = f"CD{disc} Track {track}"
        lessons.setdefault(lesson, []).append({
            "title": f"English Tahun 6 • Lesson {lesson:03d} • {label}",
            "reference": label,
            "publisher_url": recording["url"],
            "size_bytes": recording["size_bytes"],
            "sha256": recording["sha256"],
        })
    return lessons


def _original_audio(id_, *, wma=False):
    import requests
    response = requests.get(
        "https://drive.usercontent.google.com/download",
        params={"id": id_, "export": "download", "confirm": "t"},
        timeout=(10, 50), stream=True, allow_redirects=True,
    )
    return _read_audio(response, wma=wma)


def _read_audio(response, *, wma=False):
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


def _verified_audio(row, *, wma=False):
    if "publisher_url" in row:
        import requests

        url = row["publisher_url"]
        if not url.startswith("https://itbm.com.my/AcademyStarsYear6/audio/"):
            raise ValueError("Unexpected Year 6 publisher origin")
        response = requests.get(url, timeout=(5, 15), stream=True, allow_redirects=False)
        raw = _read_audio(response)
        if len(raw) != row["size_bytes"]:
            raise ValueError("Year 6 publisher audio differs from the audited size")
    else:
        raw = _original_audio(row["id"], wma=wma)
    if row.get("sha256") and sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError("Original audio differs from the audited recording")
    return raw


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

    def selection(years, with_track=False):
        allowed = {"year", "lesson", "track"} if with_track else {"year", "lesson"}
        if set(request.args) != allowed or any(len(request.args.getlist(k)) != 1 for k in allowed):
            return None
        raw_year = request.args["year"]
        if len(raw_year) != 1 or raw_year not in years or not re.fullmatch(r"[1-9][0-9]{0,2}", request.args["lesson"]):
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
        selected = selection("123456")
        if not selected:
            return jsonify({"available": False}), 404
        picked = _book_selection(runtime, *selected, **source_options(selected[0]))
        if not picked:
            return jsonify({"available": False}), 404
        state, pages = picked
        try:
            # Year 3 is stored on Drive. Use the verified mapping for listing
            # and open the original PDF only for a requested excerpt.
            if selected[0] not in (3, 5, 6):
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
        selected = selection("123456")
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
        selected = selection("123456")
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
        selected = selection("123456", with_track=True)
        if not selected:
            return jsonify({"error": "Invalid track"}), 404
        year, lesson, index = selected
        expected, mime = ("wma", "audio/x-ms-wma") if year in (1, 2) else ("mp3", "audio/mpeg")
        if extension != expected:
            return jsonify({"error": "Wrong original audio format"}), 404
        rows = _audio_rows(runtime, year, lesson, **source_options(year))
        if not 1 <= index <= len(rows):
            return jsonify({"error": "Unverified track"}), 404
        row = rows[index - 1]
        try:
            raw = _verified_audio(row, wma=year in (1, 2))
        except Exception:
            return jsonify({"error": "Original audio unavailable"}), 503
        name = re.sub(r"[^A-Za-z0-9_-]", "_", row["reference"])
        answer = Response(raw, mimetype=mime)
        answer.headers["Content-Disposition"] = (
            f'attachment; filename="CikguLaju_English_Y{year}_Lesson_{lesson:03d}_{name}.{extension}"')
        return answer

    return bp


def install_telegram_extras(runtime):
    """Use the same audited material in the Telegram picker and Web API."""
    from web.english_y4_standalone_runtime import _selected_y4_lesson
    from web.english_y5_standalone_runtime import _target as year5_lesson
    from web.english_y6_standalone_runtime import _target as year6_lesson

    available_before = runtime._available_materials_v2528
    send_before = runtime._send_reference_material_v2528
    direct_before = getattr(runtime, "_send_reference_material", None)

    def selection(state):
        lesson = _selected_y4_lesson(state)
        if lesson in YEAR4_VERIFIED_LESSONS:
            return 4, lesson
        lesson = year5_lesson(state)
        if lesson is not None:
            return 5, lesson
        return 6, year6_lesson(state)

    def available(state):
        items = list(available_before(state) or [])
        year, lesson = selection(state)
        if lesson is None:
            return items
        choices = {"media": _audio_rows(runtime, year, lesson)}
        if year != 4:
            choices["textbook"] = (_book_selection(runtime, year, lesson)
                                   or english_book_view_link(year, (lesson,), ()))
        for key, exists in choices.items():
            if exists and key not in items:
                items.append(key)
            elif not exists and key in items:
                items.remove(key)
        return items

    def send(cid, state, key):
        year, lesson = selection(state)
        if lesson is None or (key != "media" and (key != "textbook" or year == 4)):
            return send_before(cid, state, key)
        prefix = f"English_Y{year}_Lesson_{lesson:03d}"
        with TemporaryDirectory(prefix="cikgulaju-english-extras-") as folder:
            if key == "textbook":
                picked = _book_selection(runtime, year, lesson)
                if not picked:
                    book = english_book_view_link(year, (lesson,), ())
                    if not book:
                        return False
                    result = runtime.send(cid, book["title"], [[{"text": book["action"], "url": book["url"]}]])
                    return runtime._telegram_delivery_ok_v25279(result)
                path = Path(folder) / f"{prefix}_Student_Book.pdf"
                path.write_bytes(_pdf(runtime, *picked))
                result = runtime.send_document(cid, str(path), f"📘 English Year {year} • Student’s Book")
                return runtime._telegram_delivery_ok_v25279(result)
            tracks = _audio_rows(runtime, year, lesson)
            delivered = []
            for row in tracks:
                path = Path(folder) / f'{prefix}_{row["reference"].replace(" ", "_")}.mp3'
                path.write_bytes(_verified_audio(row))
                result = runtime.send_document(cid, str(path), row["title"])
                delivered.append(runtime._telegram_delivery_ok_v25279(result))
            return bool(delivered) and all(delivered)

    runtime._available_materials_v2528 = available
    runtime._send_reference_material_v2528 = send
    if callable(direct_before):
        def send_direct(cid, state, key, *args, **kwargs):
            if key == "media" and _selected_y4_lesson(state) in YEAR4_VERIFIED_LESSONS:
                return send(cid, state, key)
            return direct_before(cid, state, key, *args, **kwargs)

        runtime._send_reference_material = send_direct
