"""Verified PPKI RPH and RPT collections."""
from functools import lru_cache
from pathlib import Path
import json

from staging.ppki.render_pengurusan_kehidupan import load_catalog

YEAR = 2
YEARS = (2, 3)
SUBJECT = "PENGURUSAN_KEHIDUPAN_PPKI"
UNIT1 = "u01-pengurusan-diri"
UNIT = "u02-pengurusan-diri"
UNIT3 = "u03-pengurusan-diri"
UNIT4 = "u04-pengurusan-diri"
UNIT5 = "u05-pengurusan-diri"
COMPONENT = "pengurusan-diri"
MANIPULATIVE_COMPONENT = "kemahiran-manipulatif"
MANIPULATIVE_UNIT1 = "u01-kemahiran-manipulatif"
MANIPULATIVE_UNIT2 = "u02-kemahiran-manipulatif"
MANIPULATIVE_UNIT3 = "u03-kemahiran-manipulatif"
FORMATS = ("word", "pdf")
UNIT_LESSONS = {
    UNIT1: range(30, 40), UNIT: range(1, 15), UNIT3: range(15, 19),
    UNIT4: range(19, 24), UNIT5: range(24, 30),
}

MANIPULATIVE_UNIT_LESSONS = {
    MANIPULATIVE_UNIT1: range(40, 54),
    MANIPULATIVE_UNIT2: range(54, 64),
    MANIPULATIVE_UNIT3: range(64, 72),
}
LESSONS_BY_UNIT = {**UNIT_LESSONS, **MANIPULATIVE_UNIT_LESSONS}
COMPONENT_UNITS = {
    COMPONENT: tuple(UNIT_LESSONS),
    MANIPULATIVE_COMPONENT: tuple(MANIPULATIVE_UNIT_LESSONS),
}
YEAR3_LESSONS = {UNIT1: range(1, 18), UNIT: range(18, 36), UNIT3: range(36, 40)}

# Keep the published order in the additional_units field.
UNIT_FILES = {
    UNIT3: "pengurusan_kehidupan_tahun2_unit3.json",
    UNIT4: "pengurusan_kehidupan_tahun2_unit4.json",
    UNIT5: "pengurusan_kehidupan_tahun2_unit5.json",
    UNIT1: "pengurusan_kehidupan_tahun2_unit1.json",
    MANIPULATIVE_UNIT1: "pengurusan_kehidupan_tahun2_kemahiran_manipulatif_unit1.json",
    MANIPULATIVE_UNIT2: "pengurusan_kehidupan_tahun2_kemahiran_manipulatif_unit2.json",
    MANIPULATIVE_UNIT3: "pengurusan_kehidupan_tahun2_kemahiran_manipulatif_unit3.json",
}
RPT_FILENAME = "CIKGULAJU_RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_UNIT_2_2027.pdf"
RPT_COMBINED_EDITION = "Unit 1–5"
RPT_COMBINED_FILENAME = "CIKGULAJU_RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_UNIT_1_2_3_4_5_2027.pdf"
RPT_MANIPULATIVE_FILENAME = "CIKGULAJU_RPT_PPKI_KEMAHIRAN_MANIPULATIF_TAHUN_2_2027.pdf"
RPT_YEAR3_EDITION = "Unit 1–3"
RPT_YEAR3_FILENAME = "CIKGULAJU_RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_3_UNIT_1_2_3_2027.pdf"


def component_units(year):
    if year == 3:
        return {COMPONENT: tuple(YEAR3_LESSONS)}
    if year == YEAR:
        return COMPONENT_UNITS
    raise ValueError("Unknown PPKI year")


@lru_cache(maxsize=len(LESSONS_BY_UNIT) + len(YEAR3_LESSONS))
def catalog(unit=UNIT, *, year=YEAR):
    if year == 3 and unit in YEAR3_LESSONS:
        filename = f"pengurusan_kehidupan_tahun3_unit{int(unit[1:3])}.json"
        source = json.loads(Path(__file__).with_name(filename).read_text(encoding="utf-8"))
        expected = YEAR3_LESSONS[unit]
    elif year == YEAR and unit == UNIT:
        source = load_catalog()
        expected = LESSONS_BY_UNIT[unit]
    elif year == YEAR and unit in UNIT_FILES:
        path = Path(__file__).with_name(UNIT_FILES[unit])
        source = json.loads(path.read_text(encoding="utf-8"))
        expected = LESSONS_BY_UNIT[unit]
    else:
        raise ValueError("Unknown PPKI unit")
    numbers = [lesson["pdp"] for lesson in source["lessons"]]
    if source["year"] != year or numbers != [f"{n:03d}" for n in expected]:
        raise ValueError("PPKI catalog identity mismatch")
    for lesson in source["lessons"]:
        sp = lesson["sp"]
        if sp not in source["learning_standards"] or sp.rsplit(".", 1)[0] not in source["content_standards"]:
            raise ValueError("PPKI curriculum mapping missing")
    return source


def _unit_options(unit, year=YEAR):
    source = catalog(unit, year=year)
    return {
        "value": unit,
        "label": source["unit"],
        "lessons": [
            {
                "value": lesson["pdp"],
                "label": f"PdP {lesson['pdp']} · {lesson['title']}",
                "textbook_ref": lesson["book"],
                "formats": list(FORMATS),
            }
            for lesson in source["lessons"]
        ],
    }


def options(year=YEAR):
    units = component_units(year)
    first_unit = UNIT if year == YEAR else units[COMPONENT][0]
    additional_units = UNIT_FILES if year == YEAR else units[COMPONENT]
    source = catalog(first_unit, year=year)
    first = _unit_options(first_unit, year)
    return {
        "source": "ppki-pengurusan-kehidupan-v1",
        "year": year,
        "subjects": [{"value": SUBJECT, "label": source["subject"]}],
        "components": [{"value": COMPONENT, "label": source["component"]}],
        "units": [{"value": first_unit, "label": first["label"]}],
        "lessons": first["lessons"],
        "additional_units": [_unit_options(unit, year) for unit in additional_units
                             if unit in units[COMPONENT] and unit != first_unit],
        "kemahiran_manipulatif": [_unit_options(unit, year) for unit in units.get(MANIPULATIVE_COMPONENT, ())],
    }


def selected_lesson(unit, number, *, year=YEAR):
    if not any(unit in units for units in component_units(year).values()):
        return None
    return next((lesson for lesson in catalog(unit, year=year)["lessons"] if lesson["pdp"] == number), None)


def lesson_filename(number, fmt, *, year=YEAR):
    suffix = {"word": "docx", "pdf": "pdf"}[fmt]
    return f"CIKGULAJU_RPH_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_{year}_{number}.{suffix}"
