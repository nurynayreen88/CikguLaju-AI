"""CikguLaju Web RPH Hari Ini: read the shared Telegram timetable.

The schedule comes only from authenticated teacher_profiles.class_profiles.
No new database, RPH templates, guessed RPT offsets, credits or auto-generation.
The user confirms the exact Lesson/PdP in the existing native RPH flow.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import re
from flask import Blueprint, jsonify, request

from web.teacher_profile_routes import _auth
from web.teacher_profile_store import (
    ProfileUnavailable, ProfileValidation, get_profile, get_schedule,
)

bp = Blueprint("rph_hari_ini_web", __name__)
WEEKDAY = ("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad")
FRI_SAT = frozenset(("Kedah", "Kelantan", "Terengganu"))
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
    weekend = target.weekday() in ((4, 5) if state in FRI_SAT else (5, 6))
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
        selected.append({"day":day,"start":start,"end":end,
                         "class_name":cls,"subject":subject,
                         "year":year,"subject_code":code,"component":component,
                         "can_prepare":valid,"reason":reason})
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
        "lesson_note":"Lesson/PdP mesti dipilih daripada katalog asal. Tiada nombor PdP diteka.",
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
    if raw is None:
        target = malaysia_today()
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
        result = day_payload(profile,schedule,target)
    except ProfileValidation as exc:
        return jsonify({"error":str(exc)}),400
    except ProfileUnavailable:
        return jsonify({"error":"Jadual guru belum dapat dibaca. Data lama tidak diubah."}),503
    return jsonify(result)
