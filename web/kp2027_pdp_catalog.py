"""Display-only KP2027 unit/PdP labels pinned to approved RPH source PDFs.

The private approved catalog remains authoritative for downloadable lesson numbers,
hashes and SP codes. Metadata never approves a document and is only attached to
available, verified Word/PDF pairs.
"""
from __future__ import annotations
import json
from pathlib import Path

_DATA = json.loads(Path(__file__).with_name("kp2027_pdp_source_labels_v1.json").read_text(encoding="utf-8"))


def _entry(subject, sp_code, lesson_no):
    mapping = _DATA.get("sp_labels", {}).get(subject, {})
    label = mapping.get(sp_code)
    if (type(lesson_no) is not int or lesson_no < 1
            or not isinstance(label, dict)
            or set(label) != {"unit", "tajuk"}
            or any(not isinstance(label[k], str) or not label[k].strip()
                   or len(label[k]) > 150 for k in ("unit", "tajuk"))):
        raise ValueError("Padanan unit atau tajuk PdP sumber KP2027 tidak lengkap")
    return {"no": lesson_no, "unit": label["unit"], "tajuk": label["tajuk"], "sp": sp_code}


def math_approved_items(approved_groups, source_catalog):
    """Only return entries from already-approved complete Word/PDF source pairs."""
    if not isinstance(approved_groups, dict) or set(approved_groups) != {"A", "B"}:
        raise ValueError("Kumpulan Matematik KP2027 tidak sah")
    result = {}
    for group in ("A", "B"):
        numbers = approved_groups[group]
        if (not isinstance(numbers, list) or len(numbers) > len(source_catalog[group])
                or len(numbers) != len(set(numbers))):
            raise ValueError("Senarai PdP Matematik tidak sah")
        entries = []
        for n in numbers:
            catalog_entry = source_catalog[group].get(str(n)) if type(n) is int else None
            if not isinstance(catalog_entry, dict):
                raise ValueError("PdP Matematik tidak ada dalam katalog disahkan")
            entries.append(_entry("MATH", catalog_entry["sp"], n))
        result[group] = entries
    return result


def alam_approved_items(approved_lessons, source_catalog):
    if (not isinstance(approved_lessons, list) or len(approved_lessons) > 64
            or len(approved_lessons) != len(set(approved_lessons))):
        raise ValueError("Senarai PdP Alam dan Manusia tidak sah")
    entries = []
    for n in approved_lessons:
        item = source_catalog.get(str(n)) if type(n) is int else None
        if not isinstance(item, dict):
            raise ValueError("PdP Alam dan Manusia tiada dalam katalog disahkan")
        entries.append(_entry("ALAM", item["sp"], n))
    return entries
