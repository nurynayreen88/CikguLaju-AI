"""Signed, expiring CikguLaju Web session tickets.

v1 retains the existing 12-hour login behavior. Opt-in v2 tickets extend a
session to 14 days on a trusted personal device. Neither format contains a
password or a Supabase access/refresh token. Both are authenticated with the
same server-side signing secret; changing the opt-in flag invalidates the MAC.
"""
import hashlib
import hmac
import secrets
import time

DEFAULT_SESSION_SECONDS = 12 * 60 * 60
REMEMBER_SESSION_SECONDS = 14 * 24 * 60 * 60


def issue_session_ticket(telegram_user_id, secret, *, now=None, remember=False):
    if type(telegram_user_id) is not int or not 0 < telegram_user_id < 2**63:
        raise ValueError("invalid account user ID")
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("session signing secret too short")
    if type(remember) is not bool:
        raise ValueError("remember flag must be boolean")
    issued_at = int(time.time() if now is None else now)
    nonce = secrets.token_hex(16)
    body = (f"v2.{telegram_user_id}.{issued_at}.remember.{nonce}"
            if remember else f"v1.{telegram_user_id}.{issued_at}.{nonce}")
    mac = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{mac}"


def verify_session_ticket(ticket, secret, *, now=None, ttl_seconds=None):
    if not isinstance(ticket, str) or len(ticket) > 256:
        return None
    if not isinstance(secret, str) or len(secret) < 32:
        return None
    if ttl_seconds is not None and (type(ttl_seconds) is not int or ttl_seconds <= 0):
        return None
    parts = ticket.split(".")
    if len(parts) == 5 and parts[0] == "v1":
        _, uid, issued, nonce, supplied_mac = parts
        max_age = DEFAULT_SESSION_SECONDS
    elif len(parts) == 6 and parts[0] == "v2" and parts[3] == "remember":
        _, uid, issued, _, nonce, supplied_mac = parts
        max_age = REMEMBER_SESSION_SECONDS
    else:
        return None
    if len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
        return None
    if len(supplied_mac) != 64 or any(c not in "0123456789abcdef" for c in supplied_mac):
        return None
    try:
        user_id, issued_at = int(uid), int(issued)
    except ValueError:
        return None
    if not 0 < user_id < 2**63 or issued_at <= 0:
        return None
    timestamp = int(time.time() if now is None else now)
    if issued_at > timestamp or timestamp - issued_at > (max_age if ttl_seconds is None else min(ttl_seconds, max_age)):
        return None
    body = ".".join(parts[:-1])
    expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return user_id if hmac.compare_digest(expected, supplied_mac) else None
