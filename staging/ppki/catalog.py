"""Verified PPKI RPH and RPT collections."""
from functools import lru_cache
from pathlib import Path
import json

from staging.ppki.render_pengurusan_kehidupan import load_catalog

YEAR = 2
SUBJECT = "PENGURUSAN_KEHIDUPAN_PPKI"
UNIT1 = "u01-pengurusan-diri"
UNIT = "u02-pengurusan-diri"
UNIT3 = "u03-pengurusan-diri"
UNIT4 = "u04-pengurusan-diri"
UNIT5 = "u05-pengurusan-diri"
COMPONENT = "pengurusan-diri"
MANIPULATIVE_COMPONENT = "kemahiran-manipulatif"
MANIPULATIVE_UNIT1 = "u01-kemahiran-manipulatif"
FORMATS = ("word", "pdf")
UNIT_LESSONS = {
    UNIT1: range(30, 40), UNIT: range(1, 15), UNIT3: range(15, 19),
    UNIT4: range(19, 24), UNIT5: range(24, 30),
}

MANIPULATIVE_UNIT_LESSONS = {MANIPULATIVE_UNIT1: range(40, 44)}
LESSONS_BY_UNIT = {**UNIT_LESSONS, **MANIPULATIVE_UNIT_LESSONS}
COMPONENT_UNITS = {
    COMPONENT: tuple(UNIT_LESSONS),
    MANIPULATIVE_COMPONENT: tuple(MANIPULATIVE_UNIT_LESSONS),
}

# Keep the published order in the additional_units field.
UNIT_FILES = {
    UNIT3: "pengurusan_kehidupan_tahun2_unit3.json",
    UNIT4: "pengurusan_kehidupan_tahun2_unit4.json",
    UNIT5: "pengurusan_kehidupan_tahun2_unit5.json",
    UNIT1: "pengurusan_kehidupan_tahun2_unit1.json",
    MANIPULATIVE_UNIT1: "pengurusan_kehidupan_tahun2_kemahiran_manipulatif_unit1.json",
}
RPT_FILENAME = "CIKGULAJU_RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_UNIT_2_2027.pdf"
RPT_COMBINED_EDITION = "Unit 1–5"
RPT_COMBINED_FILENAME = "CIKGULAJU_RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_UNIT_1_2_3_4_5_2027.pdf"


@lru_cache(maxsize=len(LESSONS_BY_UNIT))
def catalog(unit=UNIT):
    if unit == UNIT:
        source = load_catalog()
    elif unit in UNIT_FILES:
        path = Path(__file__).with_name(UNIT_FILES[unit])
        source = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("Unknown PPKI unit")
    numbers = [lesson["pdp"] for lesson in source["lessons"]]
    if source["year"] != YEAR or numbers != [f"{n:03d}" for n in LESSONS_BY_UNIT[unit]]:
        raise ValueError("PPKI catalog identity mismatch")
    for lesson in source["lessons"]:
        sp = lesson["sp"]
        if sp not in source["learning_standards"] or sp.rsplit(".", 1)[0] not in source["content_standards"]:
            raise ValueError("PPKI curriculum mapping missing")
    return source


def _unit_options(unit):
    source = catalog(unit)
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


def options():
    source = catalog()
    first = _unit_options(UNIT)
    return {
        "source": "ppki-pengurusan-kehidupan-v1",
        "year": YEAR,
        "subjects": [{"value": SUBJECT, "label": source["subject"]}],
        "components": [{"value": COMPONENT, "label": source["component"]}],
        "units": [{"value": UNIT, "label": first["label"]}],
        "lessons": first["lessons"],
        "additional_units": [_unit_options(unit) for unit in UNIT_FILES if unit in UNIT_LESSONS],
        "kemahiran_manipulatif": [_unit_options(unit) for unit in MANIPULATIVE_UNIT_LESSONS],
    }


def selected_lesson(unit, number):
    if unit not in LESSONS_BY_UNIT:
        return None
    return next((lesson for lesson in catalog(unit)["lessons"] if lesson["pdp"] == number), None)


def lesson_filename(number, fmt):
    suffix = {"word": "docx", "pdf": "pdf"}[fmt]
    return f"CIKGULAJU_RPH_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_{number}.{suffix}"
