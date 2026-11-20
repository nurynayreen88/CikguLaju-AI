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
MANIPULATIVE_COMPONENT = "kemahiran-manipulatif"
MANIPULATIVE_UNIT1 = "u01-kemahiran-manipulatif"
MANIPULATIVE_UNIT2 = "u02-kemahiran-manipulatif"
MANIPULATIVE_UNIT3 = "u03-kemahiran-manipulatif"
UNIT1 = "u01-pengurusan-diri"
UNIT = "u02-pengurusan-diri"
UNIT3 = "u03-pengurusan-diri"
UNIT4 = "u04-pengurusan-diri"
UNIT5 = "u05-pengurusan-diri"
UNIT6 = "u06-pengurusan-diri"
UNIT_LESSONS = {
    UNIT: range(1, 15), UNIT3: range(15, 19), UNIT4: range(19, 24),
    UNIT5: range(24, 30), UNIT1: range(30, 40),
}
MANIPULATIVE_UNIT_LESSONS = {
    MANIPULATIVE_UNIT1: range(40, 54),
    MANIPULATIVE_UNIT2: range(54, 64),
    MANIPULATIVE_UNIT3: range(64, 72),
}
YEAR = 2
YEARS = (2, 3, 4, 5, 6)
YEAR3_LESSONS = {
    UNIT1: range(1, 18), UNIT: range(18, 36), UNIT3: range(36, 40),
    UNIT4: range(40, 44), UNIT5: range(44, 50),
}
YEAR3_MANIPULATIVE_UNIT_LESSONS = {
    MANIPULATIVE_UNIT1: range(50, 56),
    MANIPULATIVE_UNIT2: range(56, 62),
    MANIPULATIVE_UNIT3: range(62, 74),
}
YEAR4_LESSONS = {
    UNIT1: range(1, 10), UNIT: range(10, 26), UNIT3: range(26, 34), UNIT4: range(34, 40),
}
YEAR4_MANIPULATIVE_UNIT_LESSONS = {
    MANIPULATIVE_UNIT1: range(40, 55),
    MANIPULATIVE_UNIT2: range(55, 67),
    MANIPULATIVE_UNIT3: range(67, 79),
}
YEAR5_LESSONS = {
    UNIT1: range(1, 10), UNIT: range(10, 14), UNIT3: range(14, 22),
    UNIT4: range(22, 30), UNIT5: range(30, 34), UNIT6: range(34, 42),
}

YEAR5_MANIPULATIVE_UNIT_LESSONS = {
    MANIPULATIVE_UNIT1: range(42, 62),
    MANIPULATIVE_UNIT2: range(62, 75),
    MANIPULATIVE_UNIT3: range(75, 85),
}


YEAR6_LESSONS = {
    UNIT1: range(1, 9), UNIT: range(9, 16), UNIT3: range(16, 20),
    UNIT4: range(20, 24), UNIT5: range(24, 28), UNIT6: range(28, 36),
}


YEAR6_MANIPULATIVE_UNIT_LESSONS = {
    MANIPULATIVE_UNIT1: range(36, 54),
    MANIPULATIVE_UNIT2: range(54, 64),
    MANIPULATIVE_UNIT3: range(64, 70),
}

FORMATS = ("word", "pdf")
RPT_CODE = "pengurusan_kehidupan_ppki"
RPT_MANIPULATIVE_CODE = "kemahiran_manipulatif_ppki"
RPT_MANIPULATIVE_YEAR3_FILENAME = "CIKGULAJU_RPT_PPKI_KEMAHIRAN_MANIPULATIF_TAHUN_3_2027.pdf"
RPT_MANIPULATIVE_YEAR4_FILENAME = "CIKGULAJU_RPT_PPKI_KEMAHIRAN_MANIPULATIF_TAHUN_4_2027.pdf"
RPT_MANIPULATIVE_YEAR5_FILENAME = "CIKGULAJU_RPT_PPKI_KEMAHIRAN_MANIPULATIF_TAHUN_5_2027.pdf"
RPT_MANIPULATIVE_YEAR6_FILENAME = "CIKGULAJU_RPT_PPKI_KEMAHIRAN_MANIPULATIF_TAHUN_6_2027.pdf"
RPT_MANIPULATIVE_FILENAME = "CIKGULAJU_RPT_PPKI_KEMAHIRAN_MANIPULATIF_TAHUN_2_2027.pdf"


