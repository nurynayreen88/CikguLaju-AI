"""Subject-specific PPKI release catalog. Legacy Pengurusan Kehidupan stays separate.

Only a bank with status READY and each selected lesson READY is returned.
Draft content is never exported by this interface.
"""
import json
from pathlib import Path
from staging.ppki.catalog import FORMATS

BANKS = {
    (2, "BAHASA_INGGERIS_PPKI"): ("english_year2_unit1_release.json", "english_year2_units2_4_release.json", "english_year2_units5_8_release.json", "english_year2_all_units_draft.json"),
    (2, "BAHASA_MELAYU_PPKI"): ("bahasa_melayu_tahun2_tema1_draft.json", "bahasa_melayu_tahun2_tema2_6_draft.json"),
    (2, "MATEMATIK_PPKI"): ("matematik_tahun2_all_units_draft.json",),
    (2, "PENDIDIKAN_ISLAM_PPKI"): ("pendidikan_islam_tahun2_draft.json",),
    (2, "PENDIDIKAN_JASMANI_PPKI"): ("pendidikan_jasmani_tahun2_draft.json",),
    (2, "PENDIDIKAN_MORAL_PPKI"): ("pendidikan_moral_tahun2_draft.json",),
    (2, "PENDIDIKAN_SENI_KREATIF_PPKI"): ("pendidikan_seni_kreatif_tahun2_draft.json",),
}


def approved_records(year, subject):
    records = []
    seen = set()
    for filename in BANKS.get((year, subject), ()):
        bank = json.loads(Path(__file__).with_name(filename).read_text(encoding="utf-8"))
        if bank.get("year") != year or bank.get("subject_id") != subject:
            raise ValueError("PPKI bank identity mismatch")
        if bank.get("status") != "READY" or bank.get("format_blocker"):
            continue
        for lesson in bank["lessons"]:
            if lesson.get("status") != "READY":
                continue
            unit = str(lesson["unit"])
            number = lesson["pdp"]
            if not bank["units"].get(unit) or number in seen:
                raise ValueError("Invalid PPKI release unit or duplicate PdP")
            seen.add(number)
            records.append((bank, lesson))
    return records


def subject_options(year, subject):
    units = {}
    for bank, lesson in approved_records(year, subject):
        unit = str(lesson["unit"])
        entry = units.setdefault(unit, {"value": unit, "label": bank["units"][unit], "lessons": []})
        entry["lessons"].append({
            "value": lesson["pdp"], "label": lesson["title"],
            "textbook_ref": lesson["textbook_page"], "formats": list(FORMATS),
        })
    return {"source": "ppki-subject-v1", "year": year, "subject": subject,
            "units": list(units.values()), "available": bool(units)}


def approved_selection(year, subject, unit, number):
    return next(((bank, lesson) for bank, lesson in approved_records(year, subject)
                 if str(lesson["unit"]) == unit and lesson["pdp"] == number), None)
