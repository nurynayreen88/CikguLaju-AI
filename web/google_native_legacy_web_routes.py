"""Opt-in Google -> existing CikguLaju Web session on ONE production Web process.

This first compatibility bridge is for accounts independently linked with a
Telegram Login Widget proof. A verified Google email is the human login ID;
the existing positive Telegram UID is only the legacy account lookup key.

Never infer paid access from email, claim a new Google-only account has an
existing Telegram UID, mutate a Telegram balance, or fall back to cached
rights. In-process lookup avoids a staging->production Render 502 entirely.
The final canonical Google-only account path is a separate rollout.
"""
import base64
import hashlib
import json
import os
import re
import secrets
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from flask import Blueprint, jsonify, make_response, redirect, request

from web.google_auth_staging_routes import _seal_state, _unseal_state
from web.google_account_store import (
    verified_google_email, google_staging_account_profile,
    save_verified_google_email, GoogleAccountUnavailable,
)
from web.google_telegram_link_staging_routes import _link_status, StagingLinkUnavailable
from web.google_staging_service_auth import staging_service_headers
from web_v1_sessions import issue_session_ticket
from web_v1_telegram_auth_routes import _config as legacy_config, _lookup, COOKIE

bp = Blueprint("cikgulaju_google_native_legacy_login", __name__)
STATE_COOKIE = "cikgulaju_native_web_google_oauth_state"
EXPECTED_STAGING_PROJECT = "eqrcjlnvcytkgazptbor"
MAX_RESPONSE = 16384


class NativeGoogleLoginUnavailable(RuntimeError):
    pass


def _config():
    if os.environ.get("CIKGULAJU_WEB_NATIVE_GOOGLE_ENABLED") != "1":
        return None
    legacy = legacy_config()
    if not legacy or legacy.get("account_backend") != "supabase":
        return None
    host = os.environ.get("CIKGULAJU_WEB_NATIVE_GOOGLE_HOST", "")
    origin = "https://" + host
    # This is the existing native Web, not the separate Google staging app.
    if host != "cikgulaju-web.onrender.com" or request.host != host:
        return None
    oauth_url = os.environ.get("CIKGULAJU_WEB_NATIVE_GOOGLE_SUPABASE_URL", "").rstrip("/")
    oauth_key = os.environ.get("CIKGULAJU_WEB_NATIVE_GOOGLE_PUBLISHABLE_KEY", "")
    service_key = os.environ.get("CIKGULAJU_WEB_NATIVE_GOOGLE_MAPPING_SERVICE_KEY", "")
    endpoint = urlsplit(oauth_url)
    if (endpoint.scheme != "https"
            or endpoint.netloc != EXPECTED_STAGING_PROJECT + ".supabase.co"
            or endpoint.path not in ("", "/") or endpoint.query or endpoint.fragment
            or endpoint.username or endpoint.password or endpoint.port is not None
            or len(oauth_key) < 18 or len(service_key) < 24
            or legacy.get("supabase_url", "").rstrip("/") == oauth_url):
        return None
    return {**legacy, "host": host, "origin": origin, "supabase_url": oauth_url,
            "apikey": oauth_key, "staging_service_key": service_key,
            "secret": legacy["CIKGULAJU_WEB_SESSION_SECRET"]}


def _json(req, *, limit=MAX_RESPONSE):
    try:
        with urlopen(req, timeout=12) as res:
            raw = res.read(limit + 1)
            if res.status != 200 or len(raw) > limit:
                raise NativeGoogleLoginUnavailable("Invalid identity response")
        return json.loads(raw)
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        raise NativeGoogleLoginUnavailable("Verified identity provider unavailable") from None


def _canonical_google_account(cfg, google_subject):
    """Never use a browser supplied email, Telegram UID, or account UUID."""
    try:
        subject = str(uuid.UUID(google_subject))
    except (TypeError, ValueError, AttributeError):
        raise NativeGoogleLoginUnavailable("Invalid Google subject") from None
    if google_subject != subject:
        raise NativeGoogleLoginUnavailable("Noncanonical Google subject")
    query = urlencode({
        "select": "account_id,subject",
        "provider": "eq.google", "subject": "eq." + subject, "limit": "2",
    })
    endpoint = cfg["supabase_url"] + "/rest/v1/web_account_identities?" + query
    result = _json(Request(endpoint, method="GET",
                           headers=staging_service_headers(cfg["staging_service_key"])),
                   limit=4096)
    if not isinstance(result, list) or len(result) != 1:
        raise NativeGoogleLoginUnavailable("Google identity not linked to a canonical account")
    row = result[0]
    if not isinstance(row, dict) or row.get("subject") != subject:
        raise NativeGoogleLoginUnavailable("Unconfirmed Google identity")
    try:
        account = str(uuid.UUID(row.get("account_id")))
    except (ValueError, TypeError, AttributeError):
        raise NativeGoogleLoginUnavailable("Invalid account binding") from None
    if account != row.get("account_id"):
        raise NativeGoogleLoginUnavailable("Invalid canonical account")
    return account


