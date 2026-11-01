"""Optional, fail-closed Telegram Login Widget callback for isolated Web V1.

Disabled unless all secrets and explicit existing-account SQLite mapping are set.
Never creates an account or alters the Telegram bot database.
"""
import os
from flask import Blueprint, current_app, jsonify, request, make_response
from web_v1_telegram_login import verify_telegram_login
from web_v1_sessions import issue_session_ticket, verify_session_ticket
from web_v1_sqlite_account_adapter import lookup_existing_sqlite_account
from web_v1_entitlements import display_trusted_account

auth_blueprint = Blueprint("web_v1_telegram_auth", __name__)
COOKIE = "cikgulaju_web_v1_session"


def _config():
    names = ("CIKGULAJU_WEB_BOT_TOKEN", "CIKGULAJU_WEB_SESSION_SECRET",
             "CIKGULAJU_WEB_ACCOUNT_DB", "CIKGULAJU_WEB_ACCOUNT_TABLE",
             "CIKGULAJU_WEB_ACCOUNT_ID_COLUMN", "CIKGULAJU_WEB_ACCOUNT_LIFETIME_COLUMN",
             "CIKGULAJU_WEB_ACCOUNT_CREDITS_COLUMN")
    values = [os.environ.get(n, "") for n in names]
    if any(not v for v in values) or len(values[1]) < 32:
        return None
    return dict(zip(names, values))


def _lookup(config, uid):
    return lookup_existing_sqlite_account(
        config["CIKGULAJU_WEB_ACCOUNT_DB"], uid,
        table=config["CIKGULAJU_WEB_ACCOUNT_TABLE"],
        id_column=config["CIKGULAJU_WEB_ACCOUNT_ID_COLUMN"],
        lifetime_column=config["CIKGULAJU_WEB_ACCOUNT_LIFETIME_COLUMN"],
        vip_column=os.environ.get("CIKGULAJU_WEB_ACCOUNT_VIP_COLUMN") or None,
        credits_column=config["CIKGULAJU_WEB_ACCOUNT_CREDITS_COLUMN"])


@auth_blueprint.post("/api/auth/telegram/widget")
def telegram_widget_callback():
    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    if not request.is_json or request.content_length is None or request.content_length > 8192:
        return jsonify({"error": "invalid request"}), 400
    payload = request.get_json(silent=True)
    uid = verify_telegram_login(payload, config["CIKGULAJU_WEB_BOT_TOKEN"])
    if uid is None:
        return jsonify({"error": "invalid Telegram authentication"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        current_app.logger.exception("Web V1 account lookup unavailable")
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "existing account required"}), 403
    ticket = issue_session_ticket(uid, config["CIKGULAJU_WEB_SESSION_SECRET"])
    response = make_response(jsonify({"authenticated": True}), 200)
    response.set_cookie(COOKIE, ticket, secure=True, httponly=True, samesite="Lax",
                        max_age=43200, path="/")
    return response


@auth_blueprint.get("/api/auth/telegram/session")
def telegram_session_status():
    config = _config()
    if config is None:
        return jsonify({"authenticated": False}), 401
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"authenticated": False}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"authenticated": False}), 503
    if not account:
        return jsonify({"authenticated": False}), 401
    entitlement = display_trusted_account(account)
    return jsonify({"authenticated": True, **entitlement})


@auth_blueprint.post("/api/auth/telegram/logout")
def telegram_logout():
    response = make_response(jsonify({"authenticated": False}))
    response.delete_cookie(COOKIE, path="/", secure=True, httponly=True, samesite="Lax")
    return response
