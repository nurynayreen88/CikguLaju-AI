"""Production canonical Google principal store (opt-in migration, NOT activated).

One real CikguLaju Supabase project is the authority for legacy Telegram
accounts and new Google-only UUID principals. OAuth provider subject is the
stable identity. A verified email is only the visible sign-in label.

Never create a Telegram ID, infer paid status from email, or use a staging
account/entitlement as production authorization.
"""
import json
import uuid
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from web.google_account_store import verified_google_email

PROD_SUPABASE = "https://soxakntcanbycjoygrcx.supabase.co"


class CanonicalAccountUnavailable(RuntimeError):
    pass


def _uuid(value):
    try:
        canonical = str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise CanonicalAccountUnavailable("Verified account UUID required") from None
    if canonical != value:
        raise CanonicalAccountUnavailable("Noncanonical identity")
    return canonical


def _headers(cfg):
    if (not isinstance(cfg, dict) or
            cfg.get("supabase_url", "").rstrip("/") != PROD_SUPABASE):
        raise CanonicalAccountUnavailable("Production account source required")
    key = cfg.get("supabase_key", "")
    if not isinstance(key, str) or len(key) < 24 or key.startswith("sb_publishable_"):
        raise CanonicalAccountUnavailable("Private production account key required")
    headers = {"apikey": key, "Accept": "application/json"}
    # New sb_secret_ keys are NOT JWTs: do not pass them as Bearer.
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    return headers


def _read_json(request_obj, *, limit=4096):
    try:
        with urlopen(request_obj, timeout=8) as response:
            raw = response.read(limit + 1)
            if response.status not in (200, 201) or len(raw) > limit:
                raise CanonicalAccountUnavailable("Canonical account reply invalid")
        return json.loads(raw)
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        raise CanonicalAccountUnavailable("Canonical account source unavailable") from None


def register_verified_google_principal(cfg, server_verified_auth_user):
    """Server MUST first exchange OAuth PKCE and GET /auth/v1/user.

    Calls the separate service_role-only SQL RPC in the SAME production DB as
    Telegram. The RPC is disabled unless the additive canonical migration is
    reviewed and applied; the Web route must remain disabled until then.
    """
    if not isinstance(server_verified_auth_user, dict):
        raise CanonicalAccountUnavailable("Verified OAuth user required")
    try:
        subject = _uuid(server_verified_auth_user["id"])
        email = verified_google_email(server_verified_auth_user)
    except (KeyError, ValueError, TypeError, CanonicalAccountUnavailable):
        raise CanonicalAccountUnavailable("Confirmed Google provider identity required") from None
    headers = _headers(cfg)
    req = Request(
        PROD_SUPABASE + "/rest/v1/rpc/ensure_native_google_web_principal",
        data=json.dumps({"p_auth_subject": subject,
                         "p_verified_email": email}).encode("utf-8"),
        method="POST", headers={**headers, "Content-Type": "application/json"})
    account_id = _read_json(req, limit=1024)
    return _uuid(account_id)


def read_google_principal(cfg, account_id):
    """Revalidate the signed browser's UUID against the private SAME DB."""
    account_id = _uuid(account_id)
    headers = _headers(cfg)
    def query(table, options):
        req = Request(PROD_SUPABASE + "/rest/v1/" + table + "?" +
                      urlencode(options), method="GET", headers=headers)
        return _read_json(req)

    principals = query("cikgulaju_web_principals", {
        "select": "id,google_login_email,legacy_telegram_user_id,google_only_trial_remaining",
        "id": "eq." + account_id, "limit": "2",
    })
    if not isinstance(principals, list) or len(principals) != 1:
        raise CanonicalAccountUnavailable("Canonical principal not found")
    p = principals[0]
    if not isinstance(p, dict) or p.get("id") != account_id:
        raise CanonicalAccountUnavailable("Canonical principal mismatch")

    identities = query("cikgulaju_web_google_identities", {
        "select": "auth_subject,principal_id",
        "principal_id": "eq." + account_id, "limit": "2",
    })
    if (not isinstance(identities, list) or len(identities) != 1 or
            not isinstance(identities[0], dict) or
            identities[0].get("principal_id") != account_id):
        raise CanonicalAccountUnavailable("Google principal proof no longer exists")
    _uuid(identities[0].get("auth_subject"))

    uid, remaining = p.get("legacy_telegram_user_id"), p.get("google_only_trial_remaining")
    email = p.get("google_login_email")
    if not isinstance(email, str) or not 3 <= len(email) <= 254 or email != email.lower():
        raise CanonicalAccountUnavailable("Verified login email unavailable")
    if uid is None:
        if type(remaining) is not int or not 0 <= remaining <= 10:
            raise CanonicalAccountUnavailable("Google-only trial balance unavailable")
    elif (type(uid) is not int or uid <= 0 or remaining is not None):
        raise CanonicalAccountUnavailable("Linked account trial source inconsistent")
    return {"account_id": account_id, "login_id": email,
            "login_provider": "google", "legacy_telegram_user_id": uid,
            "google_only_trial_remaining": remaining}


def canonical_rph_access(cfg, principal):
    """Read from original Telegram rights for linked users, Google quota only
    for standalone accounts. Never merge two trial allowances.
    """
    if not isinstance(principal, dict):
        raise CanonicalAccountUnavailable("Verified canonical principal required")
    account_id = principal.get("account_id")
    _uuid(account_id)
    uid = principal.get("legacy_telegram_user_id")
    if uid is None:
        rem = principal.get("google_only_trial_remaining")
        if type(rem) is not int or not 0 <= rem <= 10:
            raise CanonicalAccountUnavailable("Google trial unavailable")
        return {"rph_access_mode": "trial" if rem else "exhausted",
                "rph_trial_remaining": rem, "account_id": account_id}
    if type(uid) is not int or uid <= 0:
        raise CanonicalAccountUnavailable("Legacy account ID invalid")
    from web_v1_supabase_account_adapter import lookup_existing_supabase_account
    from web.english_rpt_2027_http import _has_paid_access
    _headers(cfg)
    # Direct same-production-DB backend lookup: no Render-to-Render bridge.
    source = lookup_existing_supabase_account(
        PROD_SUPABASE, cfg["supabase_key"], uid)
    if (not isinstance(source, dict) or source.get("authenticated") is not True
            or source.get("telegram_user_id") != uid):
        raise CanonicalAccountUnavailable("Linked Telegram account unavailable")
    paid = _has_paid_access(source)
    rem = source.get("free_remaining")
    if type(rem) is not int or not 0 <= rem <= 10:
        raise CanonicalAccountUnavailable("Linked Telegram balance unavailable")
    return {"rph_access_mode": "paid" if paid else
            ("trial" if rem else "exhausted"),
            "rph_trial_remaining": rem, "account_id": account_id}
