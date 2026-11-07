"""Independent, authenticated Web identity ticket for Google-only staging accounts.

Legacy Telegram tickets in web_v1_sessions.py remain unchanged. These tickets
MUST NOT be used as Telegram user IDs or for privileged existing routes.
"""
import hashlib
import hmac
import secrets
import time
import uuid


def issue_google_identity_ticket(subject, secret, *, now=None):
    """Issue a short-lived signed ticket for a verified Supabase Auth UUID."""
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("Session secret is missing")
    try:
        identity = uuid.UUID(str(subject))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Invalid Supabase Auth user ID") from None
    if str(identity) != str(subject):
        raise ValueError("Noncanonical identity")
    timestamp = int(time.time() if now is None else now)
    if timestamp <= 0:
        raise ValueError("Invalid timestamp")
    nonce = secrets.token_hex(16)
    body = f"v2.google.{identity}.{timestamp}.{nonce}"
    signature = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return body + "." + signature


def verify_google_identity_ticket(ticket, secret, *, now=None, ttl_seconds=3600):
    """Return UUID string only for valid, unexpired Google tickets."""
    if not isinstance(ticket, str) or len(ticket) > 320:
        return None
    if not isinstance(secret, str) or len(secret) < 32:
        return None
    if type(ttl_seconds) is not int or ttl_seconds <= 0:
        return None
    parts = ticket.split(".")
    if len(parts) != 6 or parts[:2] != ["v2", "google"]:
        return None
    _, _, subject, issued, nonce, signature = parts
    try:
        identity = uuid.UUID(subject)
        issued_at = int(issued)
    except (ValueError, TypeError, AttributeError):
        return None
    if str(identity) != subject or issued_at <= 0 or str(issued_at) != issued:
        return None
    if len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
        return None
    if len(signature) != 64 or any(c not in "0123456789abcdef" for c in signature):
        return None
    timestamp = int(time.time() if now is None else now)
    if issued_at > timestamp or timestamp - issued_at > ttl_seconds:
        return None
    body = ".".join(parts[:-1])
    expected = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    return str(identity)
