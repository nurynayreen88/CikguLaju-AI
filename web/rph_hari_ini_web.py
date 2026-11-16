"""CikguLaju Web RPH Hari Ini: read the shared Telegram timetable.

The schedule comes only from authenticated teacher_profiles.class_profiles.
Weekly suggestions come from the published Web RPT. Teachers still select
the exact Lesson/PdP in the existing native RPH flow.
"""
from datetime import date, datetime, timedelta
from functools import lru_cache
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify, request
from itsdangerous import BadSignature

from web.rph_today_progress import (
    attach_progress, class_key, lesson_signer, read_progress, read_progress_summary, save_completion,
)
from web.teacher_profile_routes import _auth, _body
from web.teacher_profile_store import (
    ProfileUnavailable, ProfileValidation, TIME, get_profile, get_schedule,
)
from web.unified_rph_web import SUBJECT_LABELS
from web.school_days_2027 import FRI_SAT, WEEKDAY, is_school_day, normalize_state

bp = Blueprint("rph_hari_ini_web", __name__)
RPT_WEEKLY_CATALOG = Path(__file__).with_name("rpt_weekly_suggestions_2027.json")
INTEGRATED_ENGLISH_CATALOG = Path(__file__).with_name("english_integrated_rph_weeks_2027.json")
SUBJECTS = {
    "bahasa melayu": ("BM", None),
    "bm": ("BM", None),
    "bahasa malaysia": ("BM", None),
    "english": ("ENGLISH", None),
    "bahasa inggeris": ("ENGLISH", None),
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
    if not is_school_day(state, target):
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
            return {"week": int(week), "group": "A" if group_a else "B",
                    "lessons": row[4]}
    return None


def english_week_capacity(rows, state, class_name, year, suggestion):
    """Compare the saved class timetable with this week's 60-minute SOW Lessons."""
    offset = 0 if suggestion["group"] == "A" else 2
    span = suggestion.get("dates")
    if span is None:
        week = weekly_catalog()[f"ENGLISH:{year}"][str(suggestion["week"])]
        span = week[offset:offset + 2]
    start, end = map(date.fromisoformat, span)
    state = normalize_state(state)
    dates = (start + timedelta(days=step) for step in range((end - start).days + 1))
    school_days = {WEEKDAY[day.weekday()] for day in dates if is_school_day(state, day)}
    required = 60 * len(suggestion.get("sessions", suggestion["lessons"][""]))
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
        scheduled += (hours - start_hours) * 60 + minutes - start_minutes
    return {"scheduled_minutes": scheduled, "required_minutes": required}


def day_payload(profile, schedule, target, *, today=None):
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
    weekend = target.weekday() in ((4, 5) if str(state).strip().title() in FRI_SAT else (5, 6))
    selected = []
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
        valid = bool(year and code)
        reason = ("" if valid else
                  "Tahun kelas belum jelas; semak nama kelas di Profil Guru."
                  if year is None else
                  "Subjek belum dapat dipadankan; semak nama subjek di Profil Guru.")
        suggestion = weekly_rpt_suggestion(state, target, code, year) if valid and not weekend else None
        entry = {"day":day,"start":start,"end":end,
                 "class_name":cls,"subject":subject,
                 "year":year,"subject_code":code,"component":component,
                 "can_prepare":valid,"reason":reason,"rpt_suggestion":suggestion}
        if code == "ENGLISH" and suggestion:
            entry["rpt_capacity"] = english_week_capacity(rows, state, cls, year, suggestion)
        selected.append(entry)
    selected.sort(key=lambda x:(x["start"],x["end"],x["class_name"].casefold()))
    return {
        "date":target.isoformat(),"day":day,"state":state,
        "entries":selected,"count":len(selected),"weekend":weekend,
        "holiday_verified":False,
        "holiday_notice":(
            "Jadual ini menunjukkan hari hujung minggu negeri; "
            "sahkan PdP sebenar sebelum menyediakan RPH." if weekend else
            "Semakan cuti sekolah, cuti umum dan cuti tambahan belum automatik. "
            "Sahkan hari persekolahan sebelum menyediakan RPH."
        ),
        "lesson_note":"Cadangan minggu merujuk RPT 2027. Pilih Lesson/PdP daripada katalog mengikut kemajuan kelas.",
    }


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
        result = day_payload(profile,schedule,target,today=today)
    except ProfileValidation as exc:
        return jsonify({"error":str(exc)}),400
    except ProfileUnavailable:
        return jsonify({"error":"Jadual guru belum dapat dibaca. Data lama tidak diubah."}),503
    result["progress_editable"] = target <= today
    if any(slot["can_prepare"] for slot in result["entries"]):
        try:
            attach_progress(result, read_progress(config, uid, result["date"]))
        except ProfileUnavailable:
            result["progress_unavailable"] = True
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
        result = day_payload(profile, schedule, target, today=today)
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
