"""Scoped, reversible Sejarah primary 2027 Telegram RPH proposal bridge.

2027 Year 4–6 plans are documented DRAF, not individually approved textbooks.
This overlay uses the *existing* Telegram class/date, subscription, free-credit,
native Word/PDF and callback flow. It never mutates databases or READY flags.
Opt-out: CIKGULAJU_SEJARAH_2027_USER_ENABLED=0.
"""
from __future__ import annotations

import csv
from functools import lru_cache
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FLAG = "CIKGULAJU_SEJARAH_2027_USER_ENABLED"
SUBJECT = "Sejarah"
YEARS = (4, 5, 6)
SELECTION = "_sejarah_2027_selected_pdp"


def year_number(value):
    value = str(value or "").strip()
    match = re.fullmatch(r"(?i)(?:Tahun\s*)?([4-6])", value)
    return int(match[1]) if match else None


@lru_cache(maxsize=6)
def _catalog(year, base_path):
    """Reject a whole year if even one RPH/RPT/DSKP record disagrees."""
    if year not in YEARS:
        return ()
    base = Path(base_path).resolve()
    try:
        data = json.loads((base / f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json").read_text(encoding="utf-8"))
        standards = json.loads((base / f"curriculum/sejarah/y{year}_dskp_crosswalk_DRAF.json").read_text(encoding="utf-8"))
        units = json.loads((base / f"curriculum/sejarah/y{year}_buku_teks_unit_map_20261106.json").read_text(encoding="utf-8"))
        with (base / f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.csv").open(encoding="utf-8", newline="") as fh:
            rpt = list(csv.DictReader(fh))
        lessons = data["lessons"]
        if len(lessons) != len(rpt) or len(lessons) != 36:
            return ()
        known_codes = {sp["code"] for sk in standards["standards"] for sp in sk["sp"]}
        unit_map = {str(x["sk"]): x for x in units["units"]}
        result = []
        for n, (row, plan) in enumerate(zip(lessons, rpt), 1):
            ident = f"SEJ-T{year}-PDP-{n:03d}"
            r = row["rph"]
            bt = r["textbook_reference"]
            if (row.get("id") != ident or row.get("num") != n
                    or plan.get("ID") != ident or plan.get("Status") == "READY"
                    or r.get("year") != year or r.get("academic_year") != 2027
                    or r.get("subject") != SUBJECT or not str(r.get("status", "")).startswith("DRAF")
                    or r.get("teacher_approval") is not False
                    or r.get("textbook_page_verified") is not False
                    or not r.get("sp_codes") or not set(r["sp_codes"]) <= known_codes):
                return ()
            unit = unit_map.get(str(r.get("sk")))
            if (not unit or bt.get("unit_title") != unit["name"]
                    or bt.get("unit_number") != unit["number"]
                    or not bt.get("checked_focus_pages", {}).get("text_checked")
                    or not bt["checked_focus_pages"].get("printed_page_range")):
                return ()
            phases = ("set_induksi", "aktiviti_1", "aktiviti_2", "pengukuhan_pbd", "penutup")
            if (sum(r[p]["min"] for p in phases) != 60
                    or any(not r[p].get("activity") for p in phases)
                    or not r.get("objective") or not r.get("success_criteria")
                    or not r.get("bbm")):
                return ()
            # The actual original RPH must exist, even though the native
            # user document is made from the JSON source for parity.
            md = base / f"rph_standalone/sejarah/tahun_{year}/RPH_{ident}.md"
            if not md.is_file() or md.is_symlink():
                return ()
            result.append({"id": ident, "pdp": n, "year": year, "rph": r,
                           "unit": unit["number"], "unit_title": unit["name"]})
        return tuple(result)
    except (OSError, KeyError, ValueError, TypeError, csv.Error):
        return ()


def _lesson(year, pdp, *, root=ROOT):
    if type(year) is not int or year not in YEARS or type(pdp) is not int or not 1 <= pdp <= 36:
        return None
    entries = _catalog(year, str(Path(root).resolve()))
    return entries[pdp - 1] if len(entries) == 36 else None


def _selected(state, *, root=ROOT):
    if not isinstance(state, dict) or state.get("subject") != SUBJECT:
        return None
    year = year_number(state.get("year") or state.get("year_label"))
    ident = state.get(SELECTION)
    if not year or not isinstance(ident, dict) or ident.get("year") != year:
        return None
    pdp = ident.get("pdp")
    row = _lesson(year, pdp, root=root)
    if (not row or str(state.get("lesson_no") or "") != str(pdp)
            or str(state.get("sp_code") or "") not in row["rph"]["sp_codes"]
            or str(state.get("sk_code") or "") != row["rph"]["sk"]):
        return None
    return row


def adapt_rows(state, rows, *, root=ROOT):
    """Only approved *selection identity*, not teacher content approval."""
    row = _selected(state, root=root)
    if row is None or not isinstance(rows, dict):
        return rows
    r = row["rph"]
    focus = r["textbook_reference"]["checked_focus_pages"]["printed_page_range"]
    values = "; ".join(v.get("text", "") for v in r.get("values_sp", ()))
    result = dict(rows)
    result.update({
        "MATA PELAJARAN": SUBJECT,
        "TAHUN/TINGKATAN": f"Tahun {row['year']}",
        "TAJUK": f"{row['unit_title']} — PdP {row['pdp']:03d} (DRAF)",
        "STANDARD KANDUNGAN": f"{r['sk']} — {r['sk_title']}",
        "STANDARD PEMBELAJARAN": ", ".join(r["sp_codes"]),
        "OBJEKTIF PEMBELAJARAN": "; ".join(r["objective"]),
        "KRITERIA KEJAYAAN": r["success_criteria"],
        "PENGETAHUAN SEDIA ADA": "Pengetahuan murid tentang " + row["unit_title"],
        "BAHAN BANTU MENGAJAR": (f"Buku Teks Sejarah Tahun {row['year']}, "
                                f"rujukan isi PdP hlm. {focus}; bahan seperti dalam RPH"),
        "EMK / NILAI": values or "Patriotisme; hormat dan kerjasama",
        "KBAT / PAK21": "Kemahiran Pemikiran Sejarah: menilai bukti, membuat inferens",
        "SET INDUKSI": r["set_induksi"]["activity"],
        "AKTIVITI UTAMA": (
            "Aktiviti 1 (20 min) — " + r["aktiviti_1"]["activity"] + "\n"
            "Aktiviti 2 (20 min) — " + r["aktiviti_2"]["activity"] + "\n"
            "Pengukuhan dan PBD (10 min) — " + r["pengukuhan_pbd"]["activity"]),
        "PENTAKSIRAN": r["pengukuhan_pbd"]["activity"],
        "PENUTUP": r["penutup"]["activity"],
        "PEMULIHAN / PENGAYAAN": "Bimbing murid yang masih memerlukan sokongan.",
        "REFLEKSI": r["reflection"],
    })
    return result


def install(ns, *, enabled=None, root=ROOT):
    """Add just the Sejarah Year 4–6 menu; preserve all original handlers."""
    if enabled is None:
        enabled = os.environ.get(FLAG, "1") == "1"
    if not enabled or ns.get("SEJARAH_2027_USER_BRIDGE_ACTIVE"):
        return bool(ns.get("SEJARAH_2027_USER_BRIDGE_ACTIVE"))
    required = ("callback", "send", "_rph_rows", "_lesson_to_class_v2439")
    if any(not callable(ns.get(n)) for n in required):
        return False
    if any(len(_catalog(y, str(Path(root).resolve()))) != 36 for y in YEARS):
        return False
    subjects = ns.get("SUBJECTS_BY_GRADE")
    state = ns.get("state")
    if not isinstance(subjects, dict) or not isinstance(state, dict):
        return False

    previous_callback = ns["callback"]
    previous_rows = ns["_rph_rows"]
    send = ns["send"]
    for y in YEARS:
        options = subjects.get(f"Tahun {y}")
        if not isinstance(options, list):
            return False
    for y in YEARS:
        options = subjects[f"Tahun {y}"]
        if SUBJECT not in options:
            options.append(SUBJECT)

    def units_menu(cid):
        st = state.setdefault(cid, {})
        y = year_number(st.get("year"))
        entries = _catalog(y, str(Path(root).resolve())) if y else ()
        if len(entries) != 36:
            return send(cid, "Bahan Sejarah belum tersedia.",
                        [[{"text": "⬅️ Pilih Tahun", "callback_data": "choose_grade"}]])
        units = dict.fromkeys((r["unit"], r["unit_title"]) for r in entries)
        kb = [[{"text": f"Unit {number}: {title}"[:60],
                "callback_data": f"sej27u|{number:02d}"}] for number, title in units]
        kb.append([{"text": "⬅️ Tukar subjek", "callback_data": "back_subjects"}])
        return send(cid, f"📘 <b>Sejarah Tahun {y} (2027)</b>\n"
                    "Pilih unit, kemudian PdP. RPH ialah draf boleh sunting.", kb)

    def callback(cid, data):
        value = str(data or "")
        st = state.setdefault(cid, {})
        y = year_number(st.get("year"))
        if value == "sub_Sejarah" and y in YEARS:
            st["subject"] = SUBJECT
            st.pop(SELECTION, None)
            st.pop("_sejarah_2027_unit", None)
            return units_menu(cid)
        if value.startswith("sej27u|") or value.startswith("sej27p|"):
            if st.get("subject") != SUBJECT or y not in YEARS:
                return send(cid, "Pilihan Sejarah telah tamat. Sila pilih semula subjek.")
            if value.startswith("sej27u|"):
                match = re.fullmatch(r"sej27u\|(\d{2})", value)
                if not match:
                    return units_menu(cid)
                unit = int(match[1])
                entries = [r for r in _catalog(y, str(Path(root).resolve())) if r["unit"] == unit]
                if not entries:
                    return units_menu(cid)
                st["_sejarah_2027_unit"] = unit
                st.pop(SELECTION, None)
                kb = [[{"text": f"PdP {x['pdp']:03d} — {x['rph']['title']}"[:62],
                        "callback_data": f"sej27p|{x['pdp']:03d}"}] for x in entries]
                kb.append([{"text": "⬅️ Unit lain", "callback_data": "sub_Sejarah"}])
                return send(cid, f"📖 <b>Unit {unit}: {entries[0]['unit_title']}</b>\nPilih PdP:", kb)
            match = re.fullmatch(r"sej27p\|(\d{3})", value)
            if not match:
                return units_menu(cid)
            pdp = int(match[1])
            row = _lesson(y, pdp, root=root)
            if row is None or row["unit"] != st.get("_sejarah_2027_unit"):
                return units_menu(cid)
            r = row["rph"]
            for key in ("selected_sk", "sk_code", "selected_sp", "sp_code",
                        "selected_sk_codes", "selected_sp_codes", "grouped_sk_codes",
                        "grouped_sp_codes", "topic", "unit", "lesson_no", "pdp_no"):
                st.pop(key, None)
            st.update({
                "task": "quick_material", "quick_material_flow": True,
                "assessment_mode": "formative", "rph_mode": "fast_rpt",
                "lesson_no": str(pdp), "pdp_no": pdp, "lesson": str(pdp),
                "topic": r["title"], "unit": f"Unit {row['unit']}: {row['unit_title']}",
                "unit_title": row["unit_title"],
                "sk_code": r["sk"], "selected_sk": r["sk"],
                "selected_sk_codes": [r["sk"]], "grouped_sk_codes": [r["sk"]],
                "sp_code": r["sp_codes"][0], "selected_sp": r["sp_codes"][0],
                "selected_sp_codes": list(r["sp_codes"]),
                "grouped_sp_codes": list(r["sp_codes"]),
                "quick_content_v2391": r["title"],
                SELECTION: {"year": y, "pdp": pdp},
            })
            return ns["_lesson_to_class_v2439"](cid)
        return previous_callback(cid, data)

    def rows(state_value, *args, **kwargs):
        base = previous_rows(state_value, *args, **kwargs)
        return adapt_rows(state_value, base, root=root)

    ns["callback"] = callback
    ns["_rph_rows"] = rows
    ns["SEJARAH_2027_USER_BRIDGE_ACTIVE"] = True
    return True
