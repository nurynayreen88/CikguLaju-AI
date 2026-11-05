"""Read-only, signed-in teacher class suggestions from existing Supabase profiles.

No user rows are created or updated. Never expose the service key to the browser.
"""
import json
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

CLASS_PATTERN = re.compile(r"[\w .\-/()]+", re.UNICODE)


def normalize_class_names(values):
    """Filter profile data to names accepted by the existing Web RPH backend."""
    if not isinstance(values, list):
        return []
    items = []
    seen = set()
    for value in values[:100]:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not (0 < len(item) <= 40 and CLASS_PATTERN.fullmatch(item)):
            continue
        key = item.casefold()
        if key not in seen:
            items.append(item)
            seen.add(key)
        if len(items) >= 25:
            break
    return items


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_existing_teacher_classes(supabase_url, service_key, telegram_id, *, opener=None):
    if type(telegram_id) is not int or telegram_id <= 0:
        raise ValueError("Invalid signed-in teacher")
    parts = urlsplit(supabase_url)
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or parts.query or parts.fragment or parts.path not in ("", "/")
            or not service_key):
        raise ValueError("Invalid server-side Supabase configuration")
    params = urlencode({"select": "class_names",
                        "telegram_user_id": "eq." + str(telegram_id), "limit": "2"})
    endpoint = supabase_url.rstrip("/") + "/rest/v1/teacher_profiles?" + params
    req = Request(endpoint, headers={"apikey": service_key,
        "Authorization": "Bearer " + service_key,
        "Accept": "application/json"}, method="GET")
    client = opener or build_opener(_NoRedirect())
    with client.open(req, timeout=6) as result:
        body = result.read(16385)
    if len(body) > 16384:
        raise ValueError("Oversized profile response")
    records = json.loads(body)
    if not isinstance(records, list) or len(records) > 1:
        raise ValueError("Ambiguous teacher profile")
    if not records:
        return []
    if not isinstance(records[0], dict):
        raise ValueError("Invalid teacher profile")
    return normalize_class_names(records[0].get("class_names"))
