"""Account mapping for Google-only staging logins.

Input MUST come from /auth/v1/user after verifying a PKCE Google callback.
This module never accepts browser-provided user IDs, emails, or Telegram IDs.
Only a separate staging Supabase instance with the proposed migration may run
this write; production CikguLaju account tables are not accessed.
"""
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class GoogleAccountUnavailable(RuntimeError):
    pass


def ensure_google_staging_account(config, verified_auth_uuid):
    try:
        subject = str(uuid.UUID(verified_auth_uuid))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Invalid verified Auth identity") from None
    if subject != verified_auth_uuid:
        raise ValueError("Noncanonical Auth identity")
    key = config.get("staging_service_key", "")
    if not isinstance(key, str) or len(key) < 24:
        raise GoogleAccountUnavailable("Private staging account backend unavailable")
    endpoint = config["supabase_url"].rstrip("/") + "/rest/v1/rpc/ensure_google_web_account"
    req = Request(endpoint, data=json.dumps({"p_auth_subject": subject}).encode(),
                  method="POST", headers={
                      "apikey": key, "Authorization": "Bearer " + key,
                      "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=8) as res:
            raw = res.read(1025)
            if res.status != 200 or len(raw) > 1024:
                raise GoogleAccountUnavailable("Staging account response unavailable")
        account = json.loads(raw)
        canonical_id = str(uuid.UUID(account))
        if canonical_id != account:
            raise GoogleAccountUnavailable("Noncanonical account identity")
        return canonical_id
    except (HTTPError, URLError, OSError, KeyError, ValueError, TypeError, AttributeError):
        raise GoogleAccountUnavailable("Staging account mapping unavailable") from None
