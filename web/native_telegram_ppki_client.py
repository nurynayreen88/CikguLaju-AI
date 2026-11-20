"""Read and render PPKI from the authoritative Telegram catalog."""
from io import BytesIO
import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile

from web.native_telegram_rph_client import BlockRedirects, MAX_DOCUMENT, MIMES, NativeRPHUnavailable
from web.native_verified_rpt_rph_client import _backend
from web.rph_teacher_reflection import valid_teacher_fields

SOURCE = "ppki-pengurusan-kehidupan-v1"
SUBJECT = "PENGURUSAN_KEHIDUPAN_PPKI"
COMPONENT = "pengurusan-diri"
UNIT1 = "u01-pengurusan-diri"
UNIT = "u02-pengurusan-diri"
UNIT3 = "u03-pengurusan-diri"
UNIT4 = "u04-pengurusan-diri"
UNIT5 = "u05-pengurusan-diri"
UNIT_LESSONS = {
    UNIT: range(1, 15), UNIT3: range(15, 19), UNIT4: range(19, 24),
    UNIT5: range(24, 30), UNIT1: range(30, 40),
}
YEAR = 2
FORMATS = ("word", "pdf")
RPT_CODE = "pengurusan_kehidupan_ppki"


def _request(path, accept, limit, payload=None):
    base, token = _backend()
    headers = {"Authorization": "Bearer " + token, "Accept": accept}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(base + "/internal/rph/v1/ppki/" + path, data=data, headers=headers)
    timeout = 6 if path == "catalog" else 24
    try:
        with build_opener(HTTPSHandler(), BlockRedirects()).open(request, timeout=timeout) as response:
            if response.status != 200 or response.headers.get_content_type() != accept:
                raise NativeRPHUnavailable("Unexpected PPKI source response")
            body = response.read(limit + 1)
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        raise NativeRPHUnavailable("Source PPKI unavailable") from exc
    if not body or len(body) > limit:
        raise NativeRPHUnavailable("Invalid PPKI source size")
    return body


def catalog():
    try:
        obj = json.loads(_request("catalog", "application/json", 20000))
    except (UnicodeError, ValueError) as exc:
        raise NativeRPHUnavailable("Invalid PPKI catalog JSON") from exc
    expected = {"subjects": [SUBJECT], "components": [COMPONENT], "units": [UNIT],
                "lessons": [f"{n:03d}" for n in UNIT_LESSONS[UNIT]]}
    if not isinstance(obj, dict) or obj.get("source") != SOURCE or obj.get("year") != YEAR:
        raise NativeRPHUnavailable("Invalid PPKI catalog identity")
    for key, ids in expected.items():
        items = obj.get(key)
        if (not isinstance(items, list)
                or any(not isinstance(item, dict) or not isinstance(item.get("label"), str)
                       or not 1 <= len(item["label"]) <= 180 for item in items)
                or [item.get("value") for item in items] != ids):
            raise NativeRPHUnavailable("Invalid PPKI catalog choices")
    extra = obj.get("additional_units", [])
    expected_extra = list(UNIT_LESSONS)[1:]
    if not isinstance(extra, list) or len(extra) > len(expected_extra):
        raise NativeRPHUnavailable("Invalid PPKI additional units")
    by_unit = {UNIT: obj["lessons"]}
    for unit_id, unit in zip(expected_extra, extra):
        expected_lessons = [f"{n:03d}" for n in UNIT_LESSONS[unit_id]]
        accepted_lessons = [expected_lessons]
        if unit_id == UNIT5:
            accepted_lessons.append(expected_lessons[:4])
        if (not isinstance(unit, dict) or unit.get("value") != unit_id
                or not isinstance(unit.get("label"), str) or not 1 <= len(unit["label"]) <= 180
                or not isinstance(unit.get("lessons"), list)
                or any(not isinstance(item, dict) or not isinstance(item.get("label"), str)
                       or not 1 <= len(item["label"]) <= 180 for item in unit["lessons"])
                or [item.get("value") for item in unit["lessons"]] not in accepted_lessons):
            raise NativeRPHUnavailable("Invalid PPKI additional unit choices")
        obj["units"].append({"value": unit_id, "label": unit["label"]})
        by_unit[unit_id] = unit["lessons"]
    if any(item.get("formats") != list(FORMATS) or not isinstance(item.get("textbook_ref"), str)
           for lessons in by_unit.values() for item in lessons):
        raise NativeRPHUnavailable("Invalid PPKI material metadata")
    obj["units"].sort(key=lambda row: row["value"])
    obj["unit_numbers"] = [int(row["value"][1:3]) for row in obj["units"]]
    obj["lessons_by_unit"] = by_unit
    return obj


def get_options(kind, year, subject=None, component=None, unit=None):
    if (year != YEAR or kind not in ("subjects", "components", "units", "pdp")
            or (kind != "subjects" and subject != SUBJECT)
            or (kind == "units" and component != COMPONENT)
            or (kind == "pdp" and unit not in UNIT_LESSONS)):
        raise ValueError("Invalid PPKI catalog selection")
    source = catalog()
    if kind == "pdp":
        return source["lessons_by_unit"].get(unit, [])
    return source[kind]


def validate_selection(year, subject, unit, lesson):
    if year != YEAR or subject != SUBJECT or unit not in UNIT_LESSONS:
        raise ValueError("Invalid PPKI RPH selection")
    selected = next((row for row in catalog()["lessons_by_unit"].get(unit, ()) if row["value"] == lesson), None)
    if selected is None:
        raise ValueError("Invalid PPKI PdP")
    return selected


def _document(path, fmt, payload=None):
    body = _request(path, MIMES[fmt], MAX_DOCUMENT, payload)
    if fmt == "pdf" and (len(body) < 1000 or not body.startswith(b"%PDF-")):
        raise NativeRPHUnavailable("Corrupt PPKI PDF")
    if fmt == "word":
        try:
            with ZipFile(BytesIO(body)) as archive:
                if archive.testzip() or "word/document.xml" not in archive.namelist():
                    raise NativeRPHUnavailable("Corrupt PPKI Word")
        except (OSError, ValueError, BadZipFile) as exc:
            raise NativeRPHUnavailable("Corrupt PPKI Word") from exc
    return BytesIO(body)


def request_rph(selected, fmt):
    teacher = selected["teacher"]
    if fmt not in FORMATS or not valid_teacher_fields(teacher):
        raise ValueError("Invalid PPKI format or teacher metadata")
    selection = {key: selected[key] for key in ("year", "subject", "unit", "lesson")}
    return _document("render", fmt, {"selection": selection, "teacher": teacher, "format": fmt})


def request_rpt(*, combined=False):
    return _document("rpt-current.pdf" if combined else "rpt.pdf", "pdf")
