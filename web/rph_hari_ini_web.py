"""CikguLaju Web RPH Hari Ini: read the shared Telegram timetable.

The schedule comes only from authenticated teacher_profiles.class_profiles.
Weekly suggestions come from the published Web RPT. Teachers still select
the exact Lesson/PdP in the existing native RPH flow.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from functools import lru_cache
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify, request
from itsdangerous import BadSignature

from web import native_telegram_sjkc_math_client as sjkc
from web import native_telegram_sjkt_math_client as sjkt
from web.primary_subject_choices import variants_by_name
from web.rph_today_progress import (
    attach_progress, class_key, lesson_signer, read_progress, read_progress_summary, save_completion,
)
from web.teacher_profile_routes import _auth, _body
from web.teacher_profile_store import (
    ProfileUnavailable, ProfileValidation, TIME, get_profile, get_schedule,
)
from web.unified_rph_web import SUBJECT_LABELS
from web.school_day_calendar import calendar_available, calendar_notice, is_weekend, school_closure
from web.school_days_2027 import FRI_SAT, WEEKDAY, normalize_state

bp = Blueprint("rph_hari_ini_web", __name__)
RPT_WEEKLY_CATALOG = Path(__file__).with_name("rpt_weekly_suggestions_2027.json")
INTEGRATED_ENGLISH_CATALOG = Path(__file__).with_name("english_integrated_rph_weeks_2027.json")
SUBJECTS = {
    "bahasa melayu": ("BM", None),
    "bm": ("BM", None),
    "bahasa malaysia": ("BM", None),
    "english": ("ENGLISH", None),
    "english (sk)": ("ENGLISH", None),
    "bahasa inggeris": ("ENGLISH", None),
    "bahasa inggeris (sk)": ("ENGLISH", None),
    "bi": ("ENGLISH", None),
    "matematik": ("MATH", None),
    "mathematics": ("MATH", None),
    "math": ("MATH", None),
    "maths": ("MATH", None),
    "sains": ("SCIENCE", None),
    "science": ("SCIENCE", None),
    "pendidikan islam": ("PI", None),
    "pi": ("PI", None),
    "pendidikan moral": ("MORAL", None),
    "moral": ("MORAL", None),
    "pendidikan seni visual": ("PSV", None),
    "psv": ("PSV", None),
    "pendidikan jasmani": ("PJPK", "PJ"),
    "pj": ("PJPK", "PJ"),
    "pendidikan kesihatan": ("PJPK", "PK"),
    "pk": ("PJPK", "PK"),
    "pjpk": ("PJPK", None),
    "pendidikan jasmani dan pendidikan kesihatan": ("PJPK", None),
    "bahasa arab": ("ARAB", None),
    "arab": ("ARAB", None),
    "pendidikan muzik": ("MUZIK", None),
    "muzik": ("MUZIK", None),
    "music": ("MUZIK", None),
    "sejarah": ("SEJARAH", None),
    "reka bentuk dan teknologi": ("RBT", None),
    "reka bentuk teknologi": ("RBT", None),
    "rbt": ("RBT", None),
}
NON_TEACHING = frozenset(("rehat", "perhimpunan", "perhimpunan rasmi",
                          "kokurikulum", "masa rehat"))


def subject_identity(value):
    if not isinstance(value, str):
        return None, None
    key = " ".join(value.casefold().strip().replace("&", " dan ").split())
    return SUBJECTS.get(key, (None, None))


def class_year(value):
    """Do not infer year from trailing numbers in class names or old RPTs."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    m = re.match(r"^(?:(?:tahun|t)\s*)?([1-6])(?=$|[\s/._-]|[A-Za-z])",
                 value, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def malaysia_today():
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()


