"""Telegram Login Widget payload verification for CikguLaju Web V1.

No Flask app imports or production route changes. The caller must create its own
server-side session after verification and configure the Telegram bot domain.
"""
import hashlib
import hmac
import time


class TelegramLoginError(ValueError):
    pass


def verify_telegram_login(payload, bot_token, *, now=None, max_age_seconds=300):
    """Verify Telegram Login Widget signed fields, returning verified identity.

    Caller must enforce one-time nonce/session CSRF protection and must not use
    the unverified Telegram ID before this function returns.
    """
    if not isinstance(payload, dict) or not isinstance(bot_token, str) or not bot_token:
        raise TelegramLoginError("invalid authentication input")
    if not isinstance(max_age_seconds, int) or max_age_seconds <= 0:
        raise TelegramLoginError("invalid authentication window")
    required = ("id", "auth_date", "hash")
    if any(k not in payload for k in required):
        raise TelegramLoginError("missing signed login fields")
    if any(not isinstance(k, str) or not isinstance(v, str) for k, v in payload.items()):
        raise TelegramLoginError("invalid signed field types")
    if any("\n" in k or "=" in k or "\x00" in k for k in payload):
        raise TelegramLoginError("invalid signed field names")
    if not payload["id"].isascii() or not payload["id"].isdigit() or int(payload["id"]) <= 0:
        raise TelegramLoginError("invalid Telegram user ID")
    if not payload["auth_date"].isascii() or not payload["auth_date"].isdigit():
        raise TelegramLoginError("invalid login timestamp")
    if len(payload["hash"]) != 64:
        raise TelegramLoginError("invalid signature")
    try:
        int(payload["hash"], 16)
    except ValueError as exc:
        raise TelegramLoginError("invalid signature") from exc
    stamp = int(payload["auth_date"])
    current = int(time.time() if now is None else now)
    if stamp > current + 30 or current - stamp > max_age_seconds:
        raise TelegramLoginError("expired or future-dated login")
    data = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()) if key != "hash")
    secret = hashlib.sha256(bot_token.encode("utf-8")).digest()
    expected = hmac.new(secret, data.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload["hash"].lower()):
        raise TelegramLoginError("invalid Telegram signature")
    return {"telegram_user_id": int(payload["id"]),
            "first_name": payload.get("first_name", ""),
            "username": payload.get("username", "")}
