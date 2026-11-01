"""Server-side verification of Telegram Login Widget authentication data.

Use only after integrating a trusted server-side session and existing account lookup.
Never expose the bot token to the browser or log it.
"""
import hashlib
import hmac
import time


def verify_telegram_login(payload, bot_token, *, now=None, max_age_seconds=86400):
    """Return verified Telegram numeric user ID, or None.

    Telegram Login Widget uses SHA256(bot_token) as HMAC secret key.
    This is NOT the Telegram WebApp initData algorithm.
    """
    if not isinstance(payload, dict) or not isinstance(bot_token, str) or not bot_token:
        return None
    if not isinstance(max_age_seconds, int) or max_age_seconds <= 0:
        return None
    required = ("id", "auth_date", "hash")
    if any(not isinstance(payload.get(k), str) or not payload[k] for k in required):
        return None
    if any(not isinstance(k, str) or not isinstance(v, str) for k, v in payload.items()):
        return None
    if any(("\\r" in k or "\\n" in k or "\\r" in v or "\\n" in v) for k, v in payload.items()):
        return None
    try:
        user_id = int(payload["id"])
        auth_date = int(payload["auth_date"])
    except ValueError:
        return None
    if user_id <= 0 or auth_date <= 0:
        return None
    timestamp = int(time.time() if now is None else now)
    if auth_date > timestamp or timestamp - auth_date > max_age_seconds:
        return None
    claimed = payload["hash"]
    if len(claimed) != 64 or any(c not in "0123456789abcdefABCDEF" for c in claimed):
        return None
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()) if key != "hash")
    secret = hashlib.sha256(bot_token.encode("utf-8")).digest()
    expected = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, claimed.lower()):
        return None
    return user_id
