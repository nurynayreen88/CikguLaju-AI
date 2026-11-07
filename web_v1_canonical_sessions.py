"""Canonical Google Web account sessions, independent of legacy Telegram tickets.

The server signs only a previously verified production account UUID. Browser
email addresses, raw OAuth tokens, and Telegram numeric IDs never become session
subjects. A v2 Google cookie cannot pass the v1 Telegram verification function.
"""
import hashlib
import hmac
import secrets
import time
import uuid

COOKIE = "cikgulaju_web_google_principal_session"
MAX_AGE = 43200


def _uuid(value):
    if not isinstance(value, str):
        raise ValueError("Canonical account UUID required")
    try:
        parsed = str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid canonical account UUID") from None
    if parsed != value:
        raise ValueError("Noncanonical account UUID")
    return parsed


def issue_google_principal_ticket(account_id, secret, *, now=None):
    account_id = _uuid(account_id)
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("Session secret too short")
    at = int(time.time() if now is None else now)
    if at <= 0:
        raise ValueError("Invalid timestamp")
    body = f"v2.google.{account_id}.{at}.{secrets.token_hex(16)}"
    mac = hmac.new(secret.encode("utf-8"), body.encode("ascii"),
                   hashlib.sha256).hexdigest()
    return body + "." + mac


def verify_google_principal_ticket(ticket, secret, *, now=None, max_age=MAX_AGE):
    if (not isinstance(ticket, str) or len(ticket) > 300 or
            not isinstance(secret, str) or len(secret) < 32 or
            type(max_age) is not int or max_age <= 0):
        return None
    p = ticket.split(".")
    if len(p) != 6 or p[:2] != ["v2", "google"]:
        return None
    try:
        account = _uuid(p[2])
        at = int(p[3])
    except (TypeError, ValueError, AttributeError):
        return None
    now_at = int(time.time() if now is None else now)
    if (at <= 0 or str(at) != p[3] or at > now_at or
            now_at - at > max_age or
            len(p[4]) != 32 or any(c not in "0123456789abcdef" for c in p[4]) or
            len(p[5]) != 64 or any(c not in "0123456789abcdef" for c in p[5])):
        return None
    body = ".".join(p[:-1])
    expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"),
                        hashlib.sha256).hexdigest()
    return account if hmac.compare_digest(expected, p[5]) else None
