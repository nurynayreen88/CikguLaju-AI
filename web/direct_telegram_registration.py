"""Create a CikguLaju account after VERIFIED Telegram Login Widget identity.

The verified Telegram ID is the only account key. A conflict-safe insert does
not overwrite any existing user, entitlement, quota or profile. Supabase is
the same authoritative account store used by Telegram's admin directory.
"""
import json
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


def _rest(config, method, table, *, query=None, payload=None, prefer=None):
    if config.get("account_backend") != "supabase":
        raise RuntimeError("Shared account database is required")
    base = config["supabase_url"].rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("Invalid Supabase base URL")
    key = config["supabase_key"]
    if not isinstance(key, str) or len(key) < 20:
        raise RuntimeError("Invalid Supabase backend secret")
    url = base + "/rest/v1/" + table
    if query:
        url += "?" + urlencode(query)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"apikey": key, "Authorization": "Bearer " + key,
               "Accept": "application/json", "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=8) as response:
        body = response.read(8193)
        if len(body) > 8192:
            raise RuntimeError("Oversized account response")
        return json.loads(body) if body else []


def _telegram_label(value):
    if not isinstance(value, str):
        return ""
    return "".join(ch for ch in value if ch.isprintable())[:150]


def ensure_verified_web_user(config, uid, telegram_payload):
    """Return True only when a brand-new account was atomically inserted.

    Caller MUST verify the Telegram Widget hash beforehand. This function
    never accepts uid from an unsigned browser field, and never overwrites
    existing rows or creates duplicate trial entitlements.
    """
    if type(uid) is not int or not 0 < uid < 10**18:
        raise ValueError("Invalid verified user ID")
    if config.get("account_backend") != "supabase":
        raise RuntimeError("Web signup requires shared Supabase")
    if not isinstance(telegram_payload, dict):
        raise ValueError("Invalid authenticated Telegram profile")
    payload = {"telegram_user_id": uid}
    for field in ("first_name", "last_name", "username"):
        label = _telegram_label(telegram_payload.get(field))
        if label:
            payload[field] = label
    rows = _rest(config, "POST", "cikgulaju_users",
                 query={"on_conflict": "telegram_user_id"},
                 payload=payload, prefer="resolution=ignore-duplicates,return=representation")
    if not isinstance(rows, list):
        raise RuntimeError("Account insert confirmation missing")
    created = len(rows) == 1 and int(rows[0].get("telegram_user_id", 0)) == uid
    if len(rows) > 1 or (len(rows) == 1 and not created):
        raise RuntimeError("Unexpected account response")
    if created:
        # Durable source marker for the trusted Telegram admin notification.
        # A failed audit write must be surfaced; never invent a delivered alert.
        try:
            _rest(config, "POST", "web_direct_signups",
                  query={"on_conflict": "telegram_user_id"},
                  payload={"telegram_user_id": uid},
                  prefer="resolution=ignore-duplicates,return=minimal")
        except Exception as exc:
            print("WEB DIRECT SIGNUP audit persistence unavailable:",
                  type(exc).__name__, flush=True)
    return created


def notify_telegram_admin(uid):
    """Trusted internal call, only after a brand-new Supabase user was inserted."""
    import os
    from urllib.request import Request, urlopen
    from urllib.parse import urlsplit
    base = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "")
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    parts = urlsplit(base)
    if (parts.scheme != "https" or not parts.hostname or parts.port is not None
            or parts.username or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment or len(token) < 32):
        raise RuntimeError("Trusted Telegram API unavailable")
    body = json.dumps({"telegram_user_id": uid}).encode("utf-8")
    request = Request(base.rstrip("/") + "/internal/web-signup/v1/admin-notify",
                      data=body, method="POST", headers={
                          "Authorization": "Bearer " + token,
                          "Content-Type": "application/json",
                          "Accept": "application/json",
                      })
    with urlopen(request, timeout=10) as result:
        if result.status != 200:
            raise RuntimeError("Telegram admin notification refused")
        message = json.loads(result.read(4096))
        return message.get("notified") is True
