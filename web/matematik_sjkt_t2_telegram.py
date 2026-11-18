"""Keep normal and timetable RPH selection on the approved SJKT source."""

from datetime import datetime
import re
from zoneinfo import ZoneInfo

from curriculum_version_selector import LEGACY
from web import matematik_sjkt_t2_release as source
from web.matematik_sjkc_t3_telegram import install_school_math
from web.school_day_calendar import school_closure
from web.school_days_2027 import normalize_state

SLOT = "_sjkt2_today_slot"
CHOICES = "_sjkt2_today_choices"
SLOT_PREFIX = "msjkt2slot:"


def _today():
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()


def _is_sjkt(entry):
    name = " ".join(str(entry.get("subject") or "").casefold().split())
    return name in ("matematik sjkt", "matematik (sjkt)")


def _class_record(runtime, cid, entry):
    name = entry.get("class_name") or ""
    record = runtime._profile_class_record(cid, name) or {}
    year = record.get("year_label") or record.get("year")
    year_two = re.match(r"^(?:(?:tahun|year|t)\s*)?2(?=$|[\s/._-]|[A-Za-z])",
                        str(year or name).strip(), re.I)
    return name, record, bool(year_two)


def _slots(runtime, cid, target):
    profile = runtime._teacher_profile(cid) or {}
    school_state = normalize_state(profile.get("state_name"))
    if school_closure(school_state, target):
        return {}
    _, rows = runtime._today_rows_v25272(cid)
    eligible = {}
    for index, entry in rows:
        if not _is_sjkt(entry):
            continue
        name, record, year = _class_record(runtime, cid, entry)
        start, end = (str(entry.get(key) or "") for key in ("start", "end"))
        if (not name or not year or start >= end
                or not all(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time) for time in (start, end))):
            continue
        count = entry.get("students")
        if count in (None, ""):
            count = record.get("students")
        eligible[index] = {
            "class": name, "date": target.isoformat(), "time": f"{start} - {end}",
            "students": str(count) if count not in (None, "") else "",
        }
    return eligible


def _valid_slot(runtime, cid):
    index, selected = runtime.state[cid][SLOT]
    return _slots(runtime, cid, _today()).get(index) == selected


def _pick_materials(runtime, cid):
    if not _valid_slot(runtime, cid):
        return runtime.send(cid, "Slot telah berubah. Pilih semula melalui RPH Hari Ini.")
    state = runtime.state[cid]
    _, details = state[SLOT]
    state.update(rph_class=details["class"], rph_date=details["date"],
                 rph_time=details["time"], rph_students=details["students"])
    state.pop("rph_teacher_reflection", None)
    state.pop("_materials_selected_v2528", None)
    return runtime._material_picker_v2528(cid, "Butiran diambil daripada jadual waktu. Pilih Word atau PDF.")


def install(runtime):
    if getattr(runtime, "MATEMATIK_SJKT_T2_RPH_ACTIVE", False):
        return True
    if not install_school_math(runtime, source, "sjkt2", "MATEMATIK_SJKT_T2_RPH_ACTIVE",
                               slot_picker=_pick_materials, slot_valid=_valid_slot):
        return False
    previous = runtime.callback
    previous_daily = runtime._daily_candidate_v25292

    def daily_candidate(cid, entry):
        if _is_sjkt(entry):
            return None, "Pilih slot Matematik SJKT untuk menetapkan PdP."
        return previous_daily(cid, entry)

    def callback(cid, data):
        if data == "todayrph272":
            state = runtime.state.setdefault(cid, {})
            state.pop(SLOT, None)
            result = previous(cid, data)
            choices = _slots(runtime, cid, _today())
            state[CHOICES] = choices
            if choices:
                return runtime.send(cid, "<b>Matematik SJKT Tahun 2 · RPH Hari Ini</b>\nPilih slot.", [
                    [{"text": f"{row['time']} · {row['class']}", "callback_data": f"{SLOT_PREFIX}{index}"}]
                    for index, row in choices.items()
                ])
            return result
        if not isinstance(data, str) or not data.startswith(SLOT_PREFIX):
            return previous(cid, data)
        state = runtime.state.setdefault(cid, {})
        raw = data.removeprefix(SLOT_PREFIX)
        if not re.fullmatch(r"[0-9]{1,3}", raw):
            return runtime.send(cid, "Slot jadual tidak sah.")
        choice = int(raw)
        details = state.get(CHOICES, {}).get(choice)
        if not details or _slots(runtime, cid, _today()).get(choice) != details:
            return runtime.send(cid, "Slot telah berubah. Pilih semula melalui RPH Hari Ini.")
        state[SLOT] = choice, details
        state.update(task="rph", year=f"Tahun {source.YEAR}", curriculum_version=LEGACY)
        state.pop("waiting", None)
        return runtime._sjkt2_open_units(cid, state)

    runtime._daily_candidate_v25292 = daily_candidate
    runtime.callback = callback
    return True
