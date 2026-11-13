"""Server-only, teacher-scoped Supabase access for the Web PBD module."""
import json
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener

from web.teacher_profile_store import NoRedirect

ROSTERS = "web_pbd_rosters"
RECORDS = "web_pbd_records"


class StorageError(Exception):
    pass


class Conflict(StorageError):
    pass


def request_rows(conf, uid, table, method, filters, data=None):
    base = urlsplit(conf["supabase_url"])
    key = conf["supabase_key"]
    if (type(uid) is not int or uid <= 0 or table not in (ROSTERS, RECORDS)
            or base.scheme != "https" or not base.hostname or base.username or base.password
            or base.path not in ("", "/") or base.query or base.fragment or not key):
        raise StorageError()
    query = urlencode({**filters, "teacher_id": f"eq.{uid}"})
    headers = {"apikey": key, "Authorization": "Bearer " + key, "Accept": "application/json"}
    body = None
    if method != "GET":
        headers["Prefer"] = "return=representation"
        headers["Content-Type"] = "application/json"
        if data is not None:
            payload = {**data, "teacher_id": uid} if method == "POST" else data
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(f"{base.geturl().rstrip('/')}/rest/v1/{table}?{query}",
                  data=body, headers=headers, method=method)
    try:
        with build_opener(NoRedirect()).open(req, timeout=10) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise StorageError()
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise StorageError()
        return rows
    except HTTPError as exc:
        if exc.code in (409, 412):
            raise Conflict() from None
        raise StorageError() from None
    except (OSError, ValueError, TypeError):
        raise StorageError() from None


def scope(class_name, school_year):
    return {"class_name": f"eq.{class_name}", "school_year": f"eq.{school_year}"}


def one(conf, uid, table, filters):
    rows = request_rows(conf, uid, table, "GET", {**filters, "limit": 1})
    return rows[0] if rows else None


def roster_count(conf, uid, filters):
    row = one(conf, uid, ROSTERS, {**filters, "select": "students"})
    return len(row["students"]) if row else 0


def write(conf, uid, table, filters, payload, version=""):
    method = "PATCH" if version else "POST"
    if version:
        filters = {**filters, "version": "eq." + version}
    rows = request_rows(conf, uid, table, method, filters, payload)
    if len(rows) != 1:
        raise Conflict()
    return rows[0]