def _request(path, accept, limit, payload=None):
    base, token = _backend()
    headers = {"Authorization": "Bearer " + token, "Accept": accept}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(base + "/internal/rph/v1/ppki/" + path, data=data, headers=headers)
    timeout = 6 if path.split("?", 1)[0] == "catalog" else 24
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


def _validate_unit(unit, unit_id, accepted_lessons):
    if (not isinstance(unit, dict) or unit.get("value") != unit_id
            or not isinstance(unit.get("label"), str) or not 1 <= len(unit["label"]) <= 180
            or not isinstance(unit.get("lessons"), list)
            or any(not isinstance(item, dict) or not isinstance(item.get("label"), str)
                   or not 1 <= len(item["label"]) <= 180 for item in unit["lessons"])
            or [item.get("value") for item in unit["lessons"]] not in accepted_lessons):
        raise NativeRPHUnavailable("Invalid PPKI additional unit choices")


def catalog(year=YEAR):
    if year not in YEARS:
        raise ValueError("Unknown PPKI year")
    direct_units = {
        YEAR: UNIT_LESSONS, 3: YEAR3_LESSONS, 4: YEAR4_LESSONS, 5: YEAR5_LESSONS, 6: YEAR6_LESSONS,
    }[year]
    manipulative_units = {
        YEAR: MANIPULATIVE_UNIT_LESSONS,
        3: YEAR3_MANIPULATIVE_UNIT_LESSONS,
        4: YEAR4_MANIPULATIVE_UNIT_LESSONS,
        5: YEAR5_MANIPULATIVE_UNIT_LESSONS,
        6: YEAR6_MANIPULATIVE_UNIT_LESSONS,
    }[year]
    first_unit = next(iter(direct_units))
    try:
        path = "catalog" if year == YEAR else f"catalog?year={year}"
        obj = json.loads(_request(path, "application/json", 20000))
    except (UnicodeError, ValueError) as exc:
        raise NativeRPHUnavailable("Invalid PPKI catalog JSON") from exc
    expected = {"subjects": [SUBJECT], "components": [COMPONENT], "units": [first_unit],
                "lessons": [f"{n:03d}" for n in direct_units[first_unit]]}
    if not isinstance(obj, dict) or obj.get("source") != SOURCE or obj.get("year") != year:
        raise NativeRPHUnavailable("Invalid PPKI catalog identity")
    for key, ids in expected.items():
        items = obj.get(key)
        if (not isinstance(items, list)
                or any(not isinstance(item, dict) or not isinstance(item.get("label"), str)
                       or not 1 <= len(item["label"]) <= 180 for item in items)
                or [item.get("value") for item in items] != ids):
            raise NativeRPHUnavailable("Invalid PPKI catalog choices")
    extra = obj.get("additional_units", [])
    expected_extra = list(direct_units)[1:]
    if not isinstance(extra, list) or len(extra) > len(expected_extra):
        raise NativeRPHUnavailable("Invalid PPKI additional units")
    by_unit = {first_unit: obj["lessons"]}
    for unit_id, unit in zip(expected_extra, extra):
        expected_lessons = [f"{n:03d}" for n in direct_units[unit_id]]
        accepted_lessons = [expected_lessons]
        if year == YEAR and unit_id == UNIT5:
            accepted_lessons.append(expected_lessons[:4])
        _validate_unit(unit, unit_id, accepted_lessons)
        obj["units"].append({"value": unit_id, "label": unit["label"]})
        by_unit[unit_id] = unit["lessons"]
    manipulative = obj.get("kemahiran_manipulatif", [])
    if not isinstance(manipulative, list) or len(manipulative) > len(manipulative_units):
        raise NativeRPHUnavailable("Invalid PPKI Kemahiran Manipulatif units")
    manipulative_by_unit = {}
    for (unit_id, numbers), unit in zip(manipulative_units.items(), manipulative):
        expected_lessons = [f"{number:03d}" for number in numbers]
        accepted_lessons = [expected_lessons]
        if year == YEAR and unit_id == MANIPULATIVE_UNIT1 and len(manipulative) == 1:
            accepted_lessons.append(expected_lessons[:4])
        _validate_unit(unit, unit_id, accepted_lessons)
        manipulative_by_unit[unit_id] = unit["lessons"]

    rph_lessons = {**by_unit, **manipulative_by_unit}
    if any(item.get("formats") != list(FORMATS) or not isinstance(item.get("textbook_ref"), str)
           for lessons in rph_lessons.values() for item in lessons):
        raise NativeRPHUnavailable("Invalid PPKI material metadata")
    obj["units"].sort(key=lambda row: row["value"])
    obj["unit_numbers"] = [int(row["value"][1:3]) for row in obj["units"]]
    obj["lessons_by_unit"] = by_unit
    obj["rph_lessons_by_unit"] = rph_lessons
    obj["units_by_component"] = {COMPONENT: obj["units"]}
    if manipulative:
        obj["components"].append({"value": MANIPULATIVE_COMPONENT, "label": "Kemahiran Manipulatif"})
        obj["units_by_component"][MANIPULATIVE_COMPONENT] = [
            {"value": unit["value"], "label": unit["label"]} for unit in manipulative
        ]
    return obj


