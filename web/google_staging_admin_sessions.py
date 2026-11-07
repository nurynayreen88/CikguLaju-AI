"""Short-lived staging ADMIN sessions isolated from Google and legacy Telegram Web."""
import hashlib
import hmac
import secrets
import time


def issue_staging_admin_ticket(verified_telegram_id, secret, *, now=None):
    if type(verified_telegram_id) is not int or not 0 < verified_telegram_id < 10**18:
        raise ValueError("Invalid verified Telegram identity")
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("Invalid staging session secret")
    stamp = int(time.time() if now is None else now)
    if stamp <= 0:
        raise ValueError("Invalid timestamp")
    nonce = secrets.token_hex(16)
    body = f"v2a.admin.{verified_telegram_id}.{stamp}.{nonce}"
    mac = hmac.new(secret.encode("utf-8"),body.encode("ascii"),hashlib.sha256).hexdigest()
    return body + "." + mac


def verify_staging_admin_ticket(ticket, secret, *, now=None, ttl_seconds=3600):
    if not isinstance(ticket, str) or len(ticket) > 256:
        return None
    if not isinstance(secret, str) or len(secret) < 32:
        return None
    if type(ttl_seconds) is not int or not 0 < ttl_seconds <= 3600:
        return None
    parts = ticket.split(".")
    if len(parts) != 6 or parts[:2] != ["v2a", "admin"]:
        return None
    _, _, id_text, stamp, nonce, mac = parts
    if len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
        return None
    if len(mac) != 64 or any(c not in "0123456789abcdef" for c in mac):
        return None
    try:
        uid = int(id_text)
        issued_at = int(stamp)
    except ValueError:
        return None
    if uid <= 0 or uid >= 10**18 or str(uid) != id_text or issued_at <= 0 or str(issued_at) != stamp:
        return None
    timestamp = int(time.time() if now is None else now)
    if timestamp < issued_at or timestamp - issued_at > ttl_seconds:
        return None
    expected = hmac.new(secret.encode(), ".".join(parts[:-1]).encode("ascii"), hashlib.sha256).hexdigest()
    return uid if hmac.compare_digest(expected, mac) else None
