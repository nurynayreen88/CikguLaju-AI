"""Provisional PSV Year 2–6 Telegram RPH route.

Explicit owner-approved publication of existing *draft* lesson sources through the
native class/date/credit/Word/PDF workflow. This is NOT the FINAL READY release:
the stricter signed source-audit bridge remains unchanged and fail-closed.

Only callback navigation and the final _rph_rows renderer are wrapped. No DB,
payment, user account, subscription, or quota mutation is performed here.
Emergency off switch: CIKGULAJU_PSV_PROVISIONAL_ENABLED=0.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from web import psv_2027_rph_release_bridge as source

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = "Pendidikan Seni Visual"
FLAG = "CIKGULAJU_PSV_PROVISIONAL_ENABLED"
SESSION_KEY = "_psv2027_provisional_selection"
NUMBER = re.compile(r"^[0-9]{3}$")


def _year(value):
    return source._year(value)


def _lesson(year, number, *, root=ROOT):
    if type(year) is not int or type(number) is not int:
        return None
    return source.load_candidate(year, number, preview=True, root=root)


def _label(year, number, *, root=ROOT):
    rows = source._rpt(year, str(Path(root).resolve()))
    if rows is None or number not in range(1, 43):
        return ""
    row = rows[number - 1]
    if year == 6:
        unit = row.get("Tajuk unit", "")
        step = row.get("Tajuk/aktiviti PdP", "")
    else:
        unit = row.get("Tajuk karya cadangan", "")
        step = row.get("Fokus", "")
    return ("%s — %s" % (unit, step)).strip(" —")


def _selection(state, *, root=ROOT):
    if not isinstance(state, dict) or state.get("subject") != SUBJECT:
        return None
    year = _year(state.get("year") or state.get("year_label"))
    token = state.get(SESSION_KEY)
    raw = str(state.get("lesson_no") or "").strip()
    if (not year or not isinstance(token, dict) or
            not raw.isascii() or not raw.isdecimal()):
        return None
    number = int(raw)
    if (token.get("year") != year or token.get("number") != number or
            token.get("subject") != SUBJECT):
        return None
    lesson = _lesson(year, number, root=root)
    if not lesson:
        return None
    if str(state.get("sp_code") or "").strip() not in lesson["sp"].split("; "):
        return None
    if str(state.get("sk_code") or "").strip() not in lesson["sk"].split("; "):
        return None
    return lesson


def adapt_rows(state, rows, *, root=ROOT):
    """Overlay only an explicit validated PSV selection; preserve native metadata."""
    if not isinstance(rows, dict) or _selection(state, root=root) is None:
        return rows
    return source.adapt_rows(state, rows, preview=True, root=root)


def install(ns, *, enabled=None, root=ROOT):
    """Opt-out user-authorized route; keep the official release gate separate."""
    if enabled is None:
        enabled = os.environ.get(FLAG, "1") == "1"
    if not enabled:
        print("PSV_PROVISIONAL_RPH_ACTIVE=0; reason=feature_disabled", flush=True)
        return False
    if ns.get("PSV_2027_PROVISIONAL_TELEGRAM_ACTIVE"):
        return True
    required = ("callback", "subjects", "send", "_rph_rows", "_lesson_to_class_v2439")
    if not isinstance(ns, dict) or not isinstance(ns.get("state"), dict):
        print("PSV_PROVISIONAL_RPH_ACTIVE=0; reason=runtime_state_missing", flush=True)
        return False
    missing = [name for name in required if not callable(ns.get(name))]
    if missing:
        print("PSV_PROVISIONAL_RPH_ACTIVE=0; reason=runtime_hooks_missing; hooks=" +
              ",".join(missing), flush=True)
        return False
    root = Path(root).resolve()
    # Fail before patching any production callback if the 210 draft sources do
    # not parse or the RPT/source correspondence is incomplete.
    for year in range(2, 7):
        for number in range(1, 43):
            if _lesson(year, number, root=root) is None:
                print("PSV_PROVISIONAL_RPH_ACTIVE=0; reason=source_unavailable; "
                      "year=%d; pdp=%03d" % (year, number), flush=True)
                return False

    previous_cb, previous_rows = ns["callback"], ns["_rph_rows"]
    previous_subjects = ns["subjects"]
    send, session = ns["send"], ns["state"]

    def send_with_active_psv_subject(cid, text, kb=None, *args, **kwargs):
        """Correct the exact v26.17 subject notice on any surviving legacy route."""
        old = "Pilih subjek. 🚧 = Dalam Pembangunan; janaan belum dibuka."
        match = re.fullmatch(r"📘 <b>Tahun ([2-6])</b>\n\n" + re.escape(old),
                             str(text or ""))
        if match:
            # Always work on a copy: do not mutate a Telegram keyboard reused
            # by an unrelated handler. Leave other 🚧 subjects untouched.
            copied = [[dict(button) for button in row] for row in (kb or [])]
            found = False
            for row in copied:
                for button in row:
                    if button.get("callback_data") in (
                            "devsub2617_Pendidikan Seni Visual",
                            "sub_Pendidikan Seni Visual"):
                        button["text"] = "🎨 Pendidikan Seni Visual"
                        button["callback_data"] = "sub_Pendidikan Seni Visual"
                        found = True
            if not found:
                # Add just the PSV entry before legacy back/home navigation.
                copied.insert(max(0, len(copied) - 2), [
                    {"text": "🎨 Pendidikan Seni Visual",
                     "callback_data": "sub_Pendidikan Seni Visual"}])
            kb = copied
            text = ("📘 <b>Tahun " + match.group(1) + "</b>\n\n"
                    "Pilih subjek. 🎨 Pendidikan Seni Visual sudah tersedia "
                    "(42 PdP). 🚧 Hanya subjek lain yang berlabel "
                    "Dalam Pembangunan belum dibuka.")
        return send(cid, text, kb, *args, **kwargs)


    def subjects(cid, label):
        """Remove the old PSV development button for Years 2–6 only.

        Preserve every existing regular subject and all other development
        entries; secondary classes and Year1 remain with the original menu.
        """
        year = _year(label)
        if year is None:
            return previous_subjects(cid, label)
        catalog = ns.get("SUBJECTS_BY_GRADE")
        if not isinstance(catalog, dict):
            return previous_subjects(cid, label)
        session.setdefault(cid, {})["year"] = label
        regular = list(catalog.get(label, ()) or ())
        labels = ns.get("SUBJECT_LABEL") or {}
        development = ns.get("_CIKGULAJU_DEV_SUBJECTS_V2617") or {}
        buttons = []
        seen = set()
        for name in regular:
            if name in seen:
                continue
            seen.add(name)
            buttons.append({"text": labels.get(name, name),
                            "callback_data": "sub_" + name})
        if SUBJECT not in seen:
            # The old topic catalog lacks PSV even though 210 RPH now exist.
            buttons.append({"text": "🎨 Pendidikan Seni Visual",
                            "callback_data": "sub_" + SUBJECT})
            seen.add(SUBJECT)
        for name, years in development.items():
            if name != SUBJECT and year in years and name not in seen:
                buttons.append({"text": "🚧 " + name + " (Dalam Pembangunan)",
                                "callback_data": "devsub2617_" + name})
        kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        kb.extend([[{"text": "⬅️ Pilih Tahun/Tingkatan",
                    "callback_data": "choose_grade"}],
                   [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        return send(cid, "📘 <b>" + label +
                    "</b>\n\nPilih subjek. 🎨 PSV menyediakan 42 PdP setahun "
                    "bagi Tahun 2–6; 🚧 subjek lain masih dalam pembangunan.", kb)

    def menu(cid, page=0):
        st = session.setdefault(cid, {})
        year = _year(st.get("year"))
        if st.get("subject") != SUBJECT or not year:
            return previous_cb(cid, "choose_grade")
        page = max(0, min(5, page))
        first = page * 8 + 1
        if first > 42:
            page, first = 0, 1
        kb = []
        for n in range(first, min(first + 8, 43)):
            label = ("PdP %03d · %s" % (n, _label(year, n, root=root)))[:64]
            kb.append([{"text": label,
                        "callback_data": "psv27pick|%d|%03d" % (year, n)}])
        nav = []
        if page:
            nav.append({"text": "⬅️", "callback_data": "psv27page|%d|%d" % (year, page - 1)})
        if first + 8 <= 42:
            nav.append({"text": "➡️", "callback_data": "psv27page|%d|%d" % (year, page + 1)})
        if nav:
            kb.append(nav)
        kb.append([{"text": "⬅️ Tukar tahun/subjek",
                    "callback_data": "choose_grade"}])
        return send(cid,
                    "🎨 <b>RPH Pendidikan Seni Visual • Tahun %d</b>\n\n"
                    "Pilih PdP, kemudian pilih kelas, tarikh dan bahan PDF/Word "
                    "melalui aliran biasa CikguLaju." % year, kb)

    def callback(cid, data):
        value = str(data or "")
        st = session.setdefault(cid, {})
        if value in ("sub_Pendidikan Seni Visual",
                     "devsub2617_Pendidikan Seni Visual"):
            # Old keyboards still carry v26.17 development callback data.
            # Year 1 remains gated and other subjects are untouched.
            if _year(st.get("year")) is None:
                return previous_cb(cid, data)
            st["subject"] = SUBJECT
            st.pop(SESSION_KEY, None)
            return menu(cid)
        if value.startswith(("psv27page|", "psv27pick|")):
            fields = value.split("|")
            if len(fields) != 3 or not fields[1].isascii() or not fields[1].isdecimal():
                return send(cid, "Pilihan PSV tidak sah. Sila pilih semula tahun.")
            year = int(fields[1])
            if (_year(st.get("year")) != year or st.get("subject") != SUBJECT):
                return send(cid, "Pilihan PSV telah berubah. Pilih semula subjek dan PdP.")
            if value.startswith("psv27page|"):
                if not fields[2].isascii() or not fields[2].isdecimal():
                    return menu(cid)
                return menu(cid, int(fields[2]))
            if not NUMBER.fullmatch(fields[2]):
                return menu(cid)
            number = int(fields[2])
            plan = _lesson(year, number, root=root)
            if plan is None:
                return menu(cid)
            # Drop only stale curricular choices from a previous route.
            for key in (
                "selected_sk", "sk_code", "sk_text", "selected_sp", "sp_code",
                "sp_text", "selected_sk_codes", "selected_sp_codes",
                "grouped_sk_codes", "grouped_sp_codes", "grouped_sp_texts",
                "_quick_selected_rpt_row_v2388", "quick_rpt_row",
                "rpt_entry_id", "rpt_activity_note", "rpt_assessment_note",
                "lesson", "lesson_no", "pdp_no", "topic", "subtopic", "unit",
                "textbook_lesson_no", "quick_content_v2391",
            ):
                st.pop(key, None)
            sk = plan["sk"].split("; ")
            sp = plan["sp"].split("; ")
            st.update({
                "subject": SUBJECT,
                "task": "quick_material", "quick_material_flow": True,
                "assessment_mode": "formative", "rph_mode": "fast_rpt",
                "lesson_no": str(number), "lesson": str(number),
                "pdp_no": number, "topic": plan["title"],
                "unit": plan["title"], "unit_title": plan["title"],
                "sk_code": sk[0], "sp_code": sp[0],
                "selected_sk": sk[0], "selected_sp": sp[0],
                "selected_sk_codes": sk, "selected_sp_codes": sp,
                "grouped_sk_codes": sk, "grouped_sp_codes": sp,
                "quick_content_v2391": plan["title"],
                SESSION_KEY: {"year": year, "number": number,
                              "subject": SUBJECT},
            })
            return ns["_lesson_to_class_v2439"](cid)
        return previous_cb(cid, data)

    def rows(state, *args, **kwargs):
        base = previous_rows(state, *args, **kwargs)
        try:
            return adapt_rows(state, base, root=root)
        except Exception as exc:
            print("PSV provisional RPH fallback:", type(exc).__name__, flush=True)
            return base

    ns["subjects"] = subjects
    ns["callback"] = callback
    ns["_rph_rows"] = rows
    ns["send"] = send_with_active_psv_subject
    ns["PSV_2027_PROVISIONAL_TELEGRAM_ACTIVE"] = True
    print("PSV_PROVISIONAL_RPH_ACTIVE=1; curriculum_pdp=210; "
          "subject_menu_live=1; legacy_development_notice_guard=1", flush=True)
    return True
