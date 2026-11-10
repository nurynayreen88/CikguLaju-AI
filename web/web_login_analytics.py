"""Server-side, best-effort Web login activity recording.

Only call after Telegram Widget HMAC verification AND a successful lookup of
the same registered account. This never grants access or changes user credits.
The existing Supabase web_login_events table is the durable event source.
"""
import json
from urllib.parse import urlsplit
from urllib.request import Request, HTTPSHandler, HTTPRedirectHandler, build_opener


class _NoRedirect(HTTPRedirectHandler):
    """Do not forward server credentials to a redirect destination."""

    def redirect_request(self, request, response, code, message, headers, newurl):
        return None


def record_verified_web_login(config, uid, *, opener=None):
    """Write one login event, returning True only after the REST write succeeds.

    The caller deliberately treats logging failures as non-fatal. A session
    is never granted by this helper, and it does not accept browser user IDs.
    """
    if not isinstance(config, dict) or config.get("account_backend") != "supabase":
        return False
    if type(uid) is not int or not 0 < uid < 10**18:
        raise ValueError("Expected a verified Telegram user ID")

    base = config.get("supabase_url", "")
    key = config.get("supabase_key", "")
    if not isinstance(base, str) or not isinstance(key, str) or len(key) < 20:
        raise ValueError("Analytics database is not configured")
    parsed = urlsplit(base)
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.port is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Invalid analytics database origin")

    headers = {"apikey": key, "Content-Type": "application/json",
               "Accept": "application/json", "Prefer": "return=minimal"}
    # Modern opaque sb_secret_ keys are API keys, not bearer JWTs.
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    body = json.dumps({"telegram_user_id": uid, "source": "web"},
                      separators=(",", ":")).encode("utf-8")
    req = Request(base.rstrip("/") + "/rest/v1/web_login_events",
                  data=body, headers=headers, method="POST")
    client = opener if opener is not None else build_opener(HTTPSHandler(), _NoRedirect())
    with client.open(req, timeout=3) as response:
        if response.status not in (200, 201, 204):
            raise RuntimeError("Login event storage rejected the write")
    return True
