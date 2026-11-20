"""Verified scope for the first PPKI RPH and RPT collection."""
from functools import lru_cache

from staging.ppki.render_pengurusan_kehidupan import load_catalog

YEAR = 2
SUBJECT = "PENGURUSAN_KEHIDUPAN_PPKI"
UNIT = "u02-pengurusan-diri"
COMPONENT = "pengurusan-diri"
FORMATS = ("word", "pdf")
RPT_FILENAME = "CIKGULAJU_RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_UNIT_2_2027.pdf"


@lru_cache(maxsize=1)
def catalog():
    source = load_catalog()
    numbers = [lesson["pdp"] for lesson in source["lessons"]]
    if source["year"] != YEAR or numbers != [f"{n:03d}" for n in range(1, 15)]:
        raise ValueError("PPKI catalog identity mismatch")
    for lesson in source["lessons"]:
        sp = lesson["sp"]
        if sp not in source["learning_standards"] or sp.rsplit(".", 1)[0] not in source["content_standards"]:
            raise ValueError("PPKI curriculum mapping missing")
    return source


def options():
    source = catalog()
    return {
        "source": "ppki-pengurusan-kehidupan-v1",
        "year": YEAR,
        "subjects": [{"value": SUBJECT, "label": source["subject"]}],
        "components": [{"value": COMPONENT, "label": source["component"]}],
        "units": [{"value": UNIT, "label": source["unit"]}],
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


def selected_lesson(unit, number):
    if unit != UNIT:
        return None
    return next((lesson for lesson in catalog()["lessons"] if lesson["pdp"] == number), None)


def lesson_filename(number, fmt):
    suffix = {"word": "docx", "pdf": "pdf"}[fmt]
    return f"CIKGULAJU_RPH_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_{number}.{suffix}"
