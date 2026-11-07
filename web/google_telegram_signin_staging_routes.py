"""Telegram Login Widget -> existing linked canonical account, staging only.

A Telegram proof cannot create/merge accounts, bypass Google OAuth, or grant
production Telegram entitlements. Both providers read one staging account row.
Separate signed cookie; no impersonation of the Google OAuth session.
"""
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request

from flask import Blueprint, jsonify, make_response, request, send_file

from web.google_account_store import google_staging_account_profile, GoogleAccountUnavailable
from web.google_telegram_link_staging_routes import (
    _link_config, _read_json, _same_origin, StagingLinkUnavailable,
)
from web.google_staging_service_auth import staging_service_headers
from web_v1_telegram_login import verify_telegram_login

bp = Blueprint("staging_linked_telegram_login", __name__)
TELEGRAM_COOKIE = "cikgulaju_linked_telegram_staging_ticket"
TICKET_TTL = 3600
MAX_BODY = 8192


def _issue_ticket(uid, secret, *, now=None):
    if (type(uid) is not int or not 0 < uid <= 9223372036854775807
            or not isinstance(secret, str) or len(secret) < 32):
        raise ValueError("Invalid verified Telegram staging session")
    at = int(time.time() if now is None else now)
    if at <= 0:
        raise ValueError("Invalid timestamp")
    body = f"v1.tgteacher.{uid}.{at}.{secrets.token_hex(16)}"
    mac = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return body + "." + mac


def _verify_ticket(ticket, secret, *, now=None):
    if (not isinstance(ticket, str) or len(ticket) > 256
            or not isinstance(secret, str) or len(secret) < 32):
        return None
    p = ticket.split(".")
    if len(p) != 6 or p[:2] != ["v1", "tgteacher"]:
        return None
    _, _, raw_uid, issued, nonce, supplied = p
    if (not raw_uid.isascii() or not raw_uid.isdecimal()
            or not issued.isascii() or not issued.isdecimal()
            or not (len(nonce) == 32 and all(x in "0123456789abcdef" for x in nonce))
            or not (len(supplied) == 64 and all(x in "0123456789abcdef" for x in supplied))):
        return None
    try:
        uid, at = int(raw_uid), int(issued)
    except ValueError:
        return None
    now_at = int(time.time() if now is None else now)
    if (not 0 < uid <= 9223372036854775807 or str(uid) != raw_uid
            or at <= 0 or str(at) != issued or at > now_at
            or now_at - at > TICKET_TTL):
        return None
    body = ".".join(p[:-1])
    expected = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return uid if hmac.compare_digest(expected, supplied) else None


def _linked_account(cfg, telegram_uid):
    """Fail closed unless both identity and legacy map match exactly."""
    if type(telegram_uid) is not int or telegram_uid <= 0:
        raise ValueError("Verified Telegram ID required")
    base = cfg["supabase_url"].rstrip("/") + "/rest/v1/"
    headers = staging_service_headers(cfg["staging_service_key"])

    def rows(table, fields):
        url = base + table + "?" + urlencode({**fields, "limit": "2"})
        result = _read_json(Request(url, headers=headers, method="GET"))
        if not isinstance(result, list) or len(result) > 1:
            raise StagingLinkUnavailable("Ambiguous identity mapping")
        return result

    matches = rows("web_account_identities", {
        "select": "account_id,subject", "provider": "eq.telegram",
        "subject": "eq." + str(telegram_uid),
    })
    if not matches:
        return None  # Unlinked Telegram identities must never auto-create an account.
    account_id = matches[0].get("account_id")
    if (not isinstance(account_id, str)
            or matches[0].get("subject") != str(telegram_uid)):
        raise StagingLinkUnavailable("Inconsistent linked identity")
    import uuid
    try:
        canonical = str(uuid.UUID(account_id))
    except (TypeError, ValueError, AttributeError):
        raise StagingLinkUnavailable("Invalid canonical identity") from None
    if canonical != account_id:
        raise StagingLinkUnavailable("Noncanonical identity")
    accounts = rows("web_accounts", {
        "select": "id,legacy_telegram_user_id", "id": "eq." + account_id,
    })
    google = rows("web_account_identities", {
        "select": "account_id", "provider": "eq.google",
        "account_id": "eq." + account_id,
    })
    if (len(accounts) != 1 or accounts[0].get("id") != account_id
            or type(accounts[0].get("legacy_telegram_user_id")) is not int
            or accounts[0]["legacy_telegram_user_id"] != telegram_uid
            or len(google) != 1 or google[0].get("account_id") != account_id):
        raise StagingLinkUnavailable("Unconfirmed dual-provider account")
    return account_id


