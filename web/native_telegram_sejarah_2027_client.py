"""Web proxy for Sejarah 2027 source from the *running* Telegram service.

No copied RPH database on Web. Each Unit/PdP and Word/PDF is resolved by
the private Telegram API behind the existing authenticated quota/licence gate.
"""
from __future__ import annotations

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

ROOT = "/internal/rph/v1/sejarah/"
SOURCE = "telegram-sejarah-2027-v1"
UNIT = re.compile(r"u(?:0[1-9]|1[0-2])")
PDP = re.compile(r"0(?:0[1-9]|[12][0-9]|3[0-6])")


def _validate(year, unit=None, pdp=None):
    if type(year) is not int or year not in (4, 5, 6):
        raise ValueError("Sejarah only supports Years 4–6")
    if unit is not None and (not isinstance(unit, str) or not UNIT.fullmatch(unit)):
        raise ValueError("Invalid Telegram unit identity")
    if pdp is not None and (not isinstance(pdp, str) or not PDP.fullmatch(pdp)):
        raise ValueError("Invalid PdP identity")
    return year


def _read(endpoint, query, *, opener=None):
    base, token = _backend()
    req = Request(base + ROOT + endpoint + "?" + urlencode(query),
                  headers={"Authorization": "Bearer " + token,
                           "Accept": "application/json"}, method="GET")
    transport = opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req, timeout=12) as response:
            if response.status != 200:
                raise NativeRPHUnavailable("Unavailable Telegram Sejarah source")
            raw = response.read(100000+1)
        if len(raw) > 100000:
            raise NativeRPHUnavailable("Oversized Telegram response")
        return json.loads(raw)
    except (HTTPError, URLError, OSError, TimeoutError, ValueError):
        raise NativeRPHUnavailable("Telegram Sejarah RPH source unavailable") from None


def list_sejarah_units(year, *, opener=None):
    _validate(year)
    data = _read("units", {"year": year}, opener=opener)
    if (not isinstance(data, dict) or data.get("source") != SOURCE
            or not isinstance(data.get("items"), list)
            or not 1 <= len(data["items"]) <= 12):
        raise NativeRPHUnavailable("Unverified Sejarah unit catalog")
    out = data["items"]
    if (len(set(x.get("value") for x in out if isinstance(x, dict))) != len(out)
            or any(not isinstance(x, dict) or not UNIT.fullmatch(str(x.get("value") or ""))
                   or not isinstance(x.get("label"), str)
                   or not 4 <= len(x["label"]) <= 250 for x in out)):
        raise NativeRPHUnavailable("Invalid Sejarah unit catalog")
    return out


def list_sejarah_lessons(year, unit, *, opener=None):
    _validate(year, unit)
    data = _read("lessons", {"year": year, "unit": unit}, opener=opener)
    if (not isinstance(data, dict) or data.get("source") != SOURCE
            or not isinstance(data.get("items"), list) or not data["items"]
            or len(data["items"]) > 36):
        raise NativeRPHUnavailable("Unverified Sejarah PdP catalog")
    out = data["items"]
    if (len(set(x.get("value") for x in out if isinstance(x, dict))) != len(out)
            or any(not isinstance(x, dict) or not PDP.fullmatch(str(x.get("value") or ""))
                   or not isinstance(x.get("label"), str)
                   or not x["label"].strip() or len(x["label"]) > 300
                   or not isinstance(x.get("textbook_ref"), str)
                   or not x["textbook_ref"].startswith("Buku Teks m/s ")
                   or len(x["textbook_ref"]) > 100 for x in out)):
        raise NativeRPHUnavailable("Invalid Sejarah lesson data")
    return out


def sejarah_available(year, unit, pdp, *, opener=None):
    _validate(year, unit, pdp)
    data = _read("availability", {"year":year,"unit":unit,"lesson":pdp}, opener=opener)
    if not isinstance(data, dict) or data.get("available") is not True:
        raise NativeRPHUnavailable("Sejarah PdP not available")
    return True


def request_sejarah_rph(selection, fmt, *, opener=None):
    if fmt not in MIMES or not isinstance(selection, dict) or selection.get("source") != "telegram-native-sejarah-2027":
        raise ValueError("Invalid Sejarah RPH source")
    year = selection.get("year")
    unit = selection.get("unit")
    lesson = selection.get("lesson")
    _validate(year, unit, lesson)
    teacher = selection.get("teacher")
    if not valid_teacher_fields(teacher):
        raise ValueError("Missing verified teacher context")
    body = json.dumps({"selection":{"year":year,"unit":unit,"lesson":lesson},
                       "teacher":teacher,"format":fmt},ensure_ascii=False).encode("utf-8")
    if len(body) > 7000:
        raise ValueError("Oversized Sejarah RPH selection")
    base, token = _backend()
    req = Request(base + ROOT + "render", data=body,
                  headers={"Authorization":"Bearer " + token,
                           "Content-Type":"application/json","Accept":MIMES[fmt]},
                  method="POST")
    transport = opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req, timeout=40) as response:
            if (response.status != 200 or response.headers.get(
                    "Content-Type","").split(";")[0].strip().lower() != MIMES[fmt]):
                raise NativeRPHUnavailable("Unexpected Telegram Sejarah MIME")
            data = response.read(MAX_DOCUMENT+1)
    except (HTTPError, URLError, OSError, TimeoutError):
        raise NativeRPHUnavailable("Telegram Sejarah Word/PDF not available") from None
    if not 1000 <= len(data) <= MAX_DOCUMENT:
        raise NativeRPHUnavailable("Invalid Sejarah document size")
    if fmt == "pdf":
        if not data.startswith(b"%PDF-"):
            raise NativeRPHUnavailable("Invalid PDF")
    else:
        if not data.startswith(b"PK\x03\x04"):
            raise NativeRPHUnavailable("Invalid Word")
        try:
            with ZipFile(io.BytesIO(data)) as archive:
                if archive.testzip() or "word/document.xml" not in archive.namelist():
                    raise NativeRPHUnavailable("Damaged Word")
        except (OSError, ValueError, BadZipFile):
            raise NativeRPHUnavailable("Damaged Word") from None
    return io.BytesIO(data)
