"""Select the exact existing Moral RPH referenced by a numbered 2027 RPT session."""
from functools import lru_cache
from pathlib import PurePosixPath
import re

from rpt_2027.pendidikan_moral.complete_96_downloads import (
    BASE, PHASE_NAMES, _field, _plain, _source_components, source_rows,
)

VARIANT = "moral-rpt-2027"
STATE_KEY = "_moral_rpt_2027_session"
SP = re.compile(r"(?<!\d)\d+\.\d+(?![\d.])")


@lru_cache(maxsize=5)
def _sessions(year):
    return tuple(source_rows(year, "A"))


@lru_cache(maxsize=480)
def load_plan(year, number):
    if type(year) is not int or not 2 <= year <= 6 or type(number) is not int or not 1 <= number <= 96:
        return None
    sessions = _sessions(year)
    if not sessions:
        return None
    record = sessions[number - 1]
    relative = PurePosixPath(record["Rujukan_RPH"])
    core = None
    if record["Modul"] == "TERAS":
        match = re.fullmatch(r"lesson_(\d{3})\.md", relative.name)
        if not match or str(relative.parent) != f"rph_standalone/pendidikan_moral/year{year}":
            return None
        # Preserve the existing validated core loader and its DSKP checks.
        from web.pendidikan_moral_80_runtime import load_candidate
        core = load_candidate(year, int(match[1]))
        if core is None:
            return None
        header = f"# RPH Pendidikan Moral Tahun {year} — PdP {match[1]}"
    elif record["Modul"] == "PENGUKUHAN":
        if str(relative) != f"rph_standalone/pendidikan_moral/pengukuhan/year{year}/sesi_{number:03d}.md":
            return None
        header = f"# RPH Pendidikan Moral Tahun {year} — Sesi {number:03d} (Pengukuhan)"
    else:
        return None
    try:
        path = BASE / relative
        if path.is_symlink():
            return None
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if raw.splitlines()[0:1] != [header]:
        return None
    unit = _field(raw, "Unit").partition(".")[0]
    sk = _field(raw, "SK")
    sp = _field(raw, "SP")
    if unit != record["Unit"] or sk.split(" ", 1)[0] != record["SK"] or SP.findall(sp) != record["SP"].split("; "):
        return None
    if core:
        sections = {name: core["steps"][name.casefold()] for name in PHASE_NAMES}
        sections["Objektif"] = core["objective"]
        criterion = core["criterion"]
    else:
        sections = _source_components(raw)
        criterion = _field(raw, "Kriteria kejayaan")
    materials = _field(raw, "BBM") or _field(raw, "Bahan")
    materials = re.sub(r";\s*fail `materials/[^`]+`\.?", "", materials)
    value = _field(raw, "Nilai") or _field(raw, "Tema/Nilai")
    if not all((criterion, materials, value, *sections.values())):
        return None

    phases = []
    for name in PHASE_NAMES[1:3]:
        heading = re.search(rf"(?m)^\*\*({name}[^\n*]*):\*\*", raw)
        label = heading[1] if heading else name
        phases.append(f"{label} — {sections[name]}")
    title = f"PdP {number:03d} — {record['Tajuk_Unit']}"
    return {
        "year": year, "number": number, "unit_no": int(unit),
        "unit": f"Unit {int(unit):02d} — {record['Tajuk_Unit']}",
        "title": title, "label": f"{title} ({record['Modul'].title()})",
        "path": str(relative),
        "fields": {key: _plain(value) for key, value in {
            "TAJUK": title,
            "STANDARD KANDUNGAN": sk,
            "STANDARD PEMBELAJARAN": sp,
            "OBJEKTIF PEMBELAJARAN": sections["Objektif"],
            "KRITERIA KEJAYAAN": criterion,
            "SET INDUKSI": sections["Set induksi"],
            "AKTIVITI UTAMA": "\n".join(phases),
            "PENTAKSIRAN": sections["Pengukuhan/Pentaksiran PBD"],
            "PENUTUP": sections["Penutup"],
            "BAHAN BANTU MENGAJAR": materials,
            "EMK / NILAI": value,
        }.items()},
    }