@lru_cache(maxsize=1)
def weekly_catalog():
    return json.loads(RPT_WEEKLY_CATALOG.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def integrated_english_calendar():
    return json.loads(INTEGRATED_ENGLISH_CATALOG.read_text(encoding="utf-8"))


def integrated_pair(year, lesson):
    for row in integrated_english_calendar().get(str(year), {}).values():
        for session in row[4]:
            if len(session) == 2 and lesson in session:
                return session
    return None


def weekly_rpt_suggestion(state, target, subject, year):
    state = normalize_state(state)
    if target.year != 2027 or state is None:
        return None
    group_a = state in FRI_SAT
    if school_closure(state, target):
        return None
    try:
        from web.native_telegram_integrated_english_client import integrated_enabled
        if subject == "ENGLISH" and 2 <= year <= 6 and integrated_enabled():
            index = 0 if group_a else 2
            for week, row in integrated_english_calendar()[str(year)].items():
                if row[index] <= target.isoformat() <= row[index + 1]:
                    return {
                        "week": int(week), "group": "A" if group_a else "B",
                        "lessons": {"": [number for session in row[4] for number in session]},
                        "sessions": row[4], "dates": row[index:index + 2],
                    }
            return None
        weeks = weekly_catalog().get(f"{subject}:{year}", {})
    except (OSError, ValueError):
        return None
    offset = 0 if group_a else 2
    selected = target.isoformat()
    for week, row in weeks.items():
        if row[offset] <= selected <= row[offset + 1]:
            suggestion = {"week": int(week), "group": "A" if group_a else "B",
                          "lessons": row[4]}
            if subject == "MATH" and year in (5, 6) and len(row) == 6:
                suggestion["slot_minutes"] = row[5]
            return suggestion
    return None


def english_week_capacity(rows, state, class_name, year, suggestion):
    """Compare usable 60-minute sessions or legacy timetable minutes with the RPT."""
    offset = 0 if suggestion["group"] == "A" else 2
    span = suggestion.get("dates")
    if span is None:
        week = weekly_catalog()[f"ENGLISH:{year}"][str(suggestion["week"])]
        span = week[offset:offset + 2]
    start, end = map(date.fromisoformat, span)
    state = normalize_state(state)
    dates = (start + timedelta(days=step) for step in range((end - start).days + 1))
    school_days = {WEEKDAY[day.weekday()] for day in dates if not school_closure(state, day)}
    integrated = "sessions" in suggestion
    required = 60 * len(suggestion["sessions"] if integrated else suggestion["lessons"][""])
    session_days = set()
    scheduled = 0
    for row in rows:
        if not isinstance(row, dict) or row.get("day") not in school_days:
            continue
        name = row.get("class_name")
        if (not isinstance(name, str) or class_key(name) != class_key(class_name)
                or subject_identity(row.get("subject"))[0] != "ENGLISH"):
            continue
        begin, finish = row.get("start"), row.get("end")
        if (not isinstance(begin, str) or not isinstance(finish, str)
                or not TIME.fullmatch(begin) or not TIME.fullmatch(finish)
                or begin >= finish):
            return None
        hours, minutes = map(int, finish.split(":"))
        start_hours, start_minutes = map(int, begin.split(":"))
        duration = (hours - start_hours) * 60 + minutes - start_minutes
        if integrated:
            if duration == 60:
                session_days.add(row["day"])
        else:
            scheduled += duration
    if integrated:
        scheduled = 60 * len(session_days)
    return {"scheduled_minutes": scheduled, "required_minutes": required}


def day_payload(profile, schedule, target, *, today=None, sjkc_catalogue=None, sjkt_catalogue=None):
    """Pure computation. Never modifies the stored timetable."""
    if not isinstance(profile, dict) or not isinstance(schedule, dict):
        raise ProfileValidation("Maklumat jadual tidak sah")
    rows = schedule.get("entries")
    if not isinstance(rows, list) or len(rows) > 80:
        raise ProfileValidation("Rekod jadual tidak sah")
    today = today or malaysia_today()
    if not isinstance(target, date) or abs((target-today).days) > 400:
        raise ProfileValidation("Tarikh mesti dalam lingkungan 400 hari")
    day = WEEKDAY[target.weekday()]
    state = profile.get("state_name") or ""
    school_state = normalize_state(state)
    weekend = is_weekend(school_state, target)
    closure = school_closure(school_state, target)
    selected = []
    school_ready = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("day") != day:
            continue
        cls, subject = row.get("class_name"), row.get("subject")
        start, end = row.get("start"), row.get("end")
        if (not isinstance(cls, str) or not 0 < len(cls) <= 40
                or not isinstance(subject, str) or not 0 < len(subject) <= 60
                or not isinstance(start, str) or not isinstance(end, str)
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start)
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", end)
                or start >= end):
            raise ProfileValidation("Maklumat waktu dalam jadual tidak sah")
        year = class_year(cls)
        code, component = subject_identity(subject)
        subject_key = " ".join(subject.casefold().split())
        variant = variants_by_name().get(subject_key)
        school = None
        if not closure and variant:
            variant_key = variant["code"]
            match = {
                "matematik_sjkc": (sjkc, sjkc_catalogue),
                "matematik_sjkt": (sjkt, sjkt_catalogue),
            }.get(variant_key)
            if match and year in match[0].YEARS and match[1] is not None:
                school_key = variant_key, year
                if school_key not in school_ready:
                    school_ready[school_key] = match[1](year)
                if school_ready[school_key]:
                    school = variant["curriculum"]
                    code = match[0].SUBJECT
        valid = bool(year and code)
        reason = ("" if valid else
                  "Tahun kelas belum jelas; semak nama kelas di Profil Guru."
                  if year is None else
                  "Subjek belum dapat dipadankan; semak nama subjek di Profil Guru.")
        can_prepare = valid and not closure
        suggestion = weekly_rpt_suggestion(school_state, target, code, year) if can_prepare else None
        entry = {"day":day,"start":start,"end":end,
                 "class_name":cls,"subject":subject,
                 "year":year,"subject_code":code,"component":component,
                 "can_prepare":can_prepare,"reason":closure or reason,"rpt_suggestion":suggestion}
        if school:
            entry["curriculum"] = school
        elif variant and year and not closure:
            entry["reason"] = "RPH untuk subjek dan tahun ini dalam penyediaan."
            if variant["curriculum"] == "dlp" and year in variant.get("rpt_years", ()):
                entry["rpt_subject"] = variant["code"]
            if year in variant.get("preview_years", ()):
                entry["reason"] = "Pratonton RPH tersedia untuk semakan guru."
                entry["rph_preview"] = variant["rph_code"]
        elif subject_key in NON_TEACHING and not closure:
            entry["reason"] = "Waktu tanpa PdP."
        if code == "ENGLISH" and suggestion:
            entry["rpt_capacity"] = english_week_capacity(rows, state, cls, year, suggestion)
        selected.append(entry)
    selected.sort(key=lambda x:(x["start"],x["end"],x["class_name"].casefold()))
    return {
        "date":target.isoformat(),"day":day,"state":state,
        "entries":selected,"count":len(selected),"weekend":weekend,
        "closure":closure,
        "holiday_verified":calendar_available(school_state, target.year),
        "holiday_notice":calendar_notice(school_state, (target,)),
        "lesson_note":"Cadangan minggu merujuk RPT 2027. Pilih Lesson/PdP daripada katalog mengikut kemajuan kelas.",
    }


