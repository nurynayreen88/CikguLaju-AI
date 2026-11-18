"""Web client for the Telegram-native Mathematics and Science PdP sequence.

No RPT-week matching or Web-side lesson generation. Unit/PdP options,
readiness checks and Word/PDF bytes all come from the running Telegram bot.
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

SUBJECTS = frozenset(("MATH", "SCIENCE", "MATH_DLP", "SCIENCE_DLP"))
UNITS = re.compile(r"u[a-f0-9]{24}")
SCIENCE_2027_ROUTE = "/internal/rph/v1/sains-sk-y5-2027"
SCIENCE_2027_ROUTES = {
    5: ("v", SCIENCE_2027_ROUTE),
    6: ("w", "/internal/rph/v1/sains-sk-y6-2027"),
}
SEQUENCE_ROUTE = "/internal/rph/v1/sequence"
DLP_ROUTE = "/internal/rph/v1/dlp"
DLP_UNIT = re.compile(r"0[1-8]")
DLP_LESSON = re.compile(r"DLP-MATH-Y6-(?:L(?:0[1-9]|[1-3][0-9]|4[0-6])|R0[1-8])")
DLP_SCIENCE_UNIT = re.compile(r"(?:0[1-9]|1[0-3])")
DLP_SCIENCE_LESSON = re.compile(r"DLP-SCI-Y6-(?:L(?:0[1-9]|[1-4][0-9]|5[0-2])|R0[1-9])")
DLP_CATALOGUES = {
    (4, "SCIENCE_DLP"): ("year4-science/catalogue", re.compile(r"(?:0[1-9]|10)"),
                         re.compile(r"DLP-SCI-Y4-(?:L(?:0[1-9]|[1-5][0-9])|R(?:0[1-9]|10))"), 10, 69),
    (5, "MATH_DLP"): ("year5-mathematics/catalogue", DLP_UNIT,
                      re.compile(r"DLP-MATH-Y5-(?:L(?:0[1-9]|[1-5][0-9]|6[01])|R0[1-8])"), 8, 69),
    (5, "SCIENCE_DLP"): ("year5-science/catalogue", re.compile(r"(?:0[1-9]|10)"),
                         re.compile(r"DLP-SCI-Y5-(?:L(?:0[1-9]|[1-5][0-9]|60)|R(?:0[1-9]|10))"), 10, 70),
    (6, "MATH_DLP"): ("year6-mathematics/catalogue", DLP_UNIT, DLP_LESSON, 8, 54),
    (6, "SCIENCE_DLP"): ("year6-science/catalogue", DLP_SCIENCE_UNIT, DLP_SCIENCE_LESSON, 13, 61),
}
DLP_SUBJECTS = {subject for _, subject in DLP_CATALOGUES}


def _year_subject(year, subject):
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("Invalid school year")
    if subject not in SUBJECTS or (subject in DLP_SUBJECTS and (year, subject) not in DLP_CATALOGUES):
        raise ValueError("No Telegram native PdP sequence for subject")
    return year, subject


def _selection(year, subject, unit, lesson=None):
    _year_subject(year, subject)
    if not isinstance(unit, str):
        raise ValueError("Unverified native unit token")
    science = SCIENCE_2027_ROUTES.get(year) if subject == "SCIENCE" else None
    route = SEQUENCE_ROUTE
    if subject in DLP_SUBJECTS and DLP_CATALOGUES[year, subject][1].fullmatch(unit):
        route = DLP_ROUTE
    elif science and re.fullmatch(science[0] + r"[a-f0-9]{24}", unit):
        route = science[1]
        unit = "u" + unit[1:]
    elif subject in DLP_SUBJECTS or not UNITS.fullmatch(unit):
        raise ValueError("Unverified native unit token")
    result = {"year":year, "subject":subject, "unit":unit}
    if lesson is not None:
        if (not isinstance(lesson, str) or not 0 < len(lesson) <= 100
                or any(ord(c) < 32 for c in lesson)):
            raise ValueError("Invalid native PdP code")
        if route == DLP_ROUTE and not DLP_CATALOGUES[year, subject][2].fullmatch(lesson):
            raise ValueError("Invalid DLP lesson code")
        result["lesson"] = lesson
    return route, result


def _read(endpoint, params, *, route=SEQUENCE_ROUTE, opener=None):
    base, token = _backend()
    req = Request(base + route + "/" + endpoint + ("?" + urlencode(params) if params else ""), headers={
                      "Authorization":"Bearer " + token,
                      "Accept":"application/json",
                  }, method="GET")
    transport = opener or build_opener(HTTPSHandler(),BlockRedirects())
    try:
        with transport.open(req,timeout=12) as response:
            if response.status != 200:
                raise NativeRPHUnavailable("Telegram sequence unavailable")
            body = response.read(100000+1)
        if len(body) > 100000:
            raise NativeRPHUnavailable("Oversized Telegram response")
        return json.loads(body)
    except (HTTPError, URLError, OSError, TimeoutError, ValueError):
        raise NativeRPHUnavailable("Telegram PdP sequence unavailable") from None


def _units(data):
    if (not isinstance(data,dict)
            or data.get("source")!="telegram-runtime-v1"
            or not isinstance(data.get("items"),list)
            or len(data["items"]) > 500):
        raise NativeRPHUnavailable("Invalid Telegram native unit choices")
    result = data["items"]
    if any(not isinstance(x,dict) or not isinstance(x.get("value"),str)
           or not UNITS.fullmatch(x["value"])
           or not isinstance(x.get("label"),str) or not x["label"].strip()
           for x in result):
        raise NativeRPHUnavailable("Unverified Telegram unit data")
    return result


def _dlp_catalogue(year, subject):
    endpoint, unit_pattern, lesson_pattern, unit_count, lesson_count = DLP_CATALOGUES[year, subject]
    data = _read(endpoint, {}, route=DLP_ROUTE)
    if not isinstance(data, dict) or (data.get("year"), data.get("subject")) != (year, subject):
        raise NativeRPHUnavailable("Invalid DLP catalogue")
    units = data.get("units")
    if not isinstance(units, list) or len(units) != unit_count:
        raise NativeRPHUnavailable("Incomplete DLP catalogue")
    found = {}
    lesson_ids = set()
    for unit in units:
        if (not isinstance(unit, dict) or not unit_pattern.fullmatch(str(unit.get("id", "")))
                or unit["id"] in found or not isinstance(unit.get("title"), str)
                or not unit["title"].strip() or not isinstance(unit.get("lessons"), list)):
            raise NativeRPHUnavailable("Invalid DLP unit")
        found[unit["id"]] = unit
        for lesson in unit["lessons"]:
            if (not isinstance(lesson, dict) or not lesson_pattern.fullmatch(str(lesson.get("id", "")))
                    or lesson["id"] in lesson_ids or not isinstance(lesson.get("title"), str)
                    or not isinstance(lesson.get("label"), str)
                    or not isinstance(lesson.get("book_reference"), str)):
                raise NativeRPHUnavailable("Invalid DLP lesson")
            lesson_ids.add(lesson["id"])
    if len(lesson_ids) != lesson_count:
        raise NativeRPHUnavailable("Incomplete DLP lessons")
    return found


def list_native_units(year, subject, *, current_unit=""):
    _year_subject(year, subject)
    if subject in DLP_SUBJECTS:
        return [{"value": key, "label": unit["title"]} for key, unit in _dlp_catalogue(year, subject).items()]
    params = {"year": year, "subject": subject}
    if subject == "SCIENCE" and year in SCIENCE_2027_ROUTES and not UNITS.fullmatch(current_unit):
        prefix, route = SCIENCE_2027_ROUTES[year]
        try:
            items = _units(_read("units", params, route=route))
            if items:
                return [{**x, "value": prefix + x["value"][1:]} for x in items]
        except NativeRPHUnavailable:
            if current_unit:
                raise
    return _units(_read("units", params))


def list_native_lessons(year, subject, unit):
    route, args = _selection(year, subject, unit)
    if route == DLP_ROUTE:
        group = _dlp_catalogue(year, subject).get(unit)
        if group is None:
            raise NativeRPHUnavailable("Unknown DLP unit")
        return [{"value": row["id"], "label": row["label"].split(" · ", 1)[0] + " • " + row["title"],
                 "textbook_ref": row["book_reference"]} for row in group["lessons"]]
    data = (_read("lessons", args) if route == SEQUENCE_ROUTE else _read("lessons", args, route=route))
    if (not isinstance(data,dict)
            or data.get("source")!="telegram-runtime-v1"
            or not isinstance(data.get("items"),list)
            or len(data["items"]) > 500):
        raise NativeRPHUnavailable("Invalid Telegram lesson choices")
    result = data["items"]
    if any(not isinstance(x,dict) or not isinstance(x.get("value"),str)
           or not 0 < len(x["value"]) <= 100
           or any(ord(c)<32 for c in x["value"])
           or not isinstance(x.get("label"),str) or not x["label"].strip()
           for x in result):
        raise NativeRPHUnavailable("Unverified Telegram PdP entries")
    return result


def verified_native_sequence_available(year, subject, unit, lesson):
    route, selection = _selection(year, subject, unit, lesson)
    data = (_read("availability", selection) if route == SEQUENCE_ROUTE
            else _read("availability", selection, route=route))
    if not isinstance(data,dict) or data.get("available") is not True:
        raise NativeRPHUnavailable("Telegram PdP RPH not ready")
    return True


def request_native_sequence_rph(selection, fmt, *, opener=None):
    if fmt not in MIMES:
        raise ValueError("Invalid RPH format")
    if not isinstance(selection,dict) or selection.get("source") != "telegram-native-pdp-sequence":
        raise ValueError("Unknown source")
    route, args = _selection(selection.get("year"),selection.get("subject"),
                      selection.get("unit"),selection.get("lesson"))
    teacher = selection.get("teacher")
    if not valid_teacher_fields(teacher):
        raise ValueError("Invalid teacher data")
    payload = json.dumps({
        "selection":args,"teacher":teacher,"format":fmt
    },ensure_ascii=False).encode("utf-8")
    if len(payload) > 7000:
        raise NativeRPHUnavailable("Invalid native request size")
    base, token = _backend()
    req = Request(base + route + "/render",
                  data=payload,method="POST",headers={
                      "Authorization":"Bearer "+token,
                      "Content-Type":"application/json",
                      "Accept":MIMES[fmt],
                  })
    transport = opener or build_opener(HTTPSHandler(),BlockRedirects())
    try:
        with transport.open(req,timeout=40) as resp:
            if (resp.status != 200 or resp.headers.get(
                    "Content-Type","").split(";")[0].strip().lower()!=MIMES[fmt]):
                raise NativeRPHUnavailable("Invalid Telegram document response")
            contents=resp.read(MAX_DOCUMENT+1)
    except (HTTPError,URLError,OSError,TimeoutError):
        raise NativeRPHUnavailable("Native Telegram PdP document unavailable") from None
    if not 1000 <= len(contents) <= MAX_DOCUMENT:
        raise NativeRPHUnavailable("Invalid RPH byte size")
    if fmt=="pdf":
        if not contents.startswith(b"%PDF-"):
            raise NativeRPHUnavailable("Invalid PDF signature")
    else:
        if not contents.startswith(b"PK\x03\x04"):
            raise NativeRPHUnavailable("Invalid Word signature")
        try:
            with ZipFile(io.BytesIO(contents)) as doc:
                if doc.testzip() or "word/document.xml" not in doc.namelist():
                    raise NativeRPHUnavailable("Invalid Word archive")
        except (OSError,ValueError,BadZipFile):
            raise NativeRPHUnavailable("Invalid Word archive") from None
    return io.BytesIO(contents)
