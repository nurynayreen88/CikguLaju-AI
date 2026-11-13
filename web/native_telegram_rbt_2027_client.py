"""Authenticated Web client for RBT 2027 from running Telegram, with zero
local curriculum copies, no browser-side source selection and no redirects.

Uses the Web's existing authenticated account and after-success trial charge
in unified_rph_web. Rejects missing private source rather than falling back.
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

ROOT="/internal/rph/v1/rbt/"
SOURCE="telegram-rbt-2027-v1"
UNIT=re.compile(r"u0[1-6]")
PDP=re.compile(r"0(?:0[1-9]|[12][0-9]|3[0-2])")


def _validate(year, unit=None, pdp=None):
    if type(year) is not int or year not in (4,5,6):
        raise ValueError("RBT available only Years 4-6")
    if unit is not None and (type(unit) is not str or not UNIT.fullmatch(unit)):
        raise ValueError("Invalid RBT unit")
    if pdp is not None and (type(pdp) is not str or not PDP.fullmatch(pdp)):
        raise ValueError("Invalid RBT PdP")
    return year


def _read(endpoint, query, *, opener=None):
    base, token = _backend()
    req=Request(base+ROOT+endpoint+"?"+urlencode(query),
                headers={"Authorization":"Bearer "+token,
                         "Accept":"application/json"},method="GET")
    transport=opener or build_opener(HTTPSHandler(),BlockRedirects())
    try:
        with transport.open(req,timeout=12) as response:
            if response.status!=200:
                raise NativeRPHUnavailable("Telegram RBT source unavailable")
            raw=response.read(100001)
        if len(raw)>100000:
            raise NativeRPHUnavailable("Oversized RBT response")
        data=json.loads(raw)
        if type(data) is not dict:
            raise ValueError("Invalid source response")
        return data
    except (HTTPError,URLError,OSError,TimeoutError,ValueError) as exc:
        raise NativeRPHUnavailable("Telegram RBT curriculum source unavailable") from None


def list_rbt_units(year, *, opener=None):
    _validate(year)
    data=_read("units",{"year":year},opener=opener)
    if data.get("source")!=SOURCE or data.get("status")!="DRAF":
        raise NativeRPHUnavailable("RBT source identity mismatch")
    items=data.get("items")
    if (type(items) is not list or not 3<=len(items)<=6 or
        len({x.get("value") for x in items if type(x) is dict})!=len(items) or
        any(type(x) is not dict or not UNIT.fullmatch(str(x.get("value",""))) or
            type(x.get("label")) is not str or not x["label"].startswith("Unit ")
            or len(x["label"])>200 for x in items)):
        raise NativeRPHUnavailable("Invalid RBT Unit catalog")
    return items


def list_rbt_lessons(year, unit, *, opener=None):
    _validate(year,unit)
    data=_read("lessons",{"year":year,"unit":unit},opener=opener)
    if data.get("source")!=SOURCE or data.get("status")!="DRAF":
        raise NativeRPHUnavailable("RBT PdP source mismatch")
    items=data.get("items")
    if (type(items) is not list or not 1<=len(items)<=32 or
        len({x.get("value") for x in items if type(x) is dict})!=len(items) or
        any(type(x) is not dict or not PDP.fullmatch(str(x.get("value",""))) or
            type(x.get("label")) is not str or not x["label"].startswith("PdP ") or
            len(x["label"])>300 or type(x.get("textbook_ref")) is not str or
            len(x["textbook_ref"])>350 or x.get("status")!="DRAF"
            for x in items)):
        raise NativeRPHUnavailable("RBT PdP catalog incomplete")
    return items


def rbt_available(year, unit, pdp, *, opener=None):
    _validate(year,unit,pdp)
    data=_read("availability",
               {"year":year,"unit":unit,"lesson":pdp},opener=opener)
    if (data.get("available") is not True or data.get("status")!="DRAF"
        or data.get("generator")!="telegram-native"):
        raise NativeRPHUnavailable("RBT PdP not available")
    return True


def request_rbt_rph(selection,fmt,*,opener=None):
    if (fmt not in MIMES or type(selection) is not dict or
            selection.get("source")!="telegram-native-rbt-2027"):
        raise ValueError("Invalid RBT RPH source")
    year=selection.get("year"); unit=selection.get("unit")
    lesson=selection.get("lesson")
    _validate(year,unit,lesson)
    teacher=selection.get("teacher")
    if (not valid_teacher_fields(teacher)
        or any(type(v) is not str for v in teacher.values())):
        raise ValueError("Invalid RBT teacher context")
    body=json.dumps({"selection":{"year":year,"unit":unit,"lesson":lesson},
                     "teacher":teacher,"format":fmt},ensure_ascii=False).encode("utf-8")
    if len(body)>7000:
        raise ValueError("Oversized RBT source selection")
    base,token=_backend()
    req=Request(base+ROOT+"render",data=body,method="POST",
                headers={"Authorization":"Bearer "+token,
                         "Content-Type":"application/json","Accept":MIMES[fmt]})
    transport=opener or build_opener(HTTPSHandler(),BlockRedirects())
    try:
        with transport.open(req,timeout=40) as response:
            if (response.status!=200 or
                response.headers.get("Content-Type","").split(";")[0].strip().lower()!=MIMES[fmt]):
                raise NativeRPHUnavailable("Telegram RBT document MIME mismatch")
            data=response.read(MAX_DOCUMENT+1)
    except (HTTPError,URLError,OSError,TimeoutError):
        raise NativeRPHUnavailable("Native Telegram RBT Word/PDF unavailable") from None
    if not 1000<=len(data)<=MAX_DOCUMENT:
        raise NativeRPHUnavailable("Invalid RBT document length")
    if fmt=="pdf":
        if not data.startswith(b"%PDF-"):
            raise NativeRPHUnavailable("Invalid RBT PDF")
    else:
        if not data.startswith(b"PK\x03\x04"):
            raise NativeRPHUnavailable("Invalid RBT Word")
        try:
            with ZipFile(io.BytesIO(data)) as archive:
                if archive.testzip() or "word/document.xml" not in archive.namelist():
                    raise NativeRPHUnavailable("Invalid RBT Word document")
        except (BadZipFile,ValueError,OSError):
            raise NativeRPHUnavailable("Invalid RBT Word package") from None
    return io.BytesIO(data)
