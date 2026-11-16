"""Proxy Matematik SJKC Tahun 3 selections to the shared Telegram source."""

from io import BytesIO
import json
import re
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, HTTPSHandler, build_opener

from web.document_integrity import validate_word_document
from web.native_telegram_rph_client import BlockRedirects, MAX_DOCUMENT, MIMES, NativeRPHUnavailable
from web.native_verified_rpt_rph_client import _backend

SUBJECT = "MATH_SJKC"
LABEL = "Matematik SJKC"
YEAR = 3
SOURCE = "telegram-native-math-sjkc"
PREFIX = "/internal/rph/v1/matematik-sjkc/"


def _number(value, limit):
    if not isinstance(value, str) or not re.fullmatch(r"[1-9][0-9]?", value) or int(value) > limit:
        raise ValueError("Invalid Matematik SJKC selection")
    return int(value)


def _selection(year, unit=None, pdp=None):
    if type(year) is not int or year != YEAR:
        raise ValueError("Wrong Matematik SJKC year")
    selection = {"year": year}
    if unit is not None:
        selection["unit"] = _number(unit, 9)
    if pdp is not None:
        selection["pdp"] = _number(pdp, 96)
    return selection


def _request(endpoint, *, params=None, payload=None, mime="application/json", limit=32000, opener=None):
    base, token = _backend()
    url = base + PREFIX + endpoint
    if params is not None:
        url += "?" + urlencode(params)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Authorization": "Bearer " + token, "Accept": mime}
    if body is not None:
        headers["Content-Type"] = "application/json"
    transport = opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(Request(url, data=body, headers=headers), timeout=15) as response:
            if response.status != 200 or response.headers.get_content_type() != mime:
                raise NativeRPHUnavailable("Matematik SJKC response unavailable")
            result = response.read(limit + 1)
    except (URLError, OSError):
        raise NativeRPHUnavailable("Matematik SJKC source unavailable") from None
    if len(result) > limit:
        raise NativeRPHUnavailable("Oversized Matematik SJKC response")
    return result


def _query(selection, *, opener):
    try:
        return json.loads(_request("options", params=selection, opener=opener))
    except (UnicodeError, ValueError):
        raise NativeRPHUnavailable("Invalid Matematik SJKC response") from None


def options(year, unit=None, *, opener=None):
    items = _query(_selection(year, unit), opener=opener)
    limit = 9 if unit is None else 96
    try:
        if not isinstance(items, list) or not 1 <= len(items) <= limit:
            raise ValueError("Invalid options")
        if any(not isinstance(item, dict) for item in items):
            raise ValueError("Invalid options")
        numbers = [_number(item["value"], limit) for item in items]
        if (numbers != sorted(set(numbers))
                or any(not isinstance(item["label"], str) or not 1 <= len(item["label"]) <= 300
                       for item in items)
                or (unit is None and numbers != list(range(1, limit + 1)))
                or (unit is not None and any(item.get("lesson_no") != n for item, n in zip(items, numbers)))):
            raise ValueError("Invalid options")
    except (KeyError, TypeError, ValueError):
        raise NativeRPHUnavailable("Invalid Matematik SJKC options") from None
    return items


def verify(year, unit, pdp, *, opener=None):
    selection = _selection(year, unit, pdp)
    if _query(selection, opener=opener) != {"available": True}:
        raise NativeRPHUnavailable("Matematik SJKC PdP unavailable")
    return selection["pdp"]


def request_document(selected, fmt, *, opener=None):
    if selected.get("source") != SOURCE or fmt not in MIMES:
        raise ValueError("Invalid Matematik SJKC render")
    selection = _selection(selected["year"], selected["unit"], str(selected["lesson"]))
    payload = dict(selection, teacher=selected["teacher"], format=fmt)
    content = _request("render", payload=payload, mime=MIMES[fmt], limit=MAX_DOCUMENT, opener=opener)
    if fmt == "word":
        validate_word_document(content)
    elif len(content) < 1000 or not content.startswith(b"%PDF-") or not content.rstrip().endswith(b"%%EOF"):
        raise NativeRPHUnavailable("Invalid Matematik SJKC PDF")
    return BytesIO(content)
