"""Signed, expiring Web V1 session tickets.

This is a reusable primitive, NOT an enabled login route. Only issue tickets after
server-side Telegram signature verification and lookup of an existing account.
"""
import hashlib
import hmac
import secrets
import time


def issue_session_ticket(telegram_user_id, secret, *, now=None):
    if type(telegram_user_id) is not int or telegram_user_id <= 0:
        raise ValueError("invalid Telegram user ID")
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("session signing secret too short")
    issued_at = int(time.time() if now is None else now)
    nonce = secrets.token_hex(16)
    body = f"v1.{telegram_user_id}.{issued_at}.{nonce}"
    mac = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{mac}"


def verify_session_ticket(ticket, secret, *, now=None, ttl_seconds=43200):
    if not isinstance(ticket, str) or len(ticket) > 256:
        return None
    if not isinstance(secret, str) or len(secret) < 32:
        return None
    if type(ttl_seconds) is not int or ttl_seconds <= 0:
        return None
    parts = ticket.split(".")
    if len(parts) != 5 or parts[0] != "v1":
        return None
    version, uid, issued, nonce, supplied_mac = parts
    if len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
        return None
    if len(supplied_mac) != 64 or any(c not in "0123456789abcdef" for c in supplied_mac):
        return None
    try:
        user_id, issued_at = int(uid), int(issued)
    except ValueError:
        return None
    if user_id <= 0 or issued_at <= 0:
        return None
    timestamp = int(time.time() if now is None else now)
    if issued_at > timestamp or timestamp - issued_at > ttl_seconds:
        return None
    body = ".".join(parts[:-1])
    expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return user_id if hmac.compare_digest(expected, supplied_mac) else None