def get_options(kind, year, subject=None, component=None, unit=None):
    if (year not in YEARS or kind not in ("subjects", "components", "units", "pdp")
            or (kind != "subjects" and subject != SUBJECT)
            or (kind == "units" and component not in (COMPONENT, MANIPULATIVE_COMPONENT))
            or (kind == "pdp" and not accepted_unit(year, unit))):
        raise ValueError("Invalid PPKI catalog selection")
    source = catalog() if year == YEAR else catalog(year)
    if kind == "pdp":
        return source["rph_lessons_by_unit"].get(unit, [])
    if kind == "units":
        return source["units_by_component"].get(component, [])
    return source[kind]


def accepted_unit(year, unit):
    if year == 3:
        return unit in YEAR3_LESSONS or unit in YEAR3_MANIPULATIVE_UNIT_LESSONS
    if year == 4:
        return unit in YEAR4_LESSONS or unit in YEAR4_MANIPULATIVE_UNIT_LESSONS
    if year == 5:
        return unit in YEAR5_LESSONS or unit in YEAR5_MANIPULATIVE_UNIT_LESSONS
    if year == 6:
        return unit in YEAR6_LESSONS or unit in YEAR6_MANIPULATIVE_UNIT_LESSONS
    return year == YEAR and (unit in UNIT_LESSONS or unit in MANIPULATIVE_UNIT_LESSONS)


def validate_selection(year, subject, unit, lesson):
    if subject != SUBJECT or not accepted_unit(year, unit):
        raise ValueError("Invalid PPKI RPH selection")
    source = catalog() if year == YEAR else catalog(year)
    lessons = source["rph_lessons_by_unit"].get(unit, ())
    selected = next((row for row in lessons if row["value"] == lesson), None)
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


def request_rpt(*, combined=False, manipulative=False, year=YEAR):
    if year in (3, 4, 5, 6):
        path = "rpt-manipulatif.pdf" if manipulative else "rpt.pdf"
        return _document(f"{path}?year={year}", "pdf")
    if year != YEAR:
        raise ValueError("Invalid year for PPKI RPT")
    if manipulative:
        return _document("rpt-manipulatif.pdf", "pdf")
    return _document("rpt-current.pdf" if combined else "rpt.pdf", "pdf")
