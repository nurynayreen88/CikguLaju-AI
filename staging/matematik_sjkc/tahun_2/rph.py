"""Resolve each approved second-year SJKC Matematik plan by unit and PdP."""

from functools import lru_cache
from io import BytesIO
import json
import os
from pathlib import Path

from staging.matematik_sjkc.tahun_3.rph import _word, _pdf, teacher_lines

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[2] / "rpt_2027/sjkc/matematik/year_2_2027.json"
STEM = "RPH_2027_Matematik_SJKC_Tahun_2"
PDP_COUNT = 96
YEAR = 2
SUBJECT = "Matematik SJKC"
RELEASE_FLAG = "CIKGULAJU_MATEMATIK_SJKC_T2_RPH_ENABLED"


def enabled():
    return os.environ.get(RELEASE_FLAG) == "1"


@lru_cache(maxsize=1)
def lessons():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = data["lessons"]
    if (data["year"], data["school_type"], data["subject"]) != (YEAR, "SJKC", "Matematik"):
        raise ValueError("Unexpected Matematik SJKC Tahun 2 source")
    if [row["pdp"] for row in rows] != list(range(1, PDP_COUNT + 1)):
        raise ValueError("Invalid Matematik SJKC Tahun 2 sequence")
    return tuple(rows)


def resolve(unit, pdp):
    if type(unit) is not int or type(pdp) is not int or not 1 <= pdp <= PDP_COUNT:
        return None
    row = lessons()[pdp - 1]
    return row if row["unit_number"] == unit else None


def units():
    return tuple(dict.fromkeys((row["unit_number"], row["unit"]) for row in lessons()))


def render(lesson, fmt, teacher=None):
    output = BytesIO()
    lines = teacher_lines(teacher)
    reflection = (teacher or {}).get("reflection", "")
    if fmt == "word":
        ext = "docx"
        _word(lesson, output, lines, reflection, path=ROOT / f"{STEM}.{ext}")
    elif fmt == "pdf":
        ext = "pdf"
        _pdf(lesson, output, lines, reflection, path=ROOT / f"{STEM}.{ext}")
    else:
        raise ValueError("Unsupported RPH format")
    return f"{STEM}_PdP_{lesson['pdp']:03}.{ext}", output.getvalue()
