"""Verified navigation for the existing 696 PI Word/PDF collection.

The per-PdP field codes were read from the owner-approved v2 archive,
not inferred from a timetable/RPT record. This is non-teaching metadata:
it never edits the Word/PDF lessons. See tests for coverage and identity.
"""
from __future__ import annotations

from web.pi_696_private_bundle import YEARS, valid_pdp

# Q: al-Quran, A: Akidah, J: Jawi, I: Ibadah, S: Sirah, D: Adab, H: Hadis.
FIELD_LABELS = {
    "Q": "Al-Quran", "H": "Hadis", "A": "Akidah",
    "I": "Ibadah", "S": "Sirah", "D": "Adab", "J": "Jawi",
}
FIELD_ORDER = ("Q", "H", "A", "I", "S", "D", "J")
YEAR_FIELDS = {
    2: "QAJQAJQAJQIJQIJQIJQSJQQSJQDJQDJQAJQAJQAJQIJQIJQIJQSJQSJQDJQDJQAJQAJQAJQIJQIJQIJQSJQSJQDJQDJQIJQIJQIJQDJQDJQDJQIJ",
    3: "QQAJQQAJQQAJQQIJQQIJQQIJQQSJQQSJQQSJQQDJQQDJQQDJQQIJQQIJQQIJQQSJQQSJQQSJQQHJQQHJQQHJQQDJQQDJQQDJQQAJQQAJQQAJQQIQQIJQQIJQQSJQQSJQQSJQQDJQQDJQQDJQQDJ",
    4: "QQAJQQAJQQIJQQIJQQIJQQSJQQSJQQSJQQDJQQDJQQAJQQAJQQIJQQIJQQIJQQSJQQSJQQSJQQDJQQDJQQHJQQHJQQHJQQAJQQAJQQIJQQIJQQIQQSJQQSJQQSJQQDJQQDJQQAJQQAJQQDJQQDJQQDJ",
    5: "QQAJQQAJQQIJQQIJQQIJQQSJQQSJQQSJQQDJQQDJQQAJQQAJQQIJQQIJQQIJQQSJQQSJQQSJQQDJQQDJQQHJQQHJQQHJQQAJQQAJQQIJQQIQQIJQQSJQQSJQQDJQQDJQQAJQQAJQQIJQQIJ",
    6: "QQAJQQAJQQIJQQIJQQIJQQSJQQSJQQSJQQDJQQDJQQAJQQAJQQIJQQIJQQIIQQSJQQSJQQSJQQDJQQDJQQHJQQHJQQHJQQAJQQAJQQIJQQIQQIJQQSJQQSJQQDJQQDJQQAJQQAJQQAJQQIJ",
}

if (set(YEAR_FIELDS) != set(YEARS)
        or any(len(YEAR_FIELDS[y]) != count for y, count in YEARS.items())
        or any(set(seq) - set(FIELD_LABELS) for seq in YEAR_FIELDS.values())
        or sum(map(len, YEAR_FIELDS.values())) != 696):
    raise RuntimeError("PI v2 source-backed navigation manifest invalid")


def unit_options(year):
    """Keep the familiar Pendidikan Islam Bidang/Unit selector."""
    if type(year) is not int or year not in YEARS:
        return []
    used = set(YEAR_FIELDS[year])
    return [{"value": FIELD_LABELS[key], "label": FIELD_LABELS[key]}
            for key in FIELD_ORDER if key in used]


def pdp_options(year, unit):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Invalid Pendidikan Islam year")
    if unit not in FIELD_LABELS.values():
        raise ValueError("Unknown Pendidikan Islam unit")
    allowed = {k for k, name in FIELD_LABELS.items() if name == unit}
    return [{"value": str(number), "label": f"PdP {number:03d}", "pdp_no": number}
            for number, key in enumerate(YEAR_FIELDS[year], 1) if key in allowed]


def valid_choice(year, unit, lesson):
    number = valid_pdp(year, lesson)
    if not any(FIELD_LABELS[key] == unit for key in [YEAR_FIELDS[year][number - 1]]):
        raise ValueError("PdP does not match its verified Pendidikan Islam unit")
    return number
