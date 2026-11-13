"""Signed Web client for the actual Telegram BM verified_pdp_sequence.

The browser never chooses source rows, standards or RPH text. Telegram
resolves the exact opaque BM PdP key, then returns genuine native DOCX/PDF.
"""
import io
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPSHandler
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile
from web.rph_teacher_reflection import valid_teacher_fields

from web.native_telegram_rph_client import (
    NativeRPHUnavailable, BlockRedirects, MIMES, MAX_DOCUMENT,
)
from web.native_verified_rpt_rph_client import _backend

TOKEN = re.compile(r"b[a-f0-9]{24}")


def _selection(year, unit, lesson):
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("Invalid BM year")
    if (not isinstance(unit, str) or not 0 < len(unit.strip()) <= 300
            or any(ord(c) < 32 for c in unit)):
        raise ValueError("Invalid BM unit")
    if not isinstance(lesson, str) or not TOKEN.fullmatch(lesson):
        raise ValueError("Unverified BM PdP token")
    return {"year": year, "subject": "BM", "unit": unit, "lesson": lesson}


def _client():
    return build_opener(HTTPSHandler(), BlockRedirects())


def verified_native_bm_available(year, unit, lesson, *, opener=None):
    args = _selection(year, unit, lesson)
    base, secret = _backend()
    req = Request(base + "/internal/rph/v1/bm-sequence/availability?" +
                  urlencode(args), method="GET", headers={
                      "Authorization": "Bearer " + secret,
                      "Accept": "application/json",
                  })
    try:
        with (opener or _client()).open(req, timeout=12) as response:
            if response.status != 200:
                raise NativeRPHUnavailable("Telegram BM source not ready")
            data = response.read(4097)
        if len(data) > 4096:
            raise NativeRPHUnavailable("BM response exceeds limit")
        result = json.loads(data)
        if not isinstance(result, dict) or result.get("available") is not True:
            raise NativeRPHUnavailable("Telegram BM RPH not verified")
    except (HTTPError, URLError, OSError, TimeoutError, ValueError):
        raise NativeRPHUnavailable("Telegram BM native RPH unavailable") from None
    return True


def request_native_bm_rph(selected, fmt, *, opener=None):
    if fmt not in MIMES or not isinstance(selected, dict):
        raise ValueError("Invalid RPH request")
    if selected.get("source") != "telegram-native-bm-pdp":
        raise ValueError("Wrong RPH source")
    args = _selection(selected.get("year"), selected.get("unit"),
                      selected.get("lesson"))
    teacher = selected.get("teacher")
    if not valid_teacher_fields(teacher):
        raise ValueError("Invalid BM teacher metadata")
    payload = json.dumps({
        "selection": args, "teacher": teacher, "format": fmt,
    }, ensure_ascii=False).encode("utf-8")
    if len(payload) > 7000:
        raise NativeRPHUnavailable("BM request oversized")
    base, secret = _backend()
    req = Request(base + "/internal/rph/v1/bm-sequence/render",
                  data=payload, method="POST", headers={
                      "Authorization": "Bearer " + secret,
                      "Content-Type": "application/json",
                      "Accept": MIMES[fmt],
                  })
    try:
        with (opener or _client()).open(req, timeout=40) as response:
            if (response.status != 200 or response.headers.get(
                    "Content-Type", "").split(";")[0].strip().lower() != MIMES[fmt]):
                raise NativeRPHUnavailable("Unexpected native BM file")
            content = response.read(MAX_DOCUMENT + 1)
    except (HTTPError, URLError, OSError, TimeoutError):
        raise NativeRPHUnavailable("Native Telegram BM document unavailable") from None
    if not 1000 <= len(content) <= MAX_DOCUMENT:
        raise NativeRPHUnavailable("Invalid native BM document length")
    if fmt == "pdf":
        if not content.startswith(b"%PDF-"):
            raise NativeRPHUnavailable("Invalid BM PDF signature")
    else:
        if not content.startswith(b"PK\x03\x04"):
            raise NativeRPHUnavailable("Invalid BM Word signature")
        try:
            with ZipFile(io.BytesIO(content)) as archive:
                if archive.testzip() or "word/document.xml" not in archive.namelist():
                    raise NativeRPHUnavailable("Invalid BM Word package")
        except (BadZipFile, ValueError, OSError):
            raise NativeRPHUnavailable("Invalid BM Word package") from None
    return io.BytesIO(content)
