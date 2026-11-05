"""Isolated one-time pairing challenge primitives; no public routes or Telegram bot integration.

Storage must be a shared persistent, atomic backend before enabling in production.
Never put a session ticket or Telegram token in the QR payload.
"""
import hashlib
import hmac
import secrets
import time


def new_pairing_challenge(*, now=None, ttl_seconds=180):
    """Return (opaque QR challenge, SHA256 storage key, expiry timestamp)."""
    if type(ttl_seconds) is not int or not 30 <= ttl_seconds <= 300:
        raise ValueError("invalid pairing lifetime")
    timestamp = int(time.time() if now is None else now)
    if timestamp <= 0:
        raise ValueError("invalid time")
    challenge = secrets.token_urlsafe(32)
    key = hashlib.sha256(challenge.encode("ascii")).hexdigest()
    return challenge, key, timestamp + ttl_seconds


def challenge_storage_key(challenge):
    """Validate a challenge and return its hashed key (never persist raw QR token)."""
    if not isinstance(challenge, str) or not 40 <= len(challenge) <= 64:
        return None
    if any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in challenge):
        return None
    return hashlib.sha256(challenge.encode("ascii")).hexdigest()


def valid_pairing_confirmation(challenge, stored_hash, expires_at, telegram_user_id, *, now=None):
    """Check candidate only. Atomic consume and Telegram update verification are caller duties."""
    candidate = challenge_storage_key(challenge)
    if candidate is None or not isinstance(stored_hash, str) or len(stored_hash) != 64:
        return False
    if type(telegram_user_id) is not int or telegram_user_id <= 0:
        return False
    if type(expires_at) is not int:
        return False
    timestamp = int(time.time() if now is None else now)
    return timestamp < expires_at and hmac.compare_digest(candidate, stored_hash)
