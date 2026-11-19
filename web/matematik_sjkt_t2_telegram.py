"""Use the approved school Mathematics source for regular RPH and timetable slots."""

from datetime import datetime
import re
from zoneinfo import ZoneInfo

from curriculum_version_selector import LEGACY
from web import matematik_sjkt_t2_release as source
from web.matematik_sjkc_t3_telegram import install_school_math
from web.school_day_calendar import school_closure
from web.school_days_2027 import normalize_state



def _today():
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()


def _class_record(runtime, cid, entry):
    name = entry.get("class_name") or ""
    record = runtime._profile_class_record(cid, name) or {}
    year = record.get("year_label") or record.get("year")
    year_two = re.match(r"^(?:(?:tahun|year|t)\s*)?2(?=$|[\s/._-]|[A-Za-z])",
                        str(year or name).strip(), re.I)
    return name, record, bool(year_two)


def _matches_school_subject(entry, school_type):
    name = " ".join(str(entry.get("subject") or "").casefold().split())
    label = school_type.casefold()
    return name in (f"matematik {label}", f"matematik ({label})")


def _is_sjkt(entry):
    return _matches_school_subject(entry, "SJKT")


def _slots(runtime, cid, target, matches_subject=_is_sjkt):
    profile = runtime._teacher_profile(cid) or {}
    school_state = normalize_state(profile.get("state_name"))
    if school_closure(school_state, target):
        return {}
    _, rows = runtime._today_rows_v25272(cid)
    eligible = {}
    for index, entry in rows:
        if not matches_subject(entry):
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


def install(runtime):
    return install_year_two(runtime, source, "sjkt2", "MATEMATIK_SJKT_T2_RPH_ACTIVE")


def install_year_two(runtime, source, key, active_attr):
    if getattr(runtime, active_attr, False):
        return True
    slot_key = f"_{key}_today_slot"
    choices_key = f"_{key}_today_choices"
    slot_prefix = f"m{key}slot:"
    open_units = f"_{key}_open_units"
    school_type = source.SUBJECT.rsplit(" ", 1)[-1]

    def matches_subject(entry):
        return _matches_school_subject(entry, school_type)

    def valid_slot(runtime, cid):
        index, selected = runtime.state[cid][slot_key]
        return _slots(runtime, cid, _today(), matches_subject).get(index) == selected

    def pick_materials(runtime, cid):
        if not valid_slot(runtime, cid):
            return runtime.send(cid, "Slot telah berubah. Pilih semula melalui RPH Hari Ini.")
        state = runtime.state[cid]
        _, details = state[slot_key]
        state.update(rph_class=details["class"], rph_date=details["date"],
                     rph_time=details["time"], rph_students=details["students"])
        state.pop("rph_teacher_reflection", None)
        state.pop("_materials_selected_v2528", None)
        return runtime._material_picker_v2528(cid, "Butiran diambil daripada jadual waktu. Pilih Word atau PDF.")

    if not install_school_math(runtime, source, key, active_attr,
                               slot_picker=pick_materials, slot_valid=valid_slot):
        return False
    previous = runtime.callback
    previous_daily = runtime._daily_candidate_v25292

    def daily_candidate(cid, entry):
        if matches_subject(entry) and _class_record(runtime, cid, entry)[2]:
            return None, f"Pilih slot {source.SUBJECT} untuk menetapkan PdP."
        return previous_daily(cid, entry)

    def callback(cid, data):
        if data == "todayrph272":
            state = runtime.state.setdefault(cid, {})
            state.pop(slot_key, None)
            result = previous(cid, data)
            choices = _slots(runtime, cid, _today(), matches_subject)
            state[choices_key] = choices
            if choices:
                return runtime.send(cid, f"<b>{source.SUBJECT} Tahun 2 · RPH Hari Ini</b>\nPilih slot.", [
                    [{"text": f"{row['time']} · {row['class']}", "callback_data": f"{slot_prefix}{index}"}]
                    for index, row in choices.items()
                ])
            return result
        if not isinstance(data, str) or not data.startswith(slot_prefix):
            return previous(cid, data)
        state = runtime.state.setdefault(cid, {})
        raw = data.removeprefix(slot_prefix)
        if not re.fullmatch(r"[0-9]{1,3}", raw):
            return runtime.send(cid, "Slot jadual tidak sah.")
        choice = int(raw)
        details = state.get(choices_key, {}).get(choice)
        if not details or _slots(runtime, cid, _today(), matches_subject).get(choice) != details:
            return runtime.send(cid, "Slot telah berubah. Pilih semula melalui RPH Hari Ini.")
        state[slot_key] = choice, details
        state.update(task="rph", year=f"Tahun {source.YEAR}", curriculum_version=LEGACY)
        state.pop("waiting", None)
        return getattr(runtime, open_units)(cid, state)

    runtime._daily_candidate_v25292 = daily_candidate
    runtime.callback = callback
    return True