def school_week_start(target, group):
    offset = (target.weekday() + 1) % 7 if group == "A" else target.weekday()
    return target - timedelta(days=offset)


def week_choices(today, group):
    """Calendar ranges using the same boundaries as the saved school timetable."""
    first = today - timedelta(days=400)
    last = today + timedelta(days=400)
    start = school_week_start(first, group)
    current = school_week_start(today, group)
    choices = []
    while start <= last:
        choices.append({
            "start": start.isoformat(), "end": (start + timedelta(days=6)).isoformat(),
            "value": max(first, start).isoformat(), "current": start == current,
        })
        start += timedelta(days=7)
    return choices


def week_payload(profile, schedule, target, *, today, sjkc_catalogue=None, sjkt_catalogue=None):
    """Read the repeating timetable once and expand it in school-week order."""
    if not isinstance(profile, dict) or not isinstance(schedule, dict):
        raise ProfileValidation("Maklumat jadual tidak sah")
    if not isinstance(target, date) or abs((target - today).days) > 400:
        raise ProfileValidation("Tarikh mesti dalam lingkungan 400 hari")
    state = normalize_state(profile.get("state_name"))
    group = "A" if state in FRI_SAT else "B" if state else None
    start = school_week_start(target, group)
    dates = [start + timedelta(days=step) for step in range(7)]
    days = []
    if sjkc_catalogue is not None:
        sjkc_catalogue = lru_cache(maxsize=1)(sjkc_catalogue)
    if sjkt_catalogue is not None:
        sjkt_catalogue = lru_cache(maxsize=1)(sjkt_catalogue)
    for selected in dates:
        closure = school_closure(state, selected)
        day = {"date": selected.isoformat(), "day": WEEKDAY[selected.weekday()],
               "closure": closure, "entries": []}
        if not closure:
            slots = day_payload(profile, schedule, selected, today=target,
                                sjkc_catalogue=sjkc_catalogue, sjkt_catalogue=sjkt_catalogue)["entries"]
            day["entries"] = [slot for slot in slots
                              if " ".join(slot["subject"].casefold().split()) not in NON_TEACHING]
        days.append(day)
    return {"date": target.isoformat(), "start": days[0]["date"], "end": days[-1]["date"],
            "group": group, "days": days, "count": sum(len(day["entries"]) for day in days),
            "holiday_notice": calendar_notice(state, dates)}


