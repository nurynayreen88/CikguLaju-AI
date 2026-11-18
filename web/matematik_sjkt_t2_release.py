"""Published-source adapter for Matematik SJKT Tahun 2, after content approval."""

import os

from audits.matematik_sjkt_tahun_2 import eksport_rph
from web.matematik_sjkt_t2_review import FORMATS, TITLE, UNIT_NAMES, YEAR

SUBJECT = TITLE.removesuffix(f" Tahun {YEAR}")
RELEASE_FLAG = "CIKGULAJU_MATEMATIK_SJKT_T2_RPH_ENABLED"


def enabled():
    return os.environ.get(RELEASE_FLAG) == "1"


def units():
    return tuple(enumerate(UNIT_NAMES, 1))


def _lesson(row):
    return {
        **row, "unit_number": row["unit"], "unit": UNIT_NAMES[row["unit"] - 1],
        "topic": row["tajuk_tamil"],
    }


def lessons():
    return tuple(_lesson(row) for row in eksport_rph.lessons())


def resolve(unit, pdp):
    row = eksport_rph.resolve(unit, pdp)
    return _lesson(row) if row else None


def render(row, fmt, teacher):
    return eksport_rph.render(row["unit_number"], row["pdp"], FORMATS[fmt], teacher, review=False)