@bp.after_request
def protect(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/google-staging-telegram")
def telegram_login_page():
    if _link_config() is None:
        return jsonify({"error": "Login Telegram staging belum tersedia"}), 503
    return make_response(send_file(
        Path(__file__).with_name("google_staging_telegram.html"),
        mimetype="text/html", max_age=0))


@bp.get("/api/auth/staging/telegram/bot")
def telegram_login_bot():
    pair = _link_config()
    if pair is None:
        return jsonify({"error": "Bot Telegram staging belum tersedia"}), 503
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    return jsonify({"bot_username": pair[1][1], "staging_only": True,
                    "linked_accounts_only": True})


@bp.post("/api/auth/staging/telegram/login")
def telegram_login():
    pair = _link_config()
    if pair is None:
        return jsonify({"error": "Login Telegram staging belum tersedia"}), 503
    cfg, bot = pair
    if not _same_origin(cfg):
        return jsonify({"error": "Permintaan rentas laman ditolak"}), 403
    if (not request.is_json or request.content_length is None
            or request.content_length > MAX_BODY):
        return jsonify({"error": "Permintaan tidak sah"}), 400
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"telegram_auth"}:
        return jsonify({"error": "Bukti Telegram diperlukan"}), 400
    uid = verify_telegram_login(body["telegram_auth"], bot[0], max_age_seconds=120)
    if type(uid) is not int:
        return jsonify({"error": "Pengesahan Telegram tidak sah atau tamat"}), 403
    try:
        account_id = _linked_account(cfg, uid)
        if account_id is None:
            return jsonify({"error": "Pautkan Telegram melalui login Google dahulu"}), 403
        profile = google_staging_account_profile(cfg, account_id)
    except (StagingLinkUnavailable, GoogleAccountUnavailable, ValueError, KeyError, TypeError):
        return jsonify({"error": "Akaun staging belum boleh disahkan"}), 503
    answer = jsonify({"authenticated": True, "provider": "telegram",
                     "linked": True, "staging_only": True,
                     "trial_remaining": profile["trial_remaining"],
                     "entitlements_shared": False})
    answer.set_cookie(TELEGRAM_COOKIE, _issue_ticket(uid, cfg["secret"]),
                      secure=True, httponly=True, samesite="Lax",
                      max_age=TICKET_TTL, path="/")
    return answer


@bp.get("/api/auth/staging/telegram/profile")
def telegram_profile():
    pair = _link_config()
    if pair is None:
        return jsonify({"error": "Login Telegram staging belum tersedia"}), 503
    cfg = pair[0]
    uid = _verify_ticket(request.cookies.get(TELEGRAM_COOKIE), cfg["secret"])
    if uid is None or request.args:
        return jsonify({"error": "Sesi Telegram diperlukan"}), 401
    try:
        account_id = _linked_account(cfg, uid)
        if account_id is None:
            return jsonify({"error": "Pemadanan tidak lagi tersedia"}), 401
        profile = google_staging_account_profile(cfg, account_id)
    except (StagingLinkUnavailable, GoogleAccountUnavailable, ValueError, KeyError, TypeError):
        return jsonify({"error": "Profil staging belum boleh disahkan"}), 503
    return jsonify({"authenticated": True, "provider": "telegram",
                    "linked": True, "staging_only": True,
                    "display_name": profile["display_name"],
                    "trial_remaining": profile["trial_remaining"],
                    "entitlements_shared": False, "real_payments_enabled": False})


@bp.post("/api/auth/staging/telegram/logout")
def telegram_logout():
    pair = _link_config()
    if pair is None:
        return jsonify({"error": "Login Telegram staging belum tersedia"}), 503
    if not _same_origin(pair[0]):
        return jsonify({"error": "Permintaan rentas laman ditolak"}), 403
    response = jsonify({"authenticated": False})
    response.delete_cookie(TELEGRAM_COOKIE, secure=True, httponly=True,
                           samesite="Lax", path="/")
    return response