def assign_week_suggestions(days):
    """Assign only a complete, unambiguous RPT sequence to a class timetable."""
    groups = {}
    for day in days:
        for slot in day["entries"]:
            if not slot["can_prepare"]:
                continue
            key = class_key(slot["class_name"]), slot["subject_code"], slot["component"] or ""
            groups.setdefault(key, []).append((day["date"], slot))
    for (_, code, component), entries in groups.items():
        first = entries[0][1]
        suggestion = first.get("rpt_suggestion")
        # A generic PJPK period still needs the teacher to choose PJ or PK.
        if not suggestion or (code == "PJPK" and not component):
            continue
        if any(slot.get("rpt_suggestion") != suggestion or "progress" not in slot for _, slot in entries):
            continue
        sessions = suggestion.get("sessions")
        if sessions:
            if (len({day for day, _ in entries}) != len(entries)
                    or any(datetime.strptime(slot["end"], "%H:%M")
                           - datetime.strptime(slot["start"], "%H:%M")
                           != timedelta(hours=1) for _, slot in entries)):
                continue
        else:
            sessions = [[number] for number in suggestion["lessons"].get(component, [])]
        slot_minutes = suggestion.get("slot_minutes")
        if slot_minutes is not None:
            actual_minutes = [
                (datetime.strptime(slot["end"], "%H:%M")
                 - datetime.strptime(slot["start"], "%H:%M")) // timedelta(minutes=1)
                for _, slot in entries
            ]
            if actual_minutes != slot_minutes:
                continue
        if len(sessions) != len(entries) or len({n for row in sessions for n in row}) != sum(map(len, sessions)):
            continue
        # A class that is ahead or behind its RPT needs an explicit choice.
        compatible = True
        for index, ((_, slot), numbers) in enumerate(zip(entries, sessions, strict=True)):
            record = slot["progress"].get(component, {})
            completed = record.get("completed")
            previous = record.get("previous")
            if completed is not None and completed != numbers[-1]:
                compatible = False
            if previous is not None:
                expected = sessions[index - 1][-1] if index else numbers[0] - 1
                already_completed = {row[-1] for row in sessions[:index]}
                if previous != expected and previous not in already_completed:
                    compatible = False
        if compatible:
            for (_, slot), numbers in zip(entries, sessions, strict=True):
                slot["suggested_session"] = numbers


def attach_week_suggestions(result, config, uid, *, known_date=None, known_progress=None):
    def add_progress(day):
        try:
            rows = known_progress if day["date"] == known_date else read_progress(config, uid, day["date"])
            attach_progress(day, rows)
            return True
        except ProfileUnavailable:
            return False

    eligible = [day for day in result["days"] if any(slot["can_prepare"] for slot in day["entries"])]
    if eligible:
        with ThreadPoolExecutor(max_workers=5) as workers:
            result["progress_unavailable"] = not all(list(workers.map(add_progress, eligible)))
    assign_week_suggestions(result["days"])


