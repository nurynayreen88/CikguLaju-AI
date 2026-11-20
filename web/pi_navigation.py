"""Derive Web navigation from the verified Pendidikan Islam source field."""

import re

PI_FIELDS = {
    "القرءان": "Al-Quran",
    "القرآن": "Al-Quran",
    "ختم": "Al-Quran",
    "حديث": "Hadis",
    "عقيدة": "Akidah",
    "عبادة": "Ibadah",
    "سيرة": "Sirah",
    "ادب": "Adab",
    "أدب": "Adab",
    "جاوي": "Jawi",
}
PI_FIELD_ORDER = tuple(dict.fromkeys(PI_FIELDS.values()))
GENERIC_RPT_ACTIVITIES = (
    "aktiviti berpandu, aplikasi dan pentaksiran formatif mengikut sp.",
    "aktiviti mengikut sk dan sp",
)

_STANDARD_CODE = re.compile(r"(?<![\d.])\d+\.\d+(?:\.\d+){0,2}(?![\d.])")


def pi_document_standards(codes, descriptions):
    """Extract the matching description when the source repeats a multi-code cell."""
    if not codes or len(codes) != len(descriptions):
        return ""
    standards = {}
    for code, description in zip(codes, descriptions):
        text = " ".join(str(description or "").split())
        # Telegram may already have removed the first code from the source cell.
        matches = [match for match in _STANDARD_CODE.finditer(text) if match.group() in codes]
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            chunk = text[match.end():end].strip(" ;،,:-–—")
            if chunk:
                standards.setdefault(match.group(), chunk)
        if text and (not matches or matches[0].group() != code and matches[0].start() > 0):
            chunk = text[:matches[0].start()] if matches else text
            standards.setdefault(code, chunk.strip(" ;،,:-–—"))
    if not all(standards.get(code) for code in codes):
        return ""
    return "\n".join(f"{code} {standards[code]}" for code in dict.fromkeys(codes))


def pi_rph_document_rows(state, rows):
    formatted = {}
    for field, kind in (("STANDARD KANDUNGAN", "sk"), ("STANDARD PEMBELAJARAN", "sp")):
        standards = pi_document_standards(
            state.get(f"selected_{kind}_codes", []), state.get(f"grouped_{kind}_texts", [])
        )
        if standards:
            formatted[field] = standards
    return {**rows, **formatted} if formatted else rows


def pi_navigation_unit(row):
    title = str(row.get("unit_title") or "").strip()
    if title:
        return title
    words = str(row.get("skill_focus") or "").split()
    return PI_FIELDS.get(words[0], "") if words else ""


def is_pi_recitation_session(row):
    """Match source-only Khatam/Tasmik sessions that have no coded standards."""
    if (row.get("mapping_status") != "rpt_only_no_textbook_page"
            or not str(row.get("objective_jawi") or "").strip()
            or "تسميع" not in str(row.get("assessment_note") or "")
            or pi_navigation_unit(row) != "Al-Quran"):
        return False
    if row.get("jenis") == "KHATAM_TASMIK":
        return True
    # The verified Year 2 RPT uses the KURIKULUM tag on the same oral sessions.
    return (row.get("jenis") == "KURIKULUM" and row.get("year_label") == "Tahun 2"
            and row.get("topic") in {"القرءان 1 جم 30 مينيت", "ختم القرءان 1 جم 30 مينيت"})
