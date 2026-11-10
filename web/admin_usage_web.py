"""Private, read-only Web admin usage dashboard backed by Supabase.

The Telegram Widget session and an explicit server-side admin allowlist are
required. Only aggregate statistics leave this endpoint; not teacher identities.
No writes to accounts, credit balances, RPH or paid entitlement tables.
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPSHandler, build_opener
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, jsonify, request

from web_v1_telegram_auth_routes import COOKIE, _config, _lookup
from web_v1_sessions import verify_session_ticket
from web.web_login_analytics import _NoRedirect

bp = Blueprint("cikgulaju_admin_usage_web", __name__)
MYT = ZoneInfo("Asia/Kuala_Lumpur")
PAGE_SIZE = 500
MAX_LOGIN_EVENTS = 10000


def allowed_admin_ids(environ=None):
    """Explicit Web admin list, fail closed when missing or malformed.

    Never infer privileged access from a payment, pioneer entitlement,
    profile field, browser parameter, or a Telegram ID appearing in a log.
    """
    source = os.environ if environ is None else environ
    raw = source.get("CIKGULAJU_WEB_ADMIN_IDS", "")
    if not isinstance(raw, str) or not raw.strip():
        return set()
    parts = [part.strip() for part in raw.split(",")]
    if not parts or any(not re.fullmatch(r"[1-9][0-9]{0,17}", part) for part in parts):
        return set()
    return {int(part) for part in parts}


def _api_config(conf):
    if not isinstance(conf, dict) or conf.get("account_backend") != "supabase":
        raise RuntimeError("Authoritative admin data source unavailable")
    base, key = conf.get("supabase_url", ""), conf.get("supabase_key", "")
    if not isinstance(base, str) or not isinstance(key, str) or len(key) < 20:
        raise RuntimeError("Admin data source unavailable")
    parsed = urlsplit(base)
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.port is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise RuntimeError("Invalid trusted data source")
    headers = {"apikey": key, "Accept": "application/json"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    return base.rstrip("/"), headers


def _fetch(conf, table, query, *, count=False, opener=None):
    """Restrict requests to known tables; do not accept client-provided SQL."""
    tables = {"web_login_events", "cikgulaju_users",
              "pioneer_entitlements", "trial_ledger", "admin_rph_deliveries"}
    if table not in tables:
        raise ValueError("Unsupported admin statistics source")
    base, headers = _api_config(conf)
    headers = dict(headers)
    headers["Prefer"] = "count=exact" if count else "return=representation"
    if count:
        headers["Range-Unit"] = "items"
        headers["Range"] = "0-0"
    url = base + "/rest/v1/" + table + "?" + urlencode(query)
    req = Request(url, headers=headers, method="HEAD" if count else "GET")
    client = opener if opener is not None else build_opener(HTTPSHandler(), _NoRedirect())
    with client.open(req, timeout=8) as resp:
        if resp.status not in (200, 206):
            raise RuntimeError("Statistics source rejected the request")
        if count:
            value = resp.headers.get("Content-Range", "").split("/")[-1]
            if not value.isdecimal():
                raise RuntimeError("Exact database count unavailable")
            return int(value)
        raw = resp.read(262145)
        if len(raw) > 262144:
            raise RuntimeError("Statistics page too large")
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise RuntimeError("Invalid statistics response")
    return rows


def _oldest_login(conf, opener=None):
    rows = _fetch(conf, "web_login_events", {
        "select": "logged_in_at", "source": "eq.web", "order": "logged_in_at.asc", "limit": "1"
    }, opener=opener)
    return _parse_utc(rows[0]["logged_in_at"]) if rows else None


def _parse_utc(raw):
    if not isinstance(raw, str):
        raise ValueError("Missing event time")
    stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Event time must contain offset")
    return stamp.astimezone(timezone.utc)


def _login_metrics(conf, now, opener=None):
    """Count distinct accounts, not repeated login clicks.

    If the 30-day event set is above a bounded read limit, report unavailable
    rather than pretending the first page is the complete result.
    """
    today_local = now.astimezone(MYT).replace(hour=0, minute=0, second=0, microsecond=0)
    starts = {
        "today": today_local.astimezone(timezone.utc),
        "last_7_days": now - timedelta(days=7),
        "last_30_days": now - timedelta(days=30),
    }
    oldest = _oldest_login(conf, opener)
    if oldest is None:
        return {"users_today": None, "users_7d": None, "users_30d": None,
                "tracking_status": "not_started",
                "tracking_since": None, "coverage": {}}

    since = min(starts.values())
    total = _fetch(conf, "web_login_events", {
        "select": "id", "source": "eq.web", "logged_in_at": "gte." + since.isoformat(), "limit": "1",
    }, count=True, opener=opener)
    if total > MAX_LOGIN_EVENTS:
        return {"users_today": None, "users_7d": None, "users_30d": None,
                "tracking_status": "event_limit",
                "tracking_since": oldest.isoformat(), "coverage": {}}

    unique = {key: set() for key in starts}
    for offset in range(0, total, PAGE_SIZE):
        rows = _fetch(conf, "web_login_events", {
            "select": "telegram_user_id,logged_in_at", "source": "eq.web",
            "logged_in_at": "gte." + since.isoformat(),
            "order": "logged_in_at.asc,id.asc",
            "limit": str(PAGE_SIZE), "offset": str(offset),
        }, opener=opener)
        if len(rows) != min(PAGE_SIZE, total - offset):
            raise RuntimeError("Incomplete login event page; refuse partial totals")
        for row in rows:
            uid = row.get("telegram_user_id")
            at = _parse_utc(row.get("logged_in_at"))
            if type(uid) is not int or uid <= 0:
                raise RuntimeError("Invalid recorded login identity")
            if at > now:
                continue  # Skip future-dated entries, never invent usage.
            for window, start in starts.items():
                if at >= start:
                    unique[window].add(uid)

    coverage = {window: oldest <= start for window, start in starts.items()}
    return {
        "users_today": len(unique["today"]),
        "users_7d": len(unique["last_7_days"]),
        "users_30d": len(unique["last_30_days"]),
        "tracking_status": "complete_since_first_event"
                           if all(coverage.values()) else "partial_history",
        "tracking_since": oldest.isoformat(),
        "coverage": coverage,
    }


def summarize_admin_usage(conf, *, now=None, opener=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Summary time must be timezone-aware")
    now = now.astimezone(timezone.utc)
    users = _fetch(conf, "cikgulaju_users", {
        "select": "telegram_user_id", "limit": "1"
    }, count=True, opener=opener)
    pioneers = _fetch(conf, "pioneer_entitlements", {
        "select": "telegram_user_id", "revoked_at": "is.null", "limit": "1"
    }, count=True, opener=opener)
    credit_usage = _fetch(conf, "trial_ledger", {
        "select": "id", "amount": "lt.0", "limit": "1"
    }, count=True, opener=opener)
    confirmed = _fetch(conf, "admin_rph_deliveries", {
        "select": "telegram_user_id", "limit": "1"
    }, count=True, opener=opener)
    login = _login_metrics(conf, now, opener=opener)
    return {
        "registered_users": users, "rakan_pembangun": pioneers,
        "trial_credit_debits": credit_usage,
        # The historic delivery ledger is not backfilled. Zero rows MUST NOT
        # be represented as zero generated RPH across the whole product.
        "confirmed_rph_records": confirmed if confirmed > 0 else None,
        "rph_coverage": "partial" if confirmed > 0 else "not_instrumented",
        "time_zone": "Asia/Kuala_Lumpur",
        "generated_at": now.isoformat(),
        **login,
    }


@bp.after_request
def _private_headers(resp):
    resp.headers["Cache-Control"] = "no-store, private"
    resp.headers["Vary"] = "Cookie"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@bp.get("/api/web/admin/usage")
def admin_usage():
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    conf = _config()
    if conf is None:
        return jsonify({"error": "Sambungan akaun belum tersedia"}), 503
    uid = verify_session_ticket(
        request.cookies.get(COOKIE), conf["CIKGULAJU_WEB_SESSION_SECRET"])
    if type(uid) is not int or uid <= 0:
        return jsonify({"error": "Sila log masuk"}), 401
    # Explicit allowlist first, then verify account still exists.
    if uid not in allowed_admin_ids():
        return jsonify({"error": "Akses admin diperlukan"}), 403
    if conf.get("account_backend") != "supabase":
        return jsonify({"error": "Sumber analisis belum tersedia"}), 503
    try:
        account = _lookup(conf, uid)
        if not account or account.get("telegram_user_id") != uid:
            return jsonify({"error": "Akaun admin tidak disahkan"}), 403
        return jsonify(summarize_admin_usage(conf))
    except Exception:
        current_app.logger.exception("Private admin usage summary unavailable")
        return jsonify({"error": "Analisis belum dapat dimuatkan"}), 503