def copy_day_suggestions(result, week):
    matching_day = next(day for day in week["days"] if day["date"] == result["date"])
    fields = ("start", "end", "class_name", "subject")
    suggestions = {tuple(slot[field] for field in fields): slot["suggested_session"]
                   for slot in matching_day["entries"] if "suggested_session" in slot}
    for slot in result["entries"]:
        assigned = suggestions.get(tuple(slot[field] for field in fields))
        if assigned:
            slot["suggested_session"] = assigned


@bp.after_request
def private(resp):
    resp.headers["Cache-Control"] = "no-store, private"
    resp.headers["Vary"] = "Cookie"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@bp.get("/api/web/rph/hari-ini")
def hari_ini():
    config, uid, error = _auth()
    if error is not None:
        return error
    if not set(request.args).issubset({"date"}) or any(
            len(request.args.getlist(k)) != 1 for k in request.args):
        return jsonify({"error":"Parameter tarikh tidak sah"}),400
    raw = request.args.get("date")
    today = malaysia_today()
    if raw is None:
        target = today
    else:
        try:
            if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", raw):
                raise ValueError("Invalid ISO date")
            target = date.fromisoformat(raw)
        except (ValueError, TypeError):
            return jsonify({"error":"Format tarikh mestilah DD/MM/YYYY melalui pemilih tarikh"}),400
    try:
        profile = get_profile(config["supabase_url"],config["supabase_key"],uid)
        schedule = get_schedule(config["supabase_url"],config["supabase_key"],uid)
        result = day_payload(profile, schedule, target, today=today, sjkc_catalogue=sjkc.available,
                             sjkt_catalogue=sjkt.available)
    except ProfileValidation as exc:
        return jsonify({"error":str(exc)}),400
    except ProfileUnavailable:
        return jsonify({"error":"Jadual guru belum dapat dibaca. Data lama tidak diubah."}),503
    result["progress_editable"] = target <= today
    if any(slot["can_prepare"] for slot in result["entries"]):
        try:
            progress = read_progress(config, uid, result["date"])
            attach_progress(result, progress)
        except ProfileUnavailable:
            result["progress_unavailable"] = True
        else:
            if any(slot["rpt_suggestion"] for slot in result["entries"]):
                try:
                    week = week_payload(profile, schedule, target, today=today)
                except ProfileValidation:
                    # An invalid entry on another day must not hide this day's timetable.
                    week = None
                if week is not None:
                    attach_week_suggestions(week, config, uid, known_date=result["date"], known_progress=progress)
                    copy_day_suggestions(result, week)
    return jsonify(result)


@bp.get("/api/web/rph/minggu-ini")
def minggu_ini():
    config, uid, error = _auth()
    if error is not None:
        return error
    if set(request.args) - {"date"} or len(request.args.getlist("date")) > 1:
        return jsonify({"error": "Parameter tarikh tidak sah"}), 400
    today = malaysia_today()
    try:
        raw = request.args.get("date", today.isoformat())
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", raw):
            raise ValueError("Invalid ISO date")
        target = date.fromisoformat(raw)
    except ValueError:
        return jsonify({"error": "Format tarikh tidak sah"}), 400
    try:
        profile = get_profile(config["supabase_url"], config["supabase_key"], uid)
        schedule = get_schedule(config["supabase_url"], config["supabase_key"], uid)
        result = week_payload(profile, schedule, target, today=today, sjkc_catalogue=sjkc.available,
                             sjkt_catalogue=sjkt.available)
    except ProfileValidation as exc:
        return jsonify({"error": str(exc)}), 400
    except ProfileUnavailable:
        return jsonify({"error": "Jadual guru belum dapat dibaca."}), 503

    result["weeks"] = week_choices(today, result["group"])
    attach_week_suggestions(result, config, uid)
    return jsonify(result)



