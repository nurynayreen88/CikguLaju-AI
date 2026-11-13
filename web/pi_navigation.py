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
