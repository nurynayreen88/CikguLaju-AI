"""Fail-closed Telegram Login Widget callback for CikguLaju Web.

A verified new Telegram identity may register only through the shared Supabase
account backend. The isolated SQLite compatibility path remains read-only.
"""
import os
from pathlib import Path
from flask import Blueprint, current_app, jsonify, request, make_response
from web_v1_telegram_login import verify_telegram_login
from web_v1_sessions import issue_session_ticket, verify_session_ticket
from web_v1_sqlite_account_adapter import lookup_existing_sqlite_account
from web_v1_entitlements import display_trusted_account

auth_blueprint = Blueprint("web_v1_telegram_auth", __name__)
COOKIE = "cikgulaju_web_v1_session"


def _config():
    token = os.environ.get("CIKGULAJU_WEB_BOT_TOKEN", "")
    secret = os.environ.get("CIKGULAJU_WEB_SESSION_SECRET", "")
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    if not token or len(secret) < 32:
        return None
    if url.startswith("https://") and key:
        return {"CIKGULAJU_WEB_BOT_TOKEN": token,
                "CIKGULAJU_WEB_SESSION_SECRET": secret, "account_backend": "supabase",
                "supabase_url": url, "supabase_key": key}
    names = ("CIKGULAJU_WEB_ACCOUNT_DB", "CIKGULAJU_WEB_ACCOUNT_TABLE",
             "CIKGULAJU_WEB_ACCOUNT_ID_COLUMN", "CIKGULAJU_WEB_ACCOUNT_LIFETIME_COLUMN",
             "CIKGULAJU_WEB_ACCOUNT_CREDITS_COLUMN")
    values = [os.environ.get(n, "") for n in names]
    if any(not v for v in values):
        return None
    db = Path(values[0])
    if not db.is_file() or not os.access(db, os.R_OK):
        return None
    return {"CIKGULAJU_WEB_BOT_TOKEN": token, "CIKGULAJU_WEB_SESSION_SECRET": secret,
            "account_backend": "sqlite", **dict(zip(names, values))}


def _lookup(config, uid):
    if config.get("account_backend") == "supabase":
        from web_v1_supabase_account_adapter import lookup_existing_supabase_account
        return lookup_existing_supabase_account(config["supabase_url"], config["supabase_key"], uid)
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
    created = False
    try:
        # Only reachable after verified Telegram Login Widget HMAC.
        account = _lookup(config, uid)
        if not account and config.get("account_backend") == "supabase":
            from web.direct_telegram_registration import ensure_verified_web_user
            created = ensure_verified_web_user(config, uid, payload)
            account = _lookup(config, uid)
    except Exception:
        current_app.logger.exception("Web account registration/lookup unavailable")
        return jsonify({"error": "account registration unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        if config.get("account_backend") == "sqlite":
            # Compatibility path is intentionally read-only: unknown users are forbidden.
            return jsonify({"error": "existing account required"}), 403
        # Supabase signup could not be confirmed; fail closed, never issue a session.
        return jsonify({"error": "account registration not confirmed"}), 503
    try:
        from web.web_referral_routes import capture_after_verified_login
        capture_after_verified_login(uid, notify=not created)
    except Exception:
        current_app.logger.warning("Web referral bridge unavailable")
    if created:
        try:
            from web.direct_telegram_registration import notify_telegram_admin
            notify_telegram_admin(uid)
        except Exception as exc:
            current_app.logger.warning("Web new-user admin notice unavailable: %s",
                                       type(exc).__name__)
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
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"authenticated": False}), 401
    entitlement = display_trusted_account(account)
    from web.english_rpt_2027_http import _has_paid_access
    paid = _has_paid_access(account)
    remaining = account.get("free_remaining")
    # Same source as Telegram, not an extra Web allocation. For paid users
    # trial credits remain untouched and the interface shows unlimited access.
    if type(remaining) is not int or not 0 <= remaining <= 10:
        remaining = None
    access_mode = "paid" if paid else (
        "trial" if remaining is not None and remaining > 0 else
        "exhausted" if remaining == 0 else "unavailable")
    response = make_response(jsonify({
        "authenticated": True, **entitlement,
        "rph_access_mode": access_mode,
        "rph_trial_remaining": remaining,
    }))
    response.headers["Cache-Control"] = "no-store, private"
    return response


@auth_blueprint.post("/api/auth/telegram/logout")
def telegram_logout():
    response = make_response(jsonify({"authenticated": False}))
    response.delete_cookie(COOKIE, path="/", secure=True, httponly=True, samesite="Lax")
    # Google-linked accounts can obtain a legacy Web session. End both Web
    # sessions when the teacher uses the main CikguLaju logout button, so the
    # Google principal cookie cannot silently restore access after logout.
    from web_v1_canonical_sessions import COOKIE as GOOGLE_COOKIE
    response.delete_cookie(GOOGLE_COOKIE, path="/", secure=True,
                           httponly=True, samesite="Lax")
    return response


@auth_blueprint.get("/api/web/teacher/classes")
def teacher_class_suggestions():
    """Return only this session's saved class names; never a user directory."""
    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    uid = verify_session_ticket(
        request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "authentication required"}), 401
    if request.args:
        return jsonify({"error": "unexpected query parameters"}), 400
    try:
        account = _lookup(config, uid)
    except Exception:
        current_app.logger.exception("Web teacher profile account validation failed")
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "existing account required"}), 403
    if config.get("account_backend") != "supabase":
        return jsonify({"error": "saved classes source unavailable"}), 503
    try:
        from web.teacher_class_choices import get_existing_teacher_classes
        items = get_existing_teacher_classes(
            config["supabase_url"], config["supabase_key"], uid)
    except Exception:
        current_app.logger.exception("Web teacher class suggestions unavailable")
        return jsonify({"error": "saved classes temporarily unavailable"}), 503
    response = make_response(jsonify({"items": items}))
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
