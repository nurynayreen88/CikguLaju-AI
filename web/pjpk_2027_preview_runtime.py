"""PJPK Tahun 2–6 2027 DRAF RPH in the regular Telegram lesson flow.

Loads numbered Markdown sources matched to the current 339-record RPT manifest. The existing
class/date, RPH generation, Word/PDF renderer, access and credit gates stay
responsible for delivery. Nothing is marked READY or written to a database.
The production WSGI explicitly enables this isolated bridge; the original
RPH credit checks remain responsible for delivery.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"
FLAG = "CIKGULAJU_PJPK_PREVIEW_ENABLED"
SUBJECTS = {"Pendidikan Jasmani": "pj", "Pendidikan Kesihatan": "pk"}
MAXIMUM = {"pj": {2: 37, 3: 38, 4: 34, 5: 33, 6: 34},
           "pk": {2: 35, 3: 32, 4: 32, 5: 32, 6: 32}}
PDP_RE = re.compile(r"^lesson_(\d{3})\.md$")
MARKDOWN_LABEL = re.compile(r"^\*\*([^*\n]+?):\*\*\s*(.*?)\s*$")
CODE_SK = re.compile(r"(?<!\d)(\d+\.\d+)(?![\d.])")
CODE_SP = re.compile(r"(?<!\d)(\d+\.\d+\.\d+)(?![\d.])")


def _year(value):
    raw = str(value or "").strip().lower()
    m = re.fullmatch(r"(?:(?:tahun|year)\s+)?([2-6])(?:\s*\(sk\))?", raw)
    return int(m.group(1)) if m else None


def _record_path(year, short_subject, number):
    return "rph_standalone/pjpk/year%d_%s/lesson_%03d.md" % (
        year, short_subject, number)


@lru_cache(maxsize=4)
def _manifest(root):
    """Fail closed unless the current 2027 RPT contains exactly 339 DRAF PdP."""
    try:
        data = json.loads((Path(root) / MANIFEST).read_text(encoding="utf-8"))
        if (data.get("year") != 2027 or data.get("ready") is not False
                or len(data.get("records", ())) != 339):
            return {}
        records = {}
        counts = {(year, short): 0 for year in range(2, 7) for short in ("pj", "pk")}
        for entry in data["records"]:
            year, subject, number = entry["year"], entry["subject"], entry["pdp"]
            if type(year) is not int or type(number) is not int or subject not in ("PJ", "PK"):
                return {}
            short = subject.lower()
            if year not in MAXIMUM[short] or not 1 <= number <= MAXIMUM[short][year]:
                return {}
            if entry.get("status") != "DRAF_CADANGAN" or entry.get("ready") is not False:
                return {}
            sk, sp = entry.get("sk"), entry.get("sp")
            if (not isinstance(sk, list) or not isinstance(sp, list)
                    or not sk or not sp or
                    any(code.rsplit(".", 1)[0] not in sk for code in sp)):
                return {}
            key = (year, short, number)
            if key in records:
                return {}
            records[key] = {
                "path": _record_path(year, short, number),
                "title": entry["title"], "sk": sk, "sp": sp,
            }
            counts[(year, short)] += 1
        if any(counts[(year, short)] != MAXIMUM[short][year]
               for year in range(2, 7) for short in ("pj", "pk")):
            return {}
        return records
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


def _source(year, short_subject, number, *, root=ROOT):
    if type(number) is not int or number not in range(1, MAXIMUM.get(short_subject, {}).get(year, 0) + 1):
        return None
    root = Path(root).resolve()
    path = _record_path(year, short_subject, number)
    record = _manifest(str(root)).get((year, short_subject, number))
    if record is None or record["path"] != path:
        return None
    try:
        text = (root / path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    subject_name = "Jasmani" if short_subject == "pj" else "Kesihatan"
    if not text.startswith("# RPH Pendidikan %s Tahun %d — PdP %03d" % (
            subject_name, year, number)):
        return None
    labels = {}
    for line in text.splitlines():
        match = MARKDOWN_LABEL.fullmatch(line.strip())
        if match:
            labels[match[1].strip().casefold()] = match[2].strip()
    if "draf" not in labels.get("status", "").casefold():
        return None
    if "terhalang" in labels["status"].casefold():
        return None
    sk = CODE_SK.findall(labels.get("sk", ""))
    sp = CODE_SP.findall(labels.get("sp", ""))
    if (not sk or not sp or any(code.rsplit(".", 1)[0] not in sk for code in sp)
            or sk != record["sk"] or sp != record["sp"]):
        return None
    activities = [value for key, value in labels.items()
                  if key.startswith("aktiviti ") and re.match(r"aktiviti [12]\b", key)]
    objective = labels.get("objektif") or labels.get("objektif pembelajaran")
    required = (objective, labels.get("set induksi"), labels.get("penutup"),
                labels.get("pengukuhan/pbd") or labels.get("pengukuhan dan penilaian (pbd)")
                or labels.get("pentaksiran/pbd"), len(activities) >= 2)
    if not all(required):
        return None
    title = labels.get("tajuk") or labels.get("unit/tajuk")
    if not title or title != record["title"]:
        return None
    return {"year": year, "subject": short_subject, "lesson": number,
            "title": title, "sk": sk, "sp": sp, "fields": labels,
            "objective": objective, "activities": activities}


def list_lessons(year, subject, *, root=ROOT):
    y = _year(year)
    short = SUBJECTS.get(subject)
    if not y or not short:
        return []
    return [lesson for number in range(1, MAXIMUM[short][y] + 1)
            if (lesson := _source(y, short, number, root=root)) is not None]


def _selection(state, *, root=ROOT):
    if not isinstance(state, dict):
        return None
    subject = SUBJECTS.get(state.get("subject"))
    year = _year(state.get("year") or state.get("year_label"))
    selected = state.get("_pjpk_2027_preview_selection")
    if not (subject and year and isinstance(selected, dict)):
        return None
    number = selected.get("lesson")
    if type(number) is not int or selected.get("year") != year or selected.get("subject") != subject:
        return None
    if str(state.get("lesson_no") or "").strip() != str(number):
        return None
    lesson = _source(year, subject, number, root=root)
    if lesson is None:
        return None
    selected_sp = str(state.get("sp_code") or "").strip()
    if selected_sp and selected_sp not in lesson["sp"]:
        return None
    return lesson


def adapt_rows(state, rows, *, root=ROOT):
    source = _selection(state, root=root)
    if source is None or not isinstance(rows, dict):
        return rows
    labels = source["fields"]
    result = dict(rows)
    result.update({
        "MATA PELAJARAN": state["subject"],
        "TAHUN/TINGKATAN": "Tahun %d" % source["year"],
        "TAJUK": source["title"] + " [DRAF CADANGAN — SEMAK GURU]",
        "STANDARD KANDUNGAN": ", ".join(source["sk"]),
        "STANDARD PEMBELAJARAN": ", ".join(source["sp"]),
        "OBJEKTIF PEMBELAJARAN": source["objective"],
        "KRITERIA KEJAYAAN": source["objective"],
        "SET INDUKSI": labels["set induksi"],
        "AKTIVITI UTAMA": "\n\n".join(
            "Aktiviti %d\n%s" % (i, value)
            for i, value in enumerate(source["activities"], 1)),
        "PENTAKSIRAN": labels.get("pengukuhan/pbd")
            or labels.get("pengukuhan dan penilaian (pbd)")
            or labels.get("pentaksiran/pbd", ""),
        "PENUTUP": labels["penutup"],
        "BAHAN BANTU MENGAJAR": labels.get("bbm") or labels.get("bahan")
            or "Kad situasi, alat bantu mengajar selamat mengikut tajuk.",
        "EMK / NILAI": "Keselamatan, kerjasama dan bertanggungjawab.",
    })
    return result


def install(ns, *, enabled=None, root=ROOT):
    """Install on the requested runtime; do not mutate users, credits or databases."""
    if enabled is None:
        enabled = os.environ.get(FLAG) == "1"
    if not enabled or ns.get("CIKGULAJU_PJPK_2027_PREVIEW_INSTALLED"):
        return bool(ns.get("CIKGULAJU_PJPK_2027_PREVIEW_INSTALLED"))
    required = ("callback", "send", "_rph_rows", "_lesson_to_class_v2439")
    if any(not callable(ns.get(key)) for key in required):
        return False
    if not isinstance(ns.get("state"), dict) or not _manifest(str(Path(root).resolve())):
        return False

    previous_cb, previous_rows = ns["callback"], ns["_rph_rows"]
    send, state = ns["send"], ns["state"]

    def preview_menu(cid, page=0):
        st = state.setdefault(cid, {})
        year, subject = _year(st.get("year")), st.get("subject")
        lessons = list_lessons(year, subject, root=root)
        if not lessons:
            return send(cid, "RPH PJPK DRAF belum tersedia untuk pilihan ini.",
                        [[{"text": "⬅️ Tukar subjek", "callback_data": "choose_grade"}]])
        page = max(0, int(page))
        start = page * 10
        if start >= len(lessons):
            page, start = 0, 0
        keyboard = [[{"text": ("PdP %03d • %s" % (x["lesson"], x["title"]))[:62],
                      "callback_data": "pjpk27pick|%03d" % x["lesson"]}]
                    for x in lessons[start:start + 10]]
        navigation = []
        if page:
            navigation.append({"text": "⬅️", "callback_data": "pjpk27page|%d" % (page - 1)})
        if start + 10 < len(lessons):
            navigation.append({"text": "➡️", "callback_data": "pjpk27page|%d" % (page + 1)})
        if navigation:
            keyboard.append(navigation)
        keyboard.append([{"text": "⬅️ Tukar Subjek", "callback_data": "choose_grade"}])
        return send(cid, "📘 <b>RPH PJPK 2027 • Tahun %d</b>\n\n"
                    "Pilih PdP untuk menyediakan RPH melalui aliran kelas biasa. "
                    "Bahan masih DRAF CADANGAN dan perlu disemak guru." % year, keyboard)

    def callback(cid, data):
        value = str(data or "")
        st = state.setdefault(cid, {})
        if value in ("sub_Pendidikan Jasmani", "sub_Pendidikan Kesihatan"):
            st["subject"] = value[4:]
            st.pop("_pjpk_2027_preview_selection", None)
            if _year(st.get("year")):
                return preview_menu(cid)
            return previous_cb(cid, data)
        if value.startswith("pjpk27page|") or value.startswith("pjpk27pick|"):
            if not _year(st.get("year")) or st.get("subject") not in SUBJECTS:
                return send(cid, "Pilihan PdP tidak sah.")
            if value.startswith("pjpk27page|"):
                raw = value.partition("|")[2]
                return preview_menu(cid, int(raw)) if raw.isascii() and raw.isdecimal() else preview_menu(cid)
            raw = value.partition("|")[2]
            if not raw.isascii() or not re.fullmatch(r"\d{3}", raw):
                return preview_menu(cid)
            year, subject, number = _year(st["year"]), st["subject"], int(raw)
            lesson = _source(year, SUBJECTS[subject], number, root=root)
            if lesson is None:
                return preview_menu(cid)
            for key in ("selected_sk", "sk_code", "sk_text", "selected_sp",
                        "sp_code", "sp_text", "selected_sk_codes", "selected_sp_codes",
                        "grouped_sk_codes", "grouped_sp_codes", "grouped_sp_texts",
                        "_quick_selected_rpt_row_v2388", "quick_rpt_row",
                        "rpt_entry_id", "rpt_activity_note", "rpt_assessment_note",
                        "subtopic", "lesson", "lesson_no", "pdp_no", "topic", "unit"):
                st.pop(key, None)
            st.update({
                "task": "quick_material", "quick_material_flow": True,
                "assessment_mode": "formative", "rph_mode": "fast_rpt",
                "lesson": str(number), "lesson_no": str(number), "pdp_no": number,
                "topic": lesson["title"], "unit": lesson["title"],
                "unit_title": lesson["title"], "sk_code": lesson["sk"][0],
                "sp_code": lesson["sp"][0], "selected_sk": lesson["sk"][0],
                "selected_sp": lesson["sp"][0],
                "selected_sk_codes": list(lesson["sk"]),
                "grouped_sk_codes": list(lesson["sk"]),
                "selected_sp_codes": list(lesson["sp"]),
                "grouped_sp_codes": list(lesson["sp"]),
                "quick_content_v2391": lesson["title"],
                "_pjpk_2027_preview_selection": {
                    "year": year, "subject": SUBJECTS[subject], "lesson": number},
            })
            return ns["_lesson_to_class_v2439"](cid)
        return previous_cb(cid, data)

    def rows(state_value, *args, **kwargs):
        original = previous_rows(state_value, *args, **kwargs)
        try:
            return adapt_rows(state_value, original, root=root)
        except Exception as exc:
            print("PJPK draft RPH source fallback:", repr(exc), flush=True)
            return original

    ns["callback"] = callback
    ns["_rph_rows"] = rows
    ns["CIKGULAJU_PJPK_2027_PREVIEW_INSTALLED"] = True
    return True
