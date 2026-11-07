"""Opt-in, verified Google + Telegram account association in isolated staging.

This links *identities only*. Production Telegram subscriptions, quotas,
referrals and admin grants remain authoritative and untouched. The signed
Telegram Login Widget proof comes from the dedicated staging bot; a browser
Telegram ID, name or Google email alone is never linking authorization.
"""
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, make_response, request, send_file

from web.google_auth_staging_routes import _enabled_config
from web.google_web_catalog_staging import _actor
from web.google_staging_admin_auth_routes import _bot as _staging_admin_bot
from web.google_staging_service_auth import staging_service_headers
from web.provider_neutral_web_identity import (
    from_verified_telegram_account, may_link_accounts)
from web_v1_telegram_login import verify_telegram_login

bp = Blueprint("google_telegram_link_staging", __name__)
MAX_BODY = 8192


class StagingLinkUnavailable(RuntimeError):
    pass


def _link_bot():
    # A separate staging bot is preferred. The existing staging admin bot
    # may be reused for the Widget only if it is explicitly configured;
    # the admin allowlist/session are NEVER inherited by a linked teacher.
    token = os.environ.get("CIKGULAJU_GOOGLE_STAGING_LINK_BOT_TOKEN", "")
    name = os.environ.get("CIKGULAJU_GOOGLE_STAGING_LINK_BOT_USERNAME", "").lstrip("@")
    if (re.fullmatch(r"[0-9]{5,15}:[A-Za-z0-9_-]{20,}", token)
            and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", name)):
        return token, name
    return _staging_admin_bot()


def _link_config():
    cfg = _enabled_config()
    bot = _link_bot()
    if (cfg is None
            or os.environ.get("CIKGULAJU_GOOGLE_TELEGRAM_LINK_STAGING_ENABLED") != "1"
            or bot is None):
        return None
    return cfg, bot


def _same_origin(cfg):
    return (request.headers.get("Origin") == cfg["origin"]
            and request.headers.get("Sec-Fetch-Site", "same-origin")
            in ("same-origin", "none"))


def _read_json(req, *, limit=4096):
    try:
        with urlopen(req, timeout=8) as res:
            raw = res.read(limit + 1)
            if res.status not in (200, 201) or len(raw) > limit:
                raise StagingLinkUnavailable("Invalid link response")
        return json.loads(raw)
    except (HTTPError, URLError, OSError, ValueError, TypeError) as exc:
        raise StagingLinkUnavailable("Staging identity backend unavailable") from exc


def _link_status(cfg, account_id):
    base = cfg["supabase_url"].rstrip("/") + "/rest/v1/"
    headers = staging_service_headers(cfg["staging_service_key"])
    q = urlencode({"select": "id,legacy_telegram_user_id",
                   "id": "eq." + account_id, "limit": "1"})
    accounts = _read_json(Request(base + "web_accounts?" + q,
                                  headers=headers, method="GET"))
    q = urlencode({"select": "subject", "provider": "eq.telegram",
                   "account_id": "eq." + account_id, "limit": "2"})
    identities = _read_json(Request(base + "web_account_identities?" + q,
                                    headers=headers, method="GET"))
    if (not isinstance(accounts, list) or len(accounts) != 1
            or not isinstance(accounts[0], dict)
            or accounts[0].get("id") != account_id
            or not isinstance(identities, list) or len(identities) > 1):
        raise StagingLinkUnavailable("Invalid staging account mapping")
    telegram_id = accounts[0].get("legacy_telegram_user_id")
    if telegram_id is None and not identities:
        return {"linked": False, "staging_only": True}
    if (type(telegram_id) is not int or telegram_id <= 0
            or len(identities) != 1
            or identities[0].get("subject") != str(telegram_id)):
        raise StagingLinkUnavailable("Inconsistent staging identity mapping")
    return {"linked": True, "staging_only": True,
            "telegram_user_id": str(telegram_id)}


def _commit_link(cfg, account_id, telegram_id):
    endpoint = cfg["supabase_url"].rstrip("/") + (
        "/rest/v1/rpc/link_verified_telegram_web_account_staging")
    headers = staging_service_headers(cfg["staging_service_key"])
    req = Request(endpoint, method="POST",
                  data=json.dumps({"p_account_id": account_id,
                                   "p_telegram_user_id": telegram_id}).encode(),
                  headers={**headers, "Content-Type": "application/json"})
    result = _read_json(req, limit=2048)
    if (not isinstance(result, dict) or result.get("linked") is not True
            or result.get("staging_only") is not True
            or str(result.get("telegram_user_id")) != str(telegram_id)):
        raise StagingLinkUnavailable("Unconfirmed Telegram link")
    return result


@bp.after_request
def _private(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/google-staging-link-telegram")
def link_page():
    if _link_config() is None:
        return jsonify({"error": "Pemadanan akaun staging belum dibuka"}), 503
    actor, failure = _actor()
    if failure is not None:
        return failure
    return make_response(send_file(
        Path(__file__).with_name("google_staging_link_telegram.html"),
        mimetype="text/html", max_age=0))


@bp.get("/api/google-staging/link/telegram/status")
def link_status():
    pair = _link_config()
    if pair is None:
        return jsonify({"error": "Pemadanan staging belum tersedia"}), 503
    actor, failure = _actor()
    if failure is not None:
        return failure
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    try:
        state = _link_status(pair[0], actor.account_id)
    except (StagingLinkUnavailable, KeyError, TypeError, ValueError):
        return jsonify({"error": "Status pemadanan tidak dapat disahkan"}), 503
    return jsonify({**state, "bot_username": pair[1][1],
                    "entitlements_shared": False})


@bp.post("/api/google-staging/link/telegram")
def link_telegram():
    pair = _link_config()
    if pair is None:
        return jsonify({"error": "Pemadanan staging belum tersedia"}), 503
    actor, failure = _actor()
    if failure is not None:
        return failure
    cfg, bot = pair
    if not _same_origin(cfg):
        return jsonify({"error": "Permintaan rentas laman ditolak"}), 403
    if (not request.is_json or request.content_length is None
            or request.content_length > MAX_BODY):
        return jsonify({"error": "Permintaan tidak sah"}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"telegram_auth"}:
        return jsonify({"error": "Bukti pengesahan Telegram diperlukan"}), 400
    telegram_id = verify_telegram_login(
        payload["telegram_auth"], bot[0], max_age_seconds=120)
    if type(telegram_id) is not int:
        return jsonify({"error": "Pengesahan Telegram tidak sah atau tamat"}), 403
    telegram_actor = from_verified_telegram_account(
        telegram_id, {"authenticated": True, "telegram_user_id": telegram_id})
    if not may_link_accounts(actor, telegram_actor, both_sessions_verified=True):
        return jsonify({"error": "Dua identiti yang sah diperlukan"}), 403
    try:
        result = _commit_link(cfg, actor.account_id, telegram_id)
        state = _link_status(cfg, actor.account_id)
        if not state["linked"] or state["telegram_user_id"] != str(telegram_id):
            raise StagingLinkUnavailable("Unconfirmed account association")
    except StagingLinkUnavailable as exc:
        # PostgREST 400 is used for guarded SQL exception/unique collisions.
        code = 409 if isinstance(exc.__cause__, HTTPError) and exc.__cause__.code in (400,409) else 503
        return jsonify({"error": ("Identiti telah dipadankan dengan akaun lain"
                                 if code == 409 else
                                 "Pemadanan belum dapat disahkan")}), code
    return jsonify({"linked": True, "staging_only": True,
                    "telegram_user_id": str(telegram_id),
                    "entitlements_shared": False,
                    "note": "Identiti dipadankan di staging sahaja; langganan Telegram tidak dipindahkan."})
