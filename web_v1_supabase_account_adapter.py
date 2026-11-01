"""Read-only existing Telegram account lookup via server-side Supabase REST API."""
import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def lookup_existing_supabase_account(url, secret_key, telegram_id):
    if type(telegram_id) is not int or telegram_id <= 0:
        return None
    if not url.startswith("https://") or not secret_key:
        raise ValueError("Supabase server configuration missing")

    def select(table, columns, filters):
        query = urlencode({"select": columns, **filters})
        request = Request(
            url.rstrip("/") + "/rest/v1/" + table + "?" + query,
            headers={"apikey": secret_key, "Authorization": "Bearer " + secret_key,
                     "Accept": "application/json"},
        )
        with urlopen(request, timeout=6) as response:
            return json.load(response)

    uid = str(telegram_id)
    users = select("cikgulaju_users", "telegram_user_id,trial_remaining", {"telegram_user_id": "eq." + uid, "limit": "2"})
    if len(users) != 1 or int(users[0]["telegram_user_id"]) != telegram_id:
        return None
    credits = users[0]["trial_remaining"]
    if type(credits) is not int or credits < 0:
        raise ValueError("Invalid trial balance")

    lifetime = select("pioneer_entitlements", "entitlement,revoked_at", {"telegram_user_id": "eq." + uid, "limit": "100"})
    has_lifetime = any(row.get("revoked_at") is None and row.get("entitlement") in ("lifetime", "rakan_pembangun", "pioneer_lifetime") for row in lifetime)
    subscriptions = select("subscriptions", "status,expires_at", {"telegram_user_id": "eq." + uid, "limit": "100"})
    now = datetime.now(timezone.utc)
    expiry = None
    for row in subscriptions:
        if row.get("status") != "active" or not row.get("expires_at"):
            continue
        try:
            candidate = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if candidate.tzinfo is None:
            continue
        if candidate > now and (expiry is None or candidate > expiry):
            expiry = candidate
    return {"authenticated": True, "telegram_user_id": telegram_id,
            "rakan_pembangun": has_lifetime, "vip_until": expiry.date().isoformat() if expiry else None,
            "free_remaining": min(credits, 10)}