def _verified_linked_telegram(cfg, google_subject, verified_email):
    account_id = _canonical_google_account(cfg, google_subject)
    profile = google_staging_account_profile(cfg, account_id)
    old_email = profile.get("login_email")
    if old_email is not None and old_email != verified_email:
        raise NativeGoogleLoginUnavailable("Verified Google email changed unexpectedly")
    if old_email is None:
        # This writes ONLY the staging login identifier, not payment or
        # entitlement records, after OAuth has verified this exact subject.
        save_verified_google_email(cfg, account_id, verified_email)
    status = _link_status(cfg, account_id)
    if status.get("staging_only") is not True or status.get("linked") is not True:
        return None
    raw_uid = status.get("telegram_user_id")
    if (not isinstance(raw_uid, str) or not raw_uid.isascii()
            or not raw_uid.isdecimal() or raw_uid.startswith("0")
            or not 0 < int(raw_uid) <= 9223372036854775807):
        raise NativeGoogleLoginUnavailable("Invalid verified Telegram linkage")
    uid = int(raw_uid)
    # DIRECT existing Web account adapter, on THIS same Web service, against
    # the production Supabase that Telegram uses. NO cross-Render HTTP call.
    account = _lookup(legacy_config(), uid)
    if (not isinstance(account, dict) or account.get("authenticated") is not True
            or account.get("telegram_user_id") != uid):
        raise NativeGoogleLoginUnavailable("Existing Web account not confirmed")
    return uid


@bp.after_request
def secure(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/google-signin")
def landing():
    if _config() is None:
        return jsonify({"error": "Google login belum dibuka pada Web utama"}), 503
    return make_response(
        '<!doctype html><html lang="ms"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>CikguLaju — Google</title>'
        '<main style="max-width:480px;margin:10vh auto;font:17px system-ui">'
        '<h1>Log masuk CikguLaju</h1>'
        '<p>Gunakan e-mel Google yang disahkan. Akaun Telegram sedia ada '
        'hanya dipautkan selepas pengesahan kedua-dua identiti.</p>'
        '<a href="/api/web/google-native/start">Teruskan dengan Google</a>'
        '</main></html>', 200, {"Content-Type": "text/html; charset=utf-8"})


@bp.get("/api/web/google-native/start")
def start():
    cfg = _config()
    if cfg is None or request.args:
        return jsonify({"error": "Google login belum diaktifkan"}), 503
    state = secrets.token_hex(16)
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode("ascii")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    callback = cfg["origin"] + "/api/web/google-native/callback?state=" + state
    destination = cfg["supabase_url"] + "/auth/v1/authorize?" + urlencode({
        "provider": "google", "redirect_to": callback,
        "code_challenge": challenge, "code_challenge_method": "s256",
    })
    response = redirect(destination, code=302)
    response.set_cookie(STATE_COOKIE, _seal_state(verifier, state, int(time.time()),
                                                   cfg["secret"]),
                        secure=True, httponly=True, samesite="Lax", max_age=300,
                        path="/api/web/google-native")
    return response


@bp.get("/api/web/google-native/callback")
def callback():
    cfg = _config()
    if cfg is None:
        return jsonify({"error": "Google login belum diaktifkan"}), 503
    proof = _unseal_state(request.cookies.get(STATE_COOKIE), cfg["secret"])
    if (proof is None or len(request.args) != 2 or not request.args.get("code")
            or not 0 < len(request.args["code"]) <= 2048
            or request.args.get("state") != proof[1]):
        return jsonify({"error": "Pengesahan Google tamat atau tidak sah"}), 401
    payload = json.dumps({"auth_code": request.args["code"],
                          "code_verifier": proof[0]}).encode("utf-8")
    try:
        tokens = _json(Request(
            cfg["supabase_url"] + "/auth/v1/token?grant_type=pkce",
            data=payload, method="POST",
            headers={"apikey": cfg["apikey"], "Content-Type": "application/json",
                     "Accept": "application/json"}))
        token = tokens.get("access_token")
        if not isinstance(token, str) or not 30 < len(token) < 8192:
            raise NativeGoogleLoginUnavailable("Invalid OAuth token")
        identity = _json(Request(cfg["supabase_url"] + "/auth/v1/user",
                                 headers={"apikey": cfg["apikey"],
                                          "Authorization": "Bearer " + token,
                                          "Accept": "application/json"}))
        google_subject = str(uuid.UUID(identity["id"]))
        if google_subject != identity["id"]:
            raise NativeGoogleLoginUnavailable("Invalid OAuth subject")
        verified_email = verified_google_email(identity)
        uid = _verified_linked_telegram(cfg, google_subject, verified_email)
    except (NativeGoogleLoginUnavailable, StagingLinkUnavailable,
            GoogleAccountUnavailable, ValueError, KeyError, TypeError, AttributeError):
        return jsonify({"error": "Pengesahan akaun belum tersedia. Tiada kredit dipotong."}), 503

    if uid is None:
        # Google-only users keep their own canonical UUID. They MUST NOT
        # receive a fake numeric Telegram ID or the legacy Telegram cookie.
        return jsonify({"google_verified": True, "linked": False,
                        "error": "Akaun Google disahkan. Akses Web tanpa Telegram "
                                 "perlu menggunakan aliran UUID baharu."}), 409
    response = redirect("/", code=303)
    response.set_cookie(COOKIE, issue_session_ticket(uid, cfg["secret"]),
                        secure=True, httponly=True, samesite="Lax",
                        max_age=43200, path="/")
    response.delete_cookie(STATE_COOKIE, path="/api/web/google-native",
                           secure=True, httponly=True, samesite="Lax")
    return response