@bp.get("/api/web/rph/hari-ini/progress")
def progress_summary():
    config, uid, error = _auth()
    if error is not None:
        return error
    if request.args:
        return jsonify({"error": "Parameter tidak dijangka"}), 400
    today = malaysia_today()
    try:
        schedule = get_schedule(config["supabase_url"], config["supabase_key"], uid)
        summaries = read_progress_summary(config, uid, today)
    except (ProfileValidation, ProfileUnavailable):
        return jsonify({"error": "Kemajuan PdP belum dapat disemak."}), 503

    class_names = {}
    scopes = set(summaries)
    for slot in schedule["entries"]:
        name = slot.get("class_name")
        code, component = subject_identity(slot.get("subject"))
        if not class_year(name) or not code:
            continue
        key = class_key(name)
        class_names.setdefault(key, name)
        if code == "PJPK" and component is None:
            scopes.update(((key, code, "PJ"), (key, code, "PK")))
        else:
            scopes.add((key, code, component or ""))

    entries = []
    component_labels = {"PJ": "Pendidikan Jasmani", "PK": "Pendidikan Kesihatan"}
    for key, code, component in sorted(scopes):
        entries.append({
            "class_name": class_names.get(key, key),
            "subject": component_labels.get(component) or SUBJECT_LABELS[code],
            "label": "Lesson" if code == "ENGLISH" else "PdP",
            **summaries.get((key, code, component), {"completed": 0}),
        })
    return jsonify({"year": today.year, "entries": entries})

@bp.post("/api/web/rph/hari-ini/completion")
def complete_pdp():
    config, uid, error = _auth()
    if error is not None:
        return error
    try:
        body = _body(limit=2048)
        if set(body) != {"date", "start", "class_name", "subject_code", "component", "token"}:
            raise ProfileValidation("Pilihan PdP tidak sah")
        target = date.fromisoformat(body["date"])
        today = malaysia_today()
        if target.isoformat() != body["date"] or target > today:
            raise ProfileValidation("Rekod PdP hanya boleh disimpan pada tarikh PdP atau selepasnya")
        component, token = body["component"], body["token"]
        if component not in ("", "PJ", "PK") or (token is not None and not isinstance(token, str)):
            raise ProfileValidation("Pilihan PdP tidak sah")
        profile = get_profile(config["supabase_url"], config["supabase_key"], uid)
        schedule = get_schedule(config["supabase_url"], config["supabase_key"], uid)
        result = day_payload(profile, schedule, target, today=today, sjkc_catalogue=sjkc.available,
                             sjkt_catalogue=sjkt.available)
        slot = next((entry for entry in result["entries"] if entry["can_prepare"]
                     and all(entry[key] == body[key] for key in ("start", "class_name", "subject_code"))), None)
        if (slot is None or (slot["subject_code"] == "PJPK") != bool(component)
                or (slot["component"] and slot["component"] != component)):
            raise ProfileValidation("Slot ini tiada dalam jadual. Muat semula jadual waktu.")
        number = None
        if token is not None:
            record = lesson_signer(config).loads(token, max_age=28800)
            if (not isinstance(record, list) or len(record) != 5
                    or record[:4] != [uid, slot["year"], slot["subject_code"], component]
                    or type(record[4]) is not int or not 1 <= record[4] <= 999):
                raise ProfileValidation("Lesson/PdP ini tidak sepadan dengan slot jadual")
            number = record[4]
            if (slot["subject_code"] == "ENGLISH" and target.year == 2027
                    and 2 <= slot["year"] <= 6):
                from web.native_telegram_integrated_english_client import integrated_enabled
                from datetime import time
                if integrated_enabled() and (
                    datetime.combine(target, time.fromisoformat(slot["end"]))
                    - datetime.combine(target, time.fromisoformat(slot["start"]))
                ) == timedelta(hours=1):
                    pair = integrated_pair(slot["year"], number)
                    if pair is not None:
                        number = pair[-1]
        save_completion(config, uid, result["date"], slot, component, number)
        attach_progress(result, read_progress(config, uid, result["date"]))
    except ProfileValidation as exc:
        return jsonify({"error": str(exc)}), 400
    except BadSignature:
        return jsonify({"error": "Pilihan Lesson/PdP telah luput. Muat semula jadual waktu."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Pilihan PdP tidak sah"}), 400
    except ProfileUnavailable:
        return jsonify({"error": "Rekod PdP belum dapat disahkan. Muat semula untuk menyemaknya."}), 503
    return jsonify({"entries": result["entries"]})
