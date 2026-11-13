"""Strict Web-to-Telegram reader for optional source-linked teaching materials.

All material selections are resolved on the Telegram source. Redirects,
unknown domains, unknown subject years, mismatched responses and oversized
assets are rejected; public Web does not expose the service bearer token.
"""
import re
import json
from urllib.parse import urlencode
from urllib.request import Request, HTTPSHandler, build_opener
from urllib.error import HTTPError, URLError

from web.native_verified_rpt_rph_client import _backend
from web.native_telegram_rph_client import BlockRedirects, NativeRPHUnavailable

MUSIC_SOURCE = "telegram-provisional-subjects-2027-v1"
WORKBOOK_SOURCE = "telegram-verified-english-workbook-v1"
DRIVE_VIEW = re.compile(r"^https://drive\.google\.com/file/d/[A-Za-z0-9_-]{10,100}/view\?usp=drivesdk$")
MUSIC_UNIT = re.compile(r"^(?:u(?:0[1-9]|[1-9][0-9])|x[a-f0-9]{12})$")
MAX_PDF = 8 * 1024 * 1024


def _get(path, args, *, accept="application/json", limit=130000, opener=None):
    base, token = _backend()
    req = Request(base + path + "?" + urlencode(args), method="GET",
                  headers={"Authorization": "Bearer " + token, "Accept": accept})
    transport = opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req, timeout=20) as response:
            if (response.status != 200 or
                    response.headers.get("Content-Type", "").split(";")[0].strip().lower() != accept):
                raise NativeRPHUnavailable("Invalid Telegram material response")
            value = response.read(limit + 1)
            if len(value) > limit:
                raise NativeRPHUnavailable("Oversized material from Telegram")
        return value
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise NativeRPHUnavailable("Telegram material route unavailable") from None
    except (URLError, OSError, TimeoutError):
        raise NativeRPHUnavailable("Telegram material source unavailable") from None


def _json(path, args, *, opener=None):
    value = _get(path, args, opener=opener)
    if value is None:
        return None
    try:
        data = json.loads(value)
    except (UnicodeError, ValueError):
        raise NativeRPHUnavailable("Invalid Telegram material JSON") from None
    if not isinstance(data, dict):
        raise NativeRPHUnavailable("Invalid Telegram material metadata")
    return data


def english_workbook_metadata(year, lesson, *, opener=None):
    if type(year) is not int or year not in (2, 3, 4) or type(lesson) is not int or not 1 <= lesson <= 160:
        raise ValueError("Unsupported verified Workbook selection")
    data = _json("/internal/rph/v1/english-extras/workbook",
                 {"year": year, "lesson": lesson}, opener=opener)
    if data is None:
        return None
    if (data.get("source") != WORKBOOK_SOURCE or data.get("available") is not True
            or data.get("year") != year or data.get("lesson") != lesson
            or data.get("type") != "workbook" or data.get("format") != "pdf"
            or data.get("status") != "VERIFIED_SOURCE"
            or not isinstance(data.get("title"), str)
            or not 10 <= len(data["title"]) <= 220):
        raise NativeRPHUnavailable("Workbook source identity mismatch")
    return data["title"]


def english_workbook_pdf(year, lesson, *, opener=None):
    # A PDF request is authorized and re-verified independently of metadata.
    if type(year) is not int or year not in (2, 3, 4) or type(lesson) is not int or not 1 <= lesson <= 160:
        raise ValueError("Unsupported verified Workbook selection")
    raw = _get("/internal/rph/v1/english-extras/workbook.pdf",
               {"year": year, "lesson": lesson}, accept="application/pdf",
               limit=MAX_PDF, opener=opener)
    if raw is None or len(raw) < 450 or not raw.startswith(b"%PDF-"):
        raise NativeRPHUnavailable("Verified Workbook PDF unavailable")
    return raw


