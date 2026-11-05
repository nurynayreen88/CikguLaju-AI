"""CikguLaju teacher profile data stored in the existing shared Supabase project.

Only names/school/classes/state are updated in existing teacher_profiles; schedules
use the separate teacher_timetables table. No credits, referrals, payment, RPH
or Telegram runtime tables are written. Authenticated server-side use only.
"""
import json
import re
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from web.teacher_class_choices import CLASS_PATTERN


DAYS = frozenset(("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"))
STATES = frozenset((
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Perak", "Perlis", "Pulau Pinang", "Sabah", "Sarawak",
    "Selangor", "Terengganu", "Kuala Lumpur", "Putrajaya", "Labuan",
))
SCHEDULE_KEYS = frozenset(("day", "start", "end", "class_name", "subject"))
PROFILE_KEYS = frozenset(("display_name", "school_name", "state_name", "class_names", "version"))
SCHEDULE_PUT_KEYS = frozenset(("entries", "version"))
MAX_RESPONSE = 65536
TIME = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")
SUBJECT = re.compile(r"[\w .\-/()&,]+", re.UNICODE)


class ProfileConflict(Exception):
    pass


class ProfileUnavailable(Exception):
    pass


class ProfileValidation(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _endpoint(url, table, query):
    u = urlsplit(url)
    if (u.scheme != "https" or not u.hostname or u.username or u.password
            or u.path not in ("", "/") or u.query or u.fragment or u.port is not None):
        raise ProfileUnavailable("Invalid Supabase address")
    if table not in ("teacher_profiles", "teacher_timetables"):
        raise ProfileUnavailable("Unapproved database table")
    return url.rstrip("/") + "/rest/v1/" + table + "?" + urlencode(query)


def _rest(url, service_key, table, method, query, payload=None, opener=None):
    if not isinstance(service_key, str) or not service_key:
        raise ProfileUnavailable("Server account configuration unavailable")
    endpoint = _endpoint(url, table, query)
    headers = {
        "apikey": service_key, "Authorization": "Bearer " + service_key,
        "Accept": "application/json", "Content-Type": "application/json",
    }
    if method in ("PATCH", "POST"):
        headers["Prefer"] = "return=representation"
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8") if payload is not None else None
    request = Request(endpoint, data=data, headers=headers, method=method)
    try:
        with (opener or build_opener(NoRedirect())).open(request, timeout=8) as response:
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise ProfileUnavailable("Oversized backend response")
        rows = json.loads(raw)
        if not isinstance(rows, list) or len(rows) > 2:
            raise ProfileUnavailable("Ambiguous backend records")
        return rows
    except HTTPError as exc:
        # Never log exception or URL: Supabase URL may contain identifiers.
        if exc.code in (409, 412):
            raise ProfileConflict("Record updated elsewhere") from None
        raise ProfileUnavailable("Supabase request rejected") from None
    except (ValueError, TypeError, OSError):
        raise ProfileUnavailable("Supabase record unavailable") from None


def _get_one(url, key, table, uid, select, *, opener=None):
    if type(uid) is not int or uid <= 0:
        raise ProfileValidation("Invalid authenticated account")
    rows = _rest(url, key, table, "GET", {
        "select": select, "telegram_user_id": "eq." + str(uid), "limit": "2",
    }, opener=opener)
    if len(rows) > 1 or (rows and (not isinstance(rows[0], dict) or
        rows[0].get("telegram_user_id") != uid)):
        raise ProfileUnavailable("Ambiguous profile")
    return rows[0] if rows else None


def _version(value):
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > 50:
        raise ProfileValidation("Invalid record version")
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ProfileValidation("Invalid record version") from None
    if dt.tzinfo is None:
        raise ProfileValidation("Invalid record version")
    return value


def _now():
    return datetime.now(timezone.utc).isoformat()


def _validated_name(value, max_len, label, *, required=False):
    if not isinstance(value, str):
        raise ProfileValidation(label + " mesti teks")
    item = value.strip()
    if len(item) > max_len or any(ord(c) < 32 for c in item):
        raise ProfileValidation(label + " terlalu panjang atau tidak sah")
    if required and not item:
        raise ProfileValidation(label + " diperlukan")
    return item


def clean_profile(form):
    if not isinstance(form, dict) or set(form) != PROFILE_KEYS:
        raise ProfileValidation("Maklumat profil tidak lengkap")
    name = _validated_name(form["display_name"], 100, "Nama guru", required=True)
    school = _validated_name(form["school_name"], 160, "Nama sekolah")
    state = _validated_name(form["state_name"], 30, "Negeri")
    if state and state not in STATES:
        raise ProfileValidation("Negeri tidak sah")
    classes = form["class_names"]
    if not isinstance(classes, list) or len(classes) > 25:
        raise ProfileValidation("Maksimum 25 kelas")
    cleaned, seen = [], set()
    for value in classes:
        if not isinstance(value, str):
            raise ProfileValidation("Senarai kelas tidak sah")
        cls = value.strip()
        if not 0 < len(cls) <= 40 or not CLASS_PATTERN.fullmatch(cls):
            raise ProfileValidation("Nama kelas tidak sah")
        if cls.casefold() in seen:
            raise ProfileValidation("Nama kelas berulang")
        cleaned.append(cls)
        seen.add(cls.casefold())
    return {"display_name": name, "school_name": school,
            "state_name": state or None, "class_names": cleaned}, _version(form["version"])


def clean_schedule(form, class_names):
    if not isinstance(form, dict) or set(form) != SCHEDULE_PUT_KEYS:
        raise ProfileValidation("Data jadual tidak lengkap")
    entries = form["entries"]
    if not isinstance(entries, list) or len(entries) > 80:
        raise ProfileValidation("Maksimum 80 waktu")
    permitted = {str(c).casefold() for c in class_names}
    result, keys = [], set()
    slots = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != SCHEDULE_KEYS:
            raise ProfileValidation("Baris jadual tidak sah")
        day, start, end = (entry[k] for k in ("day", "start", "end"))
        cls = _validated_name(entry["class_name"], 40, "Kelas", required=True)
        subject = _validated_name(entry["subject"], 60, "Subjek", required=True)
        if (not isinstance(day, str) or day not in DAYS
                or not isinstance(start, str) or not isinstance(end, str)
                or not TIME.fullmatch(start) or not TIME.fullmatch(end) or start >= end):
            raise ProfileValidation("Hari atau masa tidak sah")
        if cls.casefold() not in permitted:
            raise ProfileValidation("Sila simpan kelas dalam profil sebelum mengisi jadual")
        if not SUBJECT.fullmatch(subject):
            raise ProfileValidation("Nama subjek tidak sah")
        key = (day, start, end, cls.casefold(), subject.casefold())
        if key in keys:
            raise ProfileValidation("Waktu berganda")
        keys.add(key)
        slots.setdefault(day, []).append((start, end))
        result.append({"day": day, "start": start, "end": end,
                       "class_name": cls, "subject": subject})
    # A teacher cannot teach two separate lessons at the same time.
    for day_slots in slots.values():
        day_slots.sort()
        for (_, last_end), (next_start, _) in zip(day_slots, day_slots[1:]):
            if next_start < last_end:
                raise ProfileValidation("Waktu bertindih pada hari yang sama")
    return result, _version(form["version"])


def get_profile(url, key, uid, *, opener=None):
    record = _get_one(url, key, "teacher_profiles", uid,
                      "telegram_user_id,display_name,school_name,state_name,class_names,updated_at",
                      opener=opener)
    if record is None:
        return {"display_name": "Cikgu", "school_name": "",
                "state_name": "", "class_names": [], "version": ""}
    return {
        "display_name": record.get("display_name") or "Cikgu",
        "school_name": record.get("school_name") or "",
        "state_name": record.get("state_name") or "",
        "class_names": record.get("class_names") or [],
        "version": record.get("updated_at") or "",
    }


def get_schedule(url, key, uid, *, opener=None):
    record = _get_one(url, key, "teacher_timetables", uid,
                      "telegram_user_id,entries,updated_at", opener=opener)
    return {"entries": (record.get("entries") if record else []) or [],
            "version": (record.get("updated_at") if record else "") or ""}


def _save(url, key, table, uid, values, expected_version, *, opener=None):
    if type(uid) is not int or uid <= 0:
        raise ProfileValidation("Akaun tidak sah")
    current = _get_one(
        url, key, table, uid, "telegram_user_id,updated_at", opener=opener)
    existing_version = current.get("updated_at") if current else ""
    if expected_version != existing_version:
        raise ProfileConflict("Rekod telah berubah. Muat semula sebelum simpan")
    values = {**values, "updated_at": _now()}
    if current is None:
        query = {"select": "telegram_user_id,updated_at"}
        saved = _rest(url, key, table, "POST", query, {
            "telegram_user_id": uid, **values}, opener=opener)
    else:
        query = {"select": "telegram_user_id,updated_at",
                 "telegram_user_id": "eq." + str(uid),
                 "updated_at": "eq." + existing_version}
        saved = _rest(url, key, table, "PATCH", query, values, opener=opener)
    if len(saved) != 1 or saved[0].get("telegram_user_id") != uid:
        raise ProfileConflict("Rekod berubah. Sila muat semula")
    return saved[0]["updated_at"]


def save_profile(url, key, uid, form, *, opener=None):
    values, version = clean_profile(form)
    return _save(url, key, "teacher_profiles", uid, values, version, opener=opener)


def save_schedule(url, key, uid, form, *, opener=None):
    profile = get_profile(url, key, uid, opener=opener)
    entries, version = clean_schedule(form, profile["class_names"])
    return _save(url, key, "teacher_timetables", uid,
                 {"entries": entries}, version, opener=opener)
