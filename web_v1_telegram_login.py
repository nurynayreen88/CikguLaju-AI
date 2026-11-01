"""Server-side verification of Telegram Login Widget authentication data."""
import hashlib
import hmac
import time


def verify_telegram_login(payload, bot_token, *, now=None, max_age_seconds=86400):
    if not isinstance(payload, dict) or not isinstance(bot_token, str) or not bot_token:
        return None
    if type(max_age_seconds) is not int or max_age_seconds <= 0:
        return None
    if len(payload) > 20 or any(not isinstance(k, str) for k in payload):
        return None
    if any(type(v) not in (str, int) for v in payload.values()):
        return None
    normalized = {k: str(v) for k, v in payload.items()}
    if any(len(k) > 64 or len(v) > 4096 or "\\r" in k or "\\n" in k or "\\r" in v or "\\n" in v for k, v in normalized.items()):
        return None
    if not all(k in normalized and normalized[k] for k in ("id", "auth_date", "hash")):
        return None
    try:
        user_id, auth_date = int(normalized["id"]), int(normalized["auth_date"])
    except ValueError:
        return None
    if user_id <= 0 or auth_date <= 0 or str(user_id) != normalized["id"] or str(auth_date) != normalized["auth_date"]:
        return None
    timestamp = int(time.time() if now is None else now)
    if auth_date > timestamp or timestamp - auth_date > max_age_seconds:
        return None
    claimed = normalized["hash"]
    if len(claimed) != 64 or any(c not in "0123456789abcdefABCDEF" for c in claimed):
        return None
    check_string = "\\n".join(f"{key}={value}" for key, value in sorted(normalized.items()) if key != "hash")
    secret = hashlib.sha256(bot_token.encode("utf-8")).digest()
    expected = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return user_id if hmac.compare_digest(expected, claimed.lower()) else None