def music_source_links(year, unit, lesson, *, opener=None):
    if (type(year) is not int or year not in range(2, 7)
            or not isinstance(unit, str) or not MUSIC_UNIT.fullmatch(unit)
            or not isinstance(lesson, str) or not re.fullmatch(r"0(?:0[1-9]|[12][0-9]|3[0-5])", lesson)):
        raise ValueError("Invalid Music PdP selection")
    data = _json("/internal/rph/v1/other-drafts/audio-links",
                 {"year":year, "subject":"MUZIK", "unit":unit, "lesson":lesson}, opener=opener)
    if data is None:
        raise NativeRPHUnavailable("Music source missing")
    if (data.get("source") != MUSIC_SOURCE or data.get("status") != "DRAF"
            or data.get("download_available") is not False
            or type(data.get("available")) is not bool
            or not isinstance(data.get("links"), list)
            or len(data["links"]) > 21):
        raise NativeRPHUnavailable("Untrusted Music source links")
    links = data["links"]
    if bool(links) != data["available"]:
        raise NativeRPHUnavailable("Music link availability mismatch")
    out, seen = [], set()
    for item in links:
        if (not isinstance(item, dict) or set(item) != {"title","url","track"}
                or type(item["track"]) is not int or not 1 <= item["track"] <= 300
                or not isinstance(item["title"], str) or not 1 <= len(item["title"]) <= 255
                or not isinstance(item["url"], str) or not DRIVE_VIEW.fullmatch(item["url"])
                or item["url"] in seen):
            raise NativeRPHUnavailable("Music source link unsafe or ambiguous")
        seen.add(item["url"])
        out.append({"type":"audio", "title":"Audio "+str(item["track"])+" — "+item["title"],
                    "url":item["url"], "action":"Buka Audio Sumber",
                    "source_only":True})
    return out


ENGLISH_ASSET_SOURCE = "telegram-english-lesson-locked-assets-v1"
MAX_AUDIO = 12 * 1024 * 1024


def _english_asset_selection(year, lesson):
    if type(year) is not int or year not in (3, 4) or type(lesson) is not int or not 1 <= lesson <= 160:
        raise ValueError("Unsupported English material selection")


def english_student_book_metadata(year, lesson, *, opener=None):
    _english_asset_selection(year, lesson)
    data = _json("/internal/rph/v1/english-extras/student-book",
                 {"year": year, "lesson": lesson}, opener=opener)
    if data is None:
        return None
    pages = data.get("pages")
    if (data.get("source") != ENGLISH_ASSET_SOURCE or data.get("available") is not True
            or data.get("year") != year or data.get("lesson") != lesson
            or data.get("type") != "textbook" or data.get("format") != "pdf"
            or data.get("status") != "VERIFIED_SOURCE"
            or not isinstance(pages, list) or not 1 <= len(pages) <= 4
            or not all(type(p) is int and 1 <= p <= (135 if year == 3 else 177) for p in pages)
            or pages != list(range(pages[0], pages[-1] + 1))
            or not isinstance(data.get("title"), str)
            or not 10 <= len(data["title"]) <= 220):
        raise NativeRPHUnavailable("Student Book source mismatch")
    return data["title"]


def english_student_book_pdf(year, lesson, *, opener=None):
    _english_asset_selection(year, lesson)
    raw = _get("/internal/rph/v1/english-extras/student-book.pdf",
               {"year": year, "lesson": lesson}, accept="application/pdf",
               limit=MAX_PDF, opener=opener)
    if raw is None or len(raw) < 450 or not raw.startswith(b"%PDF-"):
        raise NativeRPHUnavailable("Student Book pages unavailable")
    return raw


def english_audio_tracks(year, lesson, *, opener=None):
    _english_asset_selection(year, lesson)
    data = _json("/internal/rph/v1/english-extras/audio",
                 {"year": year, "lesson": lesson}, opener=opener)
    if data is None:
        return []
    tracks = data.get("tracks")
    if (data.get("source") != ENGLISH_ASSET_SOURCE or data.get("available") is not True
            or data.get("status") != "VERIFIED_SOURCE"
            or data.get("year") != year or data.get("lesson") != lesson
            or not isinstance(tracks, list) or not 1 <= len(tracks) <= 4):
        raise NativeRPHUnavailable("Original audio identity mismatch")
    result = []
    for i, track in enumerate(tracks, 1):
        if (not isinstance(track, dict) or set(track) != {"index", "title", "reference"}
                or track["index"] != i or type(track["index"]) is not int
                or not isinstance(track["title"], str)
                or not 10 <= len(track["title"]) <= 200
                or not isinstance(track["reference"], str)
                or not re.fullmatch(r"CD[1-9][0-9]? Track [1-9][0-9]{0,2}", track["reference"])):
            raise NativeRPHUnavailable("Unverified audio track")
        result.append({"index": i, "title": track["title"],
                       "reference": track["reference"]})
    return result


def english_audio_mp3(year, lesson, index, *, opener=None):
    _english_asset_selection(year, lesson)
    if type(index) is not int or not 1 <= index <= 4:
        raise ValueError("Invalid verified track")
    raw = _get("/internal/rph/v1/english-extras/audio.mp3",
               {"year": year, "lesson": lesson, "track": index},
               accept="audio/mpeg", limit=MAX_AUDIO, opener=opener)
    if raw is None or len(raw) < 1000 or not (
            raw.startswith(b"ID3") or (raw[0] == 0xff and (raw[1] & 0xe0) == 0xe0)):
        raise NativeRPHUnavailable("Original MP3 unavailable")
    return raw
