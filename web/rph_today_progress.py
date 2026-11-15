"""Read and record explicit PdP completion for the authenticated Web teacher."""
import json
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener

from itsdangerous import URLSafeTimedSerializer

from web.teacher_profile_store import NoRedirect, ProfileUnavailable


TABLE = "web_timetable_pdp_completion"
RPC = "rpc/web_timetable_pdp_progress"
NUMBER = re.compile(r"^(?:Lesson|PdP)\s*(\d{1,3})\b", re.IGNORECASE)


def class_key(value):
    return " ".join(value.casefold().split())


def lesson_number(item):
    match = NUMBER.match(str(item.get("label", "")).strip())
    number = int(match[1]) if match else next(
        (item[key] for key in ("pdp_no", "lesson_no", "sequence_no")
         if type(item.get(key)) is int), 0)
    return number if 1 <= number <= 999 else None


def lesson_signer(config):
    return URLSafeTimedSerializer(config["CIKGULAJU_WEB_SESSION_SECRET"],
                                  salt="cikgulaju-web-pdp-completion-v1")


def _request(config, path, method, payload=None, filters=None, *, prefer=None):
    base = urlsplit(config["supabase_url"])
    key = config["supabase_key"]
    if (base.scheme != "https" or not base.hostname or base.username or base.password
            or base.path not in ("", "/") or base.query or base.fragment or not key):
        raise ProfileUnavailable("Invalid Supabase address")
    headers = {"apikey": key, "Authorization": "Bearer " + key,
               "Accept": "application/json", "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(payload).encode() if payload is not None else None
    url = base.geturl().rstrip("/") + "/rest/v1/" + path
    if filters:
        url += "?" + urlencode(filters)
    request = Request(url, data=data, method=method, headers=headers)
    try:
        with build_opener(NoRedirect()).open(request, timeout=4) as response:
            raw = response.read(262145)
        if len(raw) > 262144:
            raise ValueError("Oversized response")
        return json.loads(raw) if raw else None
    except (OSError, ValueError) as exc:
        raise ProfileUnavailable("Rekod PdP belum tersedia") from exc


def read_progress(config, uid, target):
    rows = _request(config, RPC, "POST", {"p_teacher_id": uid, "p_target": target})
    if not isinstance(rows, list):
        raise ProfileUnavailable("Format rekod PdP tidak sah")
    return rows


def save_completion(config, uid, day, slot, component, number):
    key = {
        "teacher_id": uid, "class_key": class_key(slot["class_name"]),
        "subject_code": slot["subject_code"], "component": component,
        "pdp_date": day, "start_time": slot["start"],
    }
    if number is None:
        _request(config, TABLE, "DELETE", filters={k: f"eq.{v}" for k, v in key.items()})
    else:
        _request(config, TABLE, "POST", {**key, "sequence_no": number},
                 prefer="resolution=merge-duplicates,return=minimal")


def attach_progress(day, rows):
    by_scope = {}
    for row in rows:
        scope = row["class_key"], row["subject_code"], row["component"]
        by_scope.setdefault(scope, {})[(row["pdp_date"], row["start_time"][:5])] = row["sequence_no"]
    for slot in day["entries"]:
        if not slot["can_prepare"]:
            continue
        slot_date = day["date"], slot["start"]
        recorded = {}
        for component in ((slot["component"],) if slot["component"] else
                          ("PJ", "PK") if slot["subject_code"] == "PJPK" else ("",)):
            records = by_scope.get((class_key(slot["class_name"]), slot["subject_code"], component), {})
            previous = max((when for when in records if when < slot_date), default=None)
            recorded[component] = {"completed": records.get(slot_date),
                                   "previous": records.get(previous)}
        slot["progress"] = recorded
