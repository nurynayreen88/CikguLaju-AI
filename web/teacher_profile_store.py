"""Shared Telegram/Web teacher profile. Telegram class_profiles is canonical.

Schedule writes update class_profiles in the same profile record. An old Web
schedule table stays untouched as a recovery copy. No payments or credits touched.
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
    "W.P. Kuala Lumpur", "W.P. Putrajaya", "W.P. Labuan",
))
SCHEDULE_KEYS = frozenset(("day", "start", "end", "class_name", "subject"))
PROFILE_KEYS = frozenset(("display_name", "school_name", "state_name", "class_names", "version"))
AVATAR_CODES = frozenset(("initials", "teacher", "books", "pencil", "graduation", "art", "science", "math", "music", "star", "sun", "flower"))
SCHEDULE_PUT_KEYS = frozenset(("entries", "version"))
MAX_RESPONSE = 65536
TIME = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")
SUBJECT = re.compile(r"[\w .\-/()&,]+", re.UNICODE)
SUBJECT_CODE = re.compile(r"[A-Z][A-Z0-9]{1,7}")
STANDARD_SUBJECT_CODES = {
    "BM": "Bahasa Melayu", "BI": "English", "EN": "English", "ENG": "English",
    "BA": "Bahasa Arab", "ARAB": "Bahasa Arab",
    "MT": "Matematik", "MM": "Matematik", "MATH": "Matematik",
    "SN": "Sains", "SC": "Sains", "SCIENCE": "Sains",
    "PI": "Pendidikan Islam", "PAI": "Pendidikan Islam",
    "PM": "Pendidikan Moral", "MORAL": "Pendidikan Moral",
    "PSV": "Pendidikan Seni Visual", "MZ": "Pendidikan Muzik",
    "MUZIK": "Pendidikan Muzik", "PJ": "Pendidikan Jasmani",
    "PK": "Pendidikan Kesihatan", "PJPK": "Pendidikan Jasmani dan Pendidikan Kesihatan",
    "RBT": "Reka Bentuk dan Teknologi", "SJ": "Sejarah", "SEJ": "Sejarah",
}


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


def normalize_timetable_subject(subject, aliases):
    if not isinstance(subject, str):
        return subject
    code = subject.strip().upper()
    return aliases.get(code, STANDARD_SUBJECT_CODES.get(code, subject))


def clean_subject_aliases(aliases):
    if not isinstance(aliases, dict) or len(aliases) > 40:
        raise ProfileValidation("Maksimum 40 singkatan subjek")
    result = {}
    for raw_code, raw_subject in aliases.items():
        code = _validated_name(raw_code, 8, "Singkatan subjek", required=True).upper()
        if (not SUBJECT_CODE.fullmatch(code) or code in result):
            raise ProfileValidation("Singkatan subjek tidak sah atau berulang")
        subject = _validated_name(raw_subject, 60, "Nama penuh subjek", required=True)
        if not SUBJECT.fullmatch(subject) or SUBJECT_CODE.fullmatch(subject):
            raise ProfileValidation("Masukkan nama penuh bagi " + code)
        result[code] = subject
    return result


def clean_profile(form):
    school_fields = {"school_code", "district_name"}
    accepted = (PROFILE_KEYS, PROFILE_KEYS | {"avatar_code"},
                PROFILE_KEYS | school_fields,
                PROFILE_KEYS | school_fields | {"avatar_code"})
    if not isinstance(form, dict) or set(form) not in accepted:
        raise ProfileValidation("Maklumat profil tidak lengkap")
    name = _validated_name(form["display_name"], 100, "Nama guru", required=True).upper()
    if len(name) > 100:
        raise ProfileValidation("Nama guru terlalu panjang")
    school = _validated_name(form["school_name"], 160, "Nama sekolah")
    state = _validated_name(form["state_name"], 30, "Negeri")
    if state and state not in STATES:
        raise ProfileValidation("Negeri tidak sah")
    avatar_code = form.get("avatar_code")
    if avatar_code is not None and (not isinstance(avatar_code, str) or avatar_code not in AVATAR_CODES):
        raise ProfileValidation("Pilihan avatar tidak sah")
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
    values = {"display_name": name, "school_name": school,
              "state_name": state or None, "class_names": cleaned}
    if "school_code" in form:
        code = _validated_name(form["school_code"], 12, "Kod sekolah")
        district = _validated_name(form["district_name"], 100, "PPD sekolah")
        if bool(code) != bool(district) or (code and not state):
            raise ProfileValidation("Pilih negeri, PPD dan sekolah bersama-sama")
        values["school_code"] = code or None
        values["district_name"] = district or None
    if avatar_code is not None:
        values["avatar_code"] = avatar_code
    return values, _version(form["version"])


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


def _class_records(record):
    """Read Telegram's canonical class_profiles without dropping student counts.

    class_names is a backwards-compatible mirror; never treat a separate
    Web timetable record as more authoritative than Telegram class records.
    """
    if record is None:
        return []
    raw = record.get("class_profiles") or []
    if not isinstance(raw, list):
        raise ProfileUnavailable("Data kelas lama perlu disemak")
    rows = []
    if raw:
        for item in raw:
            if isinstance(item, str):
                item = {"name": item, "students": None, "timetable": []}
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise ProfileUnavailable("Rekod kelas tidak sah")
            name = item["name"].strip()
            if not name:
                raise ProfileUnavailable("Nama kelas tidak sah")
            timetable = item.get("timetable") or []
            if not isinstance(timetable, list):
                raise ProfileUnavailable("Jadual kelas tidak sah")
            rows.append({**item, "name": name, "timetable": timetable})
    else:
        names = record.get("class_names") or []
        if not isinstance(names, list):
            raise ProfileUnavailable("Senarai kelas tidak sah")
        rows = [{"name": item.strip(), "students": None, "timetable": []}
                for item in names if isinstance(item, str) and item.strip()]
    if len({r["name"].casefold() for r in rows}) != len(rows):
        raise ProfileUnavailable("Kelas berulang dalam rekod lama")
    return rows


def _profile_record(url, key, uid, *, opener=None):
    return _get_one(
        url, key, "teacher_profiles", uid,
        "telegram_user_id,display_name,school_name,state_name,district_name,school_code,avatar_code,class_names,class_profiles,timetable_subject_aliases,timetable_class_aliases,updated_at",
        opener=opener,
    )


def _flatten_timetable(rows):
    result = []
    for row in rows:
        for entry in row.get("timetable") or []:
            if not isinstance(entry, dict):
                raise ProfileUnavailable("Baris jadual lama tidak sah")
            result.append({
                "day": entry.get("day"), "start": entry.get("start"),
                "end": entry.get("end"), "class_name": row["name"],
                "subject": entry.get("subject"),
            })
    return result


def get_profile(url, key, uid, *, opener=None):
    record = _profile_record(url, key, uid, opener=opener)
    if record is None:
        return {"display_name": "Cikgu", "school_name": "",
                "state_name": "", "district_name": "", "school_code": "",
                "avatar_code": "initials", "class_names": [], "timetable_subject_aliases": {},
                "timetable_class_aliases": {}, "version": ""}
    classes = [r["name"] for r in _class_records(record)]
    return {
        "display_name": record.get("display_name") or "Cikgu",
        "school_name": record.get("school_name") or "",
        "state_name": record.get("state_name") or "",
        "district_name": record.get("district_name") or "",
        "school_code": record.get("school_code") or "",
        "avatar_code": record.get("avatar_code") if record.get("avatar_code") in AVATAR_CODES else "initials",
        "class_names": classes,
        "timetable_subject_aliases": record.get("timetable_subject_aliases") or {},
        "timetable_class_aliases": record.get("timetable_class_aliases") or {},
        "version": record.get("updated_at") or "",
    }


def get_schedule(url, key, uid, *, opener=None):
    record = _profile_record(url, key, uid, opener=opener)
    if record is None:
        return {"entries": [], "version": ""}
    classes = _class_records(record)
    # The current Telegram menu and RPH timetable resolver use class_profiles.
    # No fallback is permitted once class_profiles exist: an intentionally
    # cleared timetable must stay empty, not resurrect archived Web entries.
    if record.get("class_profiles"):
        entries = _flatten_timetable(classes)
    else:
        # Read-only compatibility for the pre-unification Web timetable rows.
        legacy = _get_one(url, key, "teacher_timetables", uid,
                          "telegram_user_id,entries,updated_at", opener=opener)
        entries = (legacy.get("entries") or []) if legacy else []
    aliases = record.get("timetable_subject_aliases") or {}
    return {
        "entries": [
            {**row, "subject": normalize_timetable_subject(row.get("subject"), aliases)}
            for row in entries
        ],
        "version": record.get("updated_at") or "",
    }


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
    """Patch shared profile and class_profiles atomically, preserving each class schedule."""
    values, version = clean_profile(form)
    record = _profile_record(url, key, uid, opener=opener)
    if version != ((record or {}).get("updated_at") or ""):
        raise ProfileConflict("Maklumat telah dikemas kini. Muat semula")
    # New picker submissions can never forge a full school name or attach a
    # real school code to a different PPD/negeri. Legacy unchanged text is
    # preserved so pre-existing teacher profiles are not destructively reset.
    if "school_code" in values:
        code = values["school_code"]
        if code:
            same_school = bool(
                record and record.get("school_code") == code and
                record.get("state_name") == values["state_name"] and
                record.get("district_name") == values["district_name"] and
                (record.get("school_name") or "").casefold() ==
                values["school_name"].casefold()
            )
            if same_school:
                # Preserve the existing verified school code and normalize
                # the stored name without a second HTTP call for class edits.
                from web.school_directory_store import full_school_name
                values["school_name"] = full_school_name(record["school_name"])
            else:
                from web.school_directory_store import (
                    SchoolDirectoryUnavailable, school_by_code,
                )
                try:
                    school = school_by_code(url, key, code, opener=opener)
                except SchoolDirectoryUnavailable:
                    raise ProfileUnavailable("Direktori sekolah belum tersedia") from None
                except ValueError:
                    raise ProfileValidation("Kod sekolah tidak dijumpai dalam direktori") from None
                if (school["state_name"] != values["state_name"] or
                        school["district_name"] != values["district_name"]):
                    raise ProfileValidation("Sekolah tidak sepadan dengan negeri atau PPD")
                values["school_name"] = school["school_name"]
        elif (record and record.get("school_code")
              and values["school_name"].casefold() ==
                  (record.get("school_name") or "").casefold()
              and values["state_name"] == record.get("state_name")):
            # An unavailable/legacy picker must not wipe previously linked data.
            from web.school_directory_store import full_school_name
            values["school_name"] = full_school_name(record["school_name"])
            values["school_code"] = record["school_code"]
            values["district_name"] = record.get("district_name")
        elif values["school_name"]:
            # Legacy school names may be uppercased safely; never allow free
            # text replacement or dropping a linked code while saving classes.
            if (not record or record.get("school_code") or
                    values["school_name"].casefold() !=
                        (record.get("school_name") or "").casefold() or
                    values["state_name"] != record.get("state_name")):
                raise ProfileValidation("Pilih sekolah daripada direktori rasmi")
            values["school_name"] = record["school_name"].upper()
    elif record and record.get("school_code"):
        if (values["school_name"].casefold() !=
                (record.get("school_name") or "").casefold() or
                values["state_name"] != record.get("state_name")):
            raise ProfileValidation("Muat semula profil dan pilih sekolah daripada senarai")
        from web.school_directory_store import full_school_name
        values["school_name"] = full_school_name(record["school_name"])
    elif values["school_name"]:
        # Backward-compatible Telegram/legacy calls without school_code:
        # retain their existing free-text semantics but store uppercase.
        values["school_name"] = values["school_name"].upper()
    rows = _class_records(record)
    byname = {r["name"].casefold(): r for r in rows}
    keep = {name.casefold() for name in values["class_names"]}
    for row in rows:
        # Removing a class with timetable entries must never silently delete periods.
        if row["name"].casefold() not in keep and row.get("timetable"):
            raise ProfileValidation(
                "Kelas masih mempunyai jadual. Padam waktu kelas itu dahulu.")
    class_profiles = []
    for name in values["class_names"]:
        old = byname.get(name.casefold())
        if old is not None:
            class_profiles.append({**old, "name": name})
        else:
            class_profiles.append({"name": name, "students": None, "timetable": []})
    values["class_profiles"] = class_profiles
    return _save(url, key, "teacher_profiles", uid, values, version, opener=opener)


def save_subject_aliases(url, key, uid, form, *, opener=None):
    if set(form) != {"aliases", "version"}:
        raise ProfileValidation("Maklumat singkatan subjek tidak lengkap")
    aliases = clean_subject_aliases(form["aliases"])
    version = _version(form["version"])
    if not version:
        raise ProfileValidation("Simpan maklumat guru terlebih dahulu")
    return _save(url, key, "teacher_profiles", uid,
                 {"timetable_subject_aliases": aliases}, version, opener=opener)


def clean_class_aliases(aliases):
    if not isinstance(aliases, dict) or len(aliases) > 80:
        raise ProfileValidation("Maksimum 80 padanan kelas")
    result = {}
    for raw_code, raw_name in aliases.items():
        code = _validated_name(raw_code, 40, "Kod kelas", required=True).upper()
        name = _validated_name(raw_name, 40, "Nama penuh kelas", required=True)
        if not CLASS_PATTERN.fullmatch(code) or not CLASS_PATTERN.fullmatch(name) or code in result:
            raise ProfileValidation("Nama atau kod kelas tidak sah")
        result[code] = name
    return result


def _import_schedule(url, key, uid, form, record, records, classes, *, opener=None):
    if set(form) != {"changes", "version", "subject_aliases", "class_aliases"}:
        raise ProfileValidation("Maklumat import jadual tidak lengkap")
    aliases = record.get("timetable_subject_aliases") or {}
    subject_aliases = clean_subject_aliases({**aliases, **clean_subject_aliases(form["subject_aliases"])})
    class_aliases = clean_class_aliases({
        **(record.get("timetable_class_aliases") or {}), **clean_class_aliases(form["class_aliases"]),
    })
    changes = form["changes"]
    if not isinstance(changes, list) or not 0 < len(changes) <= 80:
        raise ProfileValidation("Pilih antara 1 hingga 80 waktu")
    current = _flatten_timetable(records)
    if record and not record.get("class_profiles"):
        legacy = _get_one(url, key, "teacher_timetables", uid,
                          "telegram_user_id,entries,updated_at", opener=opener)
        current = (legacy.get("entries") or []) if legacy else []
    visible = [{**row, "subject": normalize_timetable_subject(row.get("subject"), aliases)}
               for row in current]
    added, replaced = [], set()
    known = {name.casefold() for name in classes}
    for change in changes:
        if (not isinstance(change, dict) or set(change) != {"entry", "replace"}
                or not isinstance(change["entry"], dict)):
            raise ProfileValidation("Pilihan import tidak sah")
        entry, prior = change["entry"], change["replace"]
        if prior is not None:
            try:
                index = visible.index(prior)
            except ValueError:
                raise ProfileConflict("Waktu sedia ada telah berubah") from None
            if index in replaced:
                raise ProfileValidation("Waktu sedia ada hanya boleh dikemas kini sekali")
            replaced.add(index)
        name = _validated_name(entry.get("class_name"), 40, "Nama kelas", required=True)
        if not CLASS_PATTERN.fullmatch(name):
            raise ProfileValidation("Nama kelas tidak sah")
        if name.casefold() not in known:
            records.append({"name": name, "students": None, "timetable": []})
            classes.append(name)
            known.add(name.casefold())
        selected, _ = clean_schedule({"entries": [entry], "version": form["version"]}, classes)
        new_row = selected[0]
        if prior is not None and (
                new_row["day"] != prior["day"] or not
                (new_row["start"] < prior["end"] and prior["start"] < new_row["end"])):
            raise ProfileValidation("Waktu kemas kini mesti bertindih dengan waktu asal")
        added.append({**new_row, "subject": normalize_timetable_subject(new_row["subject"], subject_aliases)})
    if len(classes) > 25:
        raise ProfileValidation("Maksimum 25 kelas dalam profil")
    retained = [row for index, row in enumerate(current) if index not in replaced]
    return {"entries": retained + added, "version": form["version"]}, {
        "timetable_subject_aliases": subject_aliases, "timetable_class_aliases": class_aliases,
    }


def save_schedule(url, key, uid, form, *, opener=None, guided=False):
    """Write the shared Telegram and Web timetable in one versioned update."""
    record = _profile_record(url, key, uid, opener=opener)
    if not record and not guided:
        raise ProfileValidation("Simpan maklumat kelas terlebih dahulu")
    record = record or {}
    version = _version(form.get("version"))
    if version != (record.get("updated_at") or ""):
        raise ProfileConflict("Maklumat telah dikemas kini. Muat semula")
    records = _class_records(record)
    classes = [r["name"] for r in records]
    aliases = record.get("timetable_subject_aliases") or {}
    values = {} if record else {"display_name": "Cikgu"}
    if guided:
        form, mappings = _import_schedule(url, key, uid, form, record, records, classes, opener=opener)
        values.update(mappings)
    entries, _ = clean_schedule(form, classes)
    byname = {r["name"].casefold(): [] for r in records}
    for entry in entries:
        byname[entry["class_name"].casefold()].append({
            "day": entry["day"], "start": entry["start"], "end": entry["end"],
            "subject": entry["subject"] if guided else normalize_timetable_subject(entry["subject"], aliases),
        })
    updated = [{**r, "timetable": byname[r["name"].casefold()]} for r in records]
    values.update(class_profiles=updated, class_names=classes)
    return _save(url, key, "teacher_profiles", uid, values, version, opener=opener)
