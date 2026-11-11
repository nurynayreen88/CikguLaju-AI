"""Server-side Supabase directory lookup for Negeri -> PPD -> Sekolah.

Only verified Web sessions call these helpers. Browser never receives
Supabase credentials, and source data is immutable through these routes.
The 2022-06 reference directory is *not* claimed to be current KPM data.
"""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener

from web.teacher_profile_store import NoRedirect

_TABLES = frozenset(("school_states", "school_districts", "school_directory", "school_logo_sources"))
_CODE = re.compile(r"[A-Z0-9]{6,12}\Z")
MAX_RESPONSE = 220000


class SchoolDirectoryUnavailable(Exception):
    pass


def _name(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 100:
        raise ValueError("Invalid " + label)
    if any(ord(ch) < 32 for ch in value):
        raise ValueError("Invalid " + label)
    return value.strip()


def _read(url, secret, table, query, *, limit=350, opener=None):
    parts = urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or parts.port is not None
            or parts.path not in ("", "/") or parts.query or parts.fragment
            or table not in _TABLES or not isinstance(secret, str)
            or len(secret) < 20 or not isinstance(query, dict)
            or not 0 < limit <= 350):
        raise SchoolDirectoryUnavailable("School directory configuration unavailable")
    options = {**query, "limit": str(limit)}
    endpoint = url.rstrip("/") + "/rest/v1/" + table + "?" + urlencode(options)
    req = Request(endpoint, headers={
        "apikey": secret, "Authorization": "Bearer " + secret,
        "Accept": "application/json",
    }, method="GET")
    try:
        with (opener or build_opener(NoRedirect())).open(req, timeout=9) as response:
            if response.status != 200:
                raise SchoolDirectoryUnavailable("School directory unavailable")
            body = response.read(MAX_RESPONSE + 1)
        if len(body) > MAX_RESPONSE:
            raise SchoolDirectoryUnavailable("Oversized directory response")
        rows = json.loads(body)
        if not isinstance(rows, list) or len(rows) > limit or any(
                not isinstance(row, dict) for row in rows):
            raise SchoolDirectoryUnavailable("Invalid directory response")
        return rows
    except (HTTPError, URLError, OSError, ValueError, UnicodeError, TypeError):
        raise SchoolDirectoryUnavailable("School directory temporarily unavailable") from None


def states(url, secret, *, opener=None):
    rows = _read(url, secret, "school_states",
                 {"select": "state_name", "order": "state_name.asc"},
                 limit=25, opener=opener)
    return [{"value": r["state_name"], "label": r["state_name"]} for r in rows]


def districts(url, secret, state, *, opener=None):
    state = _name(state, "state")
    rows = _read(url, secret, "school_districts", {
        "select": "district_name",
        "state_name": "eq." + state,
        "order": "district_name.asc",
    }, limit=80, opener=opener)
    return [{"value": r["district_name"], "label": r["district_name"]}
            for r in rows]


def schools(url, secret, state, district, *, opener=None):
    state = _name(state, "state")
    district = _name(district, "district")
    rows = _read(url, secret, "school_directory", {
        "select": "school_code,school_name,school_level",
        "state_name": "eq." + state, "district_name": "eq." + district,
        "school_level": "eq.Rendah",
        "order": "school_name.asc,school_code.asc",
    }, limit=350, opener=opener)
    return [{"value": r["school_code"], "label": r["school_name"],
             "level": r.get("school_level") or ""}
            for r in rows]


def school_by_code(url, secret, code, *, opener=None):
    if not isinstance(code, str) or not _CODE.fullmatch(code):
        raise ValueError("Invalid school code")
    rows = _read(url, secret, "school_directory", {
        "select": "school_code,school_name,state_name,district_name,school_level",
        "school_level": "eq.Rendah",
        "school_code": "eq." + code,
    }, limit=2, opener=opener)
    if len(rows) != 1 or rows[0].get("school_code") != code:
        raise ValueError("School not found in verified directory")
    if rows[0].get("school_level") != "Rendah":
        raise ValueError("Only primary schools are supported")
    return rows[0]
