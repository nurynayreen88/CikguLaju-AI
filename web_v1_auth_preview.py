"""Isolated, fail-closed Flask Telegram login flow for Web V1 staging.

No production registration. The caller supplies its bot username and bot token
through environment variables. Never accepts a Telegram ID without signature.
"""
import os
import secrets
import time

from flask import Blueprint, abort, jsonify, redirect, render_template_string, request, session, url_for
from web_v1_telegram_auth import TelegramLoginError, verify_telegram_login

auth_preview = Blueprint("web_v1_auth_preview", __name__, url_prefix="/web/auth")

LOGIN_HTML = """<!doctype html><html lang="ms"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Log Masuk — CikguLaju AI</title>
<style>body{font:16px system-ui,sans-serif;background:#f0fdfa;color:#123b39;margin:0}
main{max-width:430px;margin:10vh auto;padding:28px;background:white;border-radius:18px;box-shadow:0 8px 24px #134e4a22}
h1{color:#0f766e}p{line-height:1.6}.muted{color:#64748b;font-size:14px}
a{color:#0f766e}</style></head><body><main><h1>CikguLaju AI</h1>
<p>Log masuk dengan akaun Telegram yang sama seperti bot CikguLaju.</p>
<div id="telegram-login"></div>
<script async src="https://telegram.org/js/telegram-widget.js?22"
data-telegram-login="{{ bot_username }}" data-size="large"
data-auth-url="{{ callback_url }}" data-request-access="write"></script>
<p class="muted">Pengesahan Telegram diperlukan. Tiada kata laluan baharu.</p>
</main></body></html>"""


@auth_preview.get("/login")
def login():
    username = os.environ.get("CIKGULAJU_WEB_TELEGRAM_BOT_USERNAME", "").lstrip("@")
    if not username or not username.replace("_", "").isalnum():
        abort(503)
    # CSRF state is checked using the browser's session cookie at callback.
    nonce = secrets.token_urlsafe(24)
    session["web_auth_nonce"] = nonce
    session["web_auth_started"] = int(time.time())
    callback = url_for(".callback", _external=True, _scheme="https", state=nonce)
    return render_template_string(LOGIN_HTML, bot_username=username, callback_url=callback)


@auth_preview.get("/callback")
def callback():
    expected = session.pop("web_auth_nonce", None)
    started = session.pop("web_auth_started", 0)
    supplied = request.args.get("state", "")
    if not expected or not secrets.compare_digest(expected, supplied):
        abort(403)
    if not isinstance(started, int) or time.time() - started > 300:
        abort(403)
    token = os.environ.get("CIKGULAJU_WEB_TELEGRAM_BOT_TOKEN", "")
    if not token:
        abort(503)
    signed = request.args.to_dict(flat=True)
    signed.pop("state", None)
    try:
        user = verify_telegram_login(signed, token)
    except TelegramLoginError:
        abort(403)
    session.clear()
    session["web_telegram_user_id"] = user["telegram_user_id"]
    session["web_login_at"] = int(time.time())
    return redirect(url_for(".whoami"))


@auth_preview.get("/whoami")
def whoami():
    uid = session.get("web_telegram_user_id")
    if type(uid) is not int or uid <= 0:
        abort(401)
    return jsonify({"authenticated": True, "telegram_user_id": uid})


@auth_preview.post("/logout")
def logout():
    # Staging-only endpoint: require same-origin Origin header when present.
    origin = request.headers.get("Origin")
    if not origin or origin.rstrip("/") != request.host_url.rstrip("/"):
        abort(403)
    session.clear()
    return jsonify({"authenticated": False})


def create_auth_preview_app(*, secret_key, testing=False):
    """Standalone test harness; never imported by production app.py."""
    from flask import Flask
    if not secret_key:
        raise ValueError("strong session signing key required")
    app = Flask(__name__)
    app.config.update(SECRET_KEY=secret_key, TESTING=testing,
                      SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax")
    app.register_blueprint(auth_preview)
    return app
