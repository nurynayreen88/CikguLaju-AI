"""Derive Web navigation from the verified Pendidikan Islam source field."""

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
