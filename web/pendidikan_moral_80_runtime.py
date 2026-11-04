"""2027 Moral Year 2-6 source-backed *provisional* RPH bridge.

No DB writes, no credit/subscription changes and no change to other subjects.
The existing class/lesson navigation and native Word/PDF generator own delivery.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = "Pendidikan Moral"
FIELD = re.compile(r"^\*\*([^*:\n]{1,70}):\*\*\s*(.+)$", re.M)
PHASE = re.compile(
    r"^\*\*(Set induksi|Aktiviti 1|Aktiviti 2|Pengukuhan/Pentaksiran PBD|Penutup)"
    r"[^\n]*?\*\*\s*:?\s*(.+)$", re.M | re.I)
HEADER = re.compile(r"^# RPH Pendidikan Moral Tahun ([2-6]) — PdP (\d{3})\s*$", re.M)
SP_CODE = re.compile(r"(?<!\d)(\d+\.\d+)(?![\d.])")


def _year(value):
    value = str(value or "").strip().casefold()
    m = re.fullmatch(r"(?:tahun\s+)?([2-6])(?:\s*\(sk\))?", value)
    return int(m[1]) if m else None


def _clean(value):
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", str(value or "")).strip()


@lru_cache(maxsize=5)
def _index(year):
    path = ROOT / "rpt_2027" / "pendidikan_moral" / ("year%d_crosswalk_DSKP.json" % year)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        units = data.get("units", [])
        if data.get("status") != "DRAF_SEMAK" or len(units) != 14:
            return None
        if any(int(u.get("unit", -1)) != n or len(u.get("sp", [])) != 5 for n, u in enumerate(units, 1)):
            return None
        return units
    except (OSError, ValueError, TypeError):
        return None


@lru_cache(maxsize=210)
def load_candidate(year, number):
    if type(year) is not int or year not in range(2, 7) or type(number) is not int or not 1 <= number <= 42:
        return None
    units = _index(year)
    if units is None:
        return None
    unit_index, phase = divmod(number - 1, 3)
    source = units[unit_index]
    expected = source["sp"][phase * 2:phase * 2 + 2] if phase < 2 else source["sp"][4:5]
    path = ROOT / "rph_standalone" / "pendidikan_moral" / ("year%d" % year) / ("lesson_%03d.md" % number)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = HEADER.search(raw)
    if not match or (int(match[1]), int(match[2])) != (year, number):
        return None
    if "DRAF SEMAK" not in raw or "BELUM READY" not in raw:
        return None
    meta = {name.strip().casefold(): value.strip() for name, value in FIELD.findall(raw)}
    sp = SP_CODE.findall(meta.get("sp", ""))
    if sp != [entry["code"] for entry in expected]:
        return None
    if any(entry["text"] not in raw for entry in expected):
        return None
    steps = {key.casefold(): _clean(value) for key, value in PHASE.findall(raw)}
    required = ("set induksi", "aktiviti 1", "aktiviti 2", "pengukuhan/pentaksiran pbd", "penutup")
    if any(len(steps.get(k, "")) < 30 for k in required):
        return None
    obj = re.search(r"(?ms)^## Objektif dan kriteria kejayaan\s*\n(.+?)\n## Langkah PdP\s*$", raw)
    if not obj or "Kriteria kejayaan:" not in obj[1]:
        return None
    objective, criterion = obj[1].split("Kriteria kejayaan:", 1)
    if not objective.strip() or not criterion.strip():
        return None
    sk = str(source.get("sk_code") or ("%d.0" % (unit_index + 1)))
    sk_text = meta.get("sk", "")
    if sk not in sk_text:
        return None
    return dict(year=year, number=number, unit=source, sp=sp, sk=sk,
                objective=_clean(objective), criterion=_clean(criterion),
                steps=steps, materials=_clean(meta.get("bbm", "")),
                value=_clean(meta.get("nilai", "")), title=_clean(meta.get("unit", "")))


def adapt_rows(state, rows):
    if not isinstance(state, dict) or not isinstance(rows, dict):
        return rows
    if state.get("subject") != SUBJECT:
        return rows
    year = _year(state.get("year") or state.get("year_label"))
    raw = str(state.get("lesson_no") or state.get("pdp_no") or "").strip()
    if year is None or not raw.isascii() or not raw.isdecimal():
        return rows
    candidate = load_candidate(year, int(raw))
    if candidate is None:
        return rows
    selected_sp = str(state.get("sp_code") or "").strip()
    if selected_sp and selected_sp not in candidate["sp"]:
        return rows
    selected_sk = str(state.get("sk_code") or "").strip()
    if selected_sk and selected_sk != candidate["sk"]:
        return rows
    p = candidate
    result = dict(rows)
    steps = p["steps"]
    result.update({
        "MATA PELAJARAN": SUBJECT,
        "TAHUN/TINGKATAN": "Tahun %d" % year,
        "TAJUK": "CADANGAN CIKGULAJU (SEMAKAN GURU) — " + p["title"],
        "STANDARD KANDUNGAN": p["sk"],
        "STANDARD PEMBELAJARAN": "; ".join(p["sp"]),
        "OBJEKTIF PEMBELAJARAN": p["objective"],
        "KRITERIA KEJAYAAN": p["criterion"],
        "SET INDUKSI": steps["set induksi"],
        "AKTIVITI UTAMA": "Aktiviti 1 — " + steps["aktiviti 1"] + "\n\nAktiviti 2 — " + steps["aktiviti 2"],
        "PENTAKSIRAN": steps["pengukuhan/pentaksiran pbd"],
        "PENUTUP": steps["penutup"],
        "BAHAN BANTU MENGAJAR": p["materials"],
        "EMK / NILAI": p["value"],
    })
    return result


def install(runtime):
    """Opt-out emergency switch; only replaces Moral RPH rows for valid PdP."""
    if os.environ.get("CIKGULAJU_MORAL_80_ENABLED", "1") != "1":
        return False
    if getattr(runtime, "CIKGULAJU_MORAL_80_ACTIVE", False):
        return True
    original = getattr(runtime, "_rph_rows", None)
    if not callable(original):
        return False

    def rows(state, *args, **kwargs):
        base = original(state, *args, **kwargs)
        try:
            return adapt_rows(state, base)
        except Exception as exc:
            print("Moral 80 source fallback:", repr(exc), flush=True)
            return base

    runtime._rph_rows = rows
    runtime.CIKGULAJU_MORAL_80_ACTIVE = True
    return True
