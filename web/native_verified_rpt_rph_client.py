"""Web client for the active Telegram master RPT -> native RPH bridge.

All lesson identity and source content are resolved again by the Telegram
runtime. No Web copy, unverified SK/SP, or client-selected RPH text is used.
"""
import io
import json
import os
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPSHandler
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile
from web.rph_teacher_reflection import valid_teacher_fields

from web.native_telegram_rph_client import (
    NativeRPHUnavailable, BlockRedirects, MIMES, MAX_DOCUMENT
)

SUBJECTS = frozenset(("BM", "PI"))


def _backend():
    base = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    parts = urlsplit(base)
    if (parts.scheme != "https" or not parts.hostname or parts.port is not None
            or parts.username or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment or len(token) < 32):
        raise NativeRPHUnavailable("Authoritative Telegram API unavailable")
    return base.rstrip("/"), token


def _selection(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid selection")
    year, code, unit, token = (
        data.get("year"), data.get("subject"), data.get("unit"),
        data.get("lesson")
    )
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("Invalid year")
    if code not in SUBJECTS:
        raise ValueError("Subject lacks a verified native RPT bridge")
    if not isinstance(unit, str) or not unit.strip() or len(unit) > 300:
        raise ValueError("Invalid unit")
    if type(token) is str:
        if not re.fullmatch(r"[1-9][0-9]{0,9}", token):
            raise ValueError("Invalid RPT row ID")
        token = int(token)
    if type(token) is not int or not 0 < token < 2**31:
        raise ValueError("Invalid RPT row ID")
    return {"year": year, "subject": code, "unit": unit, "lesson": token}


def verified_rpt_available(year, subject, unit, lesson, *, opener=None):
    selection = _selection({
        "year": year, "subject": subject, "unit": unit, "lesson": lesson
    })
    base, token = _backend()
    url = base + "/internal/rph/v1/verified-rpt/availability?" + urlencode(selection)
    req = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
    }, method="GET")
    transport = opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req, timeout=9) as resp:
            if resp.status != 200:
                raise NativeRPHUnavailable("No approved master RPT")
            payload = resp.read(4097)
        if len(payload) > 4096:
            raise NativeRPHUnavailable("Unexpected native RPT response")
        result = json.loads(payload)
        if not isinstance(result, dict) or result.get("available") is not True:
            raise NativeRPHUnavailable("Native RPT RPH unavailable")
        return True
    except (HTTPError, URLError, OSError, TimeoutError, ValueError):
        raise NativeRPHUnavailable("Native RPT RPH unavailable") from None


def request_verified_rpt_rph(data, fmt, *, opener=None):
    if fmt not in MIMES:
        raise ValueError("Invalid format")
    selection = _selection(data)
    if data.get("source") != "telegram-verified-rpt-master":
        raise ValueError("Unsupported native RPH source")
    teacher = data.get("teacher")
    if not valid_teacher_fields(teacher):
        raise ValueError("Invalid teacher metadata")
    base, token = _backend()
    body = json.dumps({
        "selection": selection, "teacher": teacher, "format": fmt
    }, ensure_ascii=False).encode("utf-8")
    if len(body) > 7000:
        raise NativeRPHUnavailable("Invalid native RPH request size")
    req = Request(base + "/internal/rph/v1/verified-rpt/render",
                  data=body, headers={
                      "Authorization": "Bearer " + token,
                      "Content-Type": "application/json",
                      "Accept": MIMES[fmt],
                  }, method="POST")
    transport = opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req, timeout=40) as response:
            if response.status != 200 or response.headers.get(
                    "Content-Type", "").split(";")[0].strip().lower() != MIMES[fmt]:
                raise NativeRPHUnavailable("Telegram source did not return RPH")
            content = response.read(MAX_DOCUMENT+1)
    except (HTTPError, URLError, OSError, TimeoutError):
        raise NativeRPHUnavailable("Native Telegram master RPH unavailable") from None
    if not 1000 <= len(content) <= MAX_DOCUMENT:
        raise NativeRPHUnavailable("Invalid native RPH file size")
    if fmt == "pdf":
        if not content.startswith(b"%PDF-"):
            raise NativeRPHUnavailable("Invalid native PDF file")
    else:
        if not content.startswith(b"PK\x03\x04"):
            raise NativeRPHUnavailable("Invalid native Word signature")
        try:
            with ZipFile(io.BytesIO(content)) as archive:
                if archive.testzip() or "word/document.xml" not in archive.namelist():
                    raise NativeRPHUnavailable("Invalid native Word package")
        except (OSError, ValueError, BadZipFile):
            raise NativeRPHUnavailable("Invalid native Word package") from None
    return io.BytesIO(content)
