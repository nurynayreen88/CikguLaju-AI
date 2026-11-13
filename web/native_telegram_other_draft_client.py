"""Signed source-only proxy for Arabic and Music draft RPH in Telegram runtime.

The Web does not copy/deserialize author-authored lesson content or invent
lessons. It checks every item against source-specific unit, year and PdP
identity before asking Telegram to render files.
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

PREFIX = "/internal/rph/v1/other-drafts/"
SOURCE = "telegram-provisional-subjects-2027-v1"
SUBJECTS = ("ARAB", "MUZIK")
UNIT = re.compile(r"u(?:0[1-9]|[1-9][0-9])|x[a-f0-9]{12}")
PDP = re.compile(r"0[0-9][0-9]")


def _check(year, subject, unit=None, lesson=None):
    if type(year) is not int or year not in range(2, 7) or subject not in SUBJECTS:
        raise ValueError("Unsupported draft subject")
    if unit is not None and (not isinstance(unit, str) or not UNIT.fullmatch(unit)):
        raise ValueError("Invalid draft unit")
    if lesson is not None and (not isinstance(lesson, str) or not PDP.fullmatch(lesson)
                               or int(lesson) == 0 or int(lesson) > (35 if subject=="MUZIK" else 60)):
        raise ValueError("Invalid draft PdP")
    return True


def _read(endpoint, args, *, opener=None):
    base, token = _backend()
    req = Request(base + PREFIX + endpoint + "?" + urlencode(args),
                  headers={"Authorization": "Bearer " + token,
                           "Accept": "application/json"}, method="GET")
    transport = opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req, timeout=12) as response:
            if response.status != 200:
                raise NativeRPHUnavailable("Telegram draft source unavailable")
            raw=response.read(110000)
        if len(raw) >= 110000:
            raise NativeRPHUnavailable("Oversized draft response")
        data=json.loads(raw)
        if not isinstance(data,dict):
            raise NativeRPHUnavailable("Invalid draft response")
        return data
    except (HTTPError, URLError, OSError, TimeoutError, ValueError):
        raise NativeRPHUnavailable("Telegram draft source unavailable") from None


def _options(endpoint,args,*,opener=None):
    out=_read(endpoint,args,opener=opener)
    if out.get("source")!=SOURCE or out.get("status")!="DRAF":
        raise NativeRPHUnavailable("Draft source signature unavailable")
    items=out.get("items")
    if (not isinstance(items,list) or not 1<=len(items)<=100
            or any(not isinstance(x,dict) or x.get("status")!="DRAF"
                   or not isinstance(x.get("value"),str) or not isinstance(x.get("label"),str)
                   or not 4<=len(x["label"])<=360 for x in items)
            or len({x["value"] for x in items})!=len(items)):
        raise NativeRPHUnavailable("Untrusted draft choices")
    return items


def list_draft_units(year,subject,*,opener=None):
    _check(year,subject)
    out=_options("units",{"year":year,"subject":subject},opener=opener)
    if any(not UNIT.fullmatch(x["value"]) for x in out):
        raise NativeRPHUnavailable("Unverified draft unit token")
    return out


def list_draft_lessons(year,subject,unit,*,opener=None):
    _check(year,subject,unit)
    out=_options("lessons",{"year":year,"subject":subject,"unit":unit},opener=opener)
    for item in out:
        try:
            _check(year,subject,unit,item["value"])
        except ValueError:
            raise NativeRPHUnavailable("Unverified draft PdP token") from None
        if not item["label"].startswith("PdP ") or "(DRAF)" not in item["label"]:
            raise NativeRPHUnavailable("Draft PdP label required")
        fmts=item.get("formats")
        if not isinstance(fmts,list) or not fmts or not set(fmts).issubset(MIMES):
            raise NativeRPHUnavailable("Invalid draft RPH formats")
        if subject=="ARAB" and fmts!=["word"]:
            raise NativeRPHUnavailable("Unverified Arabic PDF")
    return out


def draft_available(year,subject,unit,lesson,*,opener=None):
    _check(year,subject,unit,lesson)
    data=_read("availability",{"year":year,"subject":subject,
                               "unit":unit,"lesson":lesson},opener=opener)
    if (data.get("available") is not True or data.get("status")!="DRAF"
            or data.get("generator")!="telegram-native"):
        raise NativeRPHUnavailable("Draft RPH source not available")
    fmts=data.get("formats")
    if not isinstance(fmts,list) or not fmts or not set(fmts).issubset(MIMES):
        raise NativeRPHUnavailable("No validated formats")
    if subject=="ARAB" and fmts!=["word"]:
        raise NativeRPHUnavailable("Arabic PDF not certified")
    return tuple(fmts)


def request_draft_rph(selection, fmt, *, opener=None):
    if (not isinstance(selection,dict)
            or selection.get("source")!="telegram-provisional-subjects-2027"
            or fmt not in MIMES):
        raise ValueError("Wrong draft source")
    year,subject,unit,lesson=(selection.get(key)
                             for key in ("year","subject","unit","lesson"))
    _check(year,subject,unit,lesson)
    if subject=="ARAB" and fmt=="pdf":
        raise NativeRPHUnavailable("Arabic PDF Arabic shaping not certified")
    teacher=selection.get("teacher")
    if not valid_teacher_fields(teacher):
        raise ValueError("Invalid teacher metadata")
    payload=json.dumps({"selection":{"year":year,"subject":subject,
                                     "unit":unit,"lesson":lesson},
                        "teacher":teacher,"format":fmt},
                       ensure_ascii=False).encode("utf8")
    if len(payload)>7000:
        raise ValueError("Oversized draft selection")
    base,token=_backend()
    req=Request(base+PREFIX+"render",data=payload,method="POST",
                headers={"Authorization":"Bearer "+token,
                         "Content-Type":"application/json","Accept":MIMES[fmt]})
    transport=opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req,timeout=45) as response:
            if response.status!=200 or response.headers.get("Content-Type","").split(";")[0].strip().lower()!=MIMES[fmt]:
                raise NativeRPHUnavailable("Wrong Telegram draft file")
            data=response.read(MAX_DOCUMENT+1)
    except (HTTPError,URLError,OSError,TimeoutError):
        raise NativeRPHUnavailable("Telegram draft RPH unavailable") from None
    if not 1000<=len(data)<=MAX_DOCUMENT:
        raise NativeRPHUnavailable("Invalid draft document size")
    if fmt=="word":
        if not data.startswith(b"PK\x03\x04"):
            raise NativeRPHUnavailable("Corrupt draft Word")
        try:
            with ZipFile(io.BytesIO(data)) as z:
                if z.testzip() or "word/document.xml" not in z.namelist():
                    raise NativeRPHUnavailable("Corrupt draft Word")
        except (OSError,ValueError,BadZipFile):
            raise NativeRPHUnavailable("Corrupt draft Word") from None
    elif not data.startswith(b"%PDF-"):
        raise NativeRPHUnavailable("Corrupt draft PDF")
    return io.BytesIO(data)
