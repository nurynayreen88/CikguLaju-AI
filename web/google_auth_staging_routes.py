"""Staging-only Supabase Google OAuth PKCE handshake.

This deliberately does NOT issue the legacy Telegram Web cookie or grant
catalogue, RPH, quota, payment, admin, or profile access. Google-only accounts
need a canonical account migration before those privileges can be enabled.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, make_response, redirect, request, send_file
from web_google_identity_sessions import (
    issue_google_identity_ticket, verify_google_identity_ticket,
)
from web.google_account_store import ensure_google_staging_account, GoogleAccountUnavailable

bp = Blueprint("google_auth_staging", __name__)
STATE_COOKIE = "cikgulaju_google_oauth_staging_state"
TICKET_COOKIE = "cikgulaju_google_staging_ticket"
STATE_TTL = 300


def _config():
    # Enabling this route requires deliberate, *separate* staging configuration.
    if os.environ.get("CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED") != "1":
        return None
    base = os.environ.get("CIKGULAJU_GOOGLE_STAGING_SUPABASE_URL", "").rstrip("/")
    parsed = urlsplit(base)
    key = os.environ.get("CIKGULAJU_GOOGLE_STAGING_SUPABASE_PUBLISHABLE_KEY", "")
    staging_service_key = os.environ.get("CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY", "")
    secret = os.environ.get("CIKGULAJU_WEB_SESSION_SECRET", "")
    origin = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ORIGIN", "").rstrip("/")
    host = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ALLOWED_HOST", "")
    parsed_origin = urlsplit(origin)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.port is not None
            or parsed.username or parsed.password or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment):
        return None
    if (parsed_origin.scheme != "https" or not parsed_origin.hostname
            or parsed_origin.port is not None or parsed_origin.username
            or parsed_origin.password or parsed_origin.path not in ("", "/")
            or parsed_origin.query or parsed_origin.fragment
            or parsed_origin.netloc != host or not host):
        return None
    # Do not let a staging-only Google signup accidentally target the live DB.
    production_supabase = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if (not production_supabase or base == production_supabase
            or host == "cikgulaju-web.onrender.com"
            or len(key) < 20 or len(secret) < 32
            or len(staging_service_key) < 24):
        return None
    return {"supabase_url": base, "apikey": key, "secret": secret,
            "staging_service_key": staging_service_key,
            "origin": origin, "host": host}


def _enabled_config():
    config = _config()
    if config is None or request.host != config["host"] or not request.is_secure:
        return None
    return config


def _seal_state(verifier, state, issued_at, secret):
    body = f"{verifier}.{state}.{issued_at}"
    mac = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return body + "." + mac


def _unseal_state(cookie, secret):
    if not isinstance(cookie, str) or len(cookie) > 400:
        return None
    parts = cookie.split(".")
    if len(parts) != 4:
        return None
    verifier, state, issued, supplied = parts
    if (len(verifier) < 43 or len(verifier) > 128
            or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in verifier)
            or len(state) != 32 or any(c not in "0123456789abcdef" for c in state)
            or len(supplied) != 64 or any(c not in "0123456789abcdef" for c in supplied)):
        return None
    try:
        when = int(issued)
    except ValueError:
        return None
    now = int(time.time())
    if when <= 0 or when > now or now - when > STATE_TTL or str(when) != issued:
        return None
    body = ".".join(parts[:-1])
    expected = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return (verifier, state) if hmac.compare_digest(expected, supplied) else None


def _json_response(request_obj, *, timeout=8, limit=16384):
    try:
        with urlopen(request_obj, timeout=timeout) as response:
            data = response.read(limit + 1)
            if len(data) > limit or response.status != 200:
                raise ValueError("Unexpected Supabase Auth response")
        answer = json.loads(data)
        if not isinstance(answer, dict):
            raise ValueError("Invalid Supabase Auth response")
        return answer
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError):
        raise RuntimeError("Supabase Google Auth unavailable") from None


@bp.get("/google-staging-login")
def google_staging_login():
    if not _enabled_config():
        return jsonify({"error": "Google staging unavailable"}), 503
    return send_file(Path(__file__).with_name("google_staging_login.html"),
                     mimetype="text/html", max_age=0)


@bp.get("/api/auth/google/start")
def google_start():
    config = _enabled_config()
    if not config:
        return jsonify({"error": "Google staging login not configured"}), 503
    if request.args:
        return jsonify({"error": "Unexpected query"}), 400
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode("ascii")
    state = secrets.token_hex(16)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    callback = config["origin"] + "/api/auth/google/callback?state=" + state
    url = config["supabase_url"] + "/auth/v1/authorize?" + urlencode({
        "provider": "google", "redirect_to": callback,
        "code_challenge": challenge, "code_challenge_method": "s256"})
    response = redirect(url, code=302)
    response.set_cookie(STATE_COOKIE, _seal_state(verifier, state, int(time.time()),
                                                   config["secret"]),
                        secure=True, httponly=True, samesite="Lax",
                        max_age=STATE_TTL, path="/api/auth/google")
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/api/auth/google/callback")
def google_callback():
    config = _enabled_config()
    if not config:
        return jsonify({"error": "Google staging login not configured"}), 503
    response = make_response(jsonify({"error": "Pengesahan Google tidak berjaya"}), 401)
    response.delete_cookie(STATE_COOKIE, path="/api/auth/google",
                           secure=True, httponly=True, samesite="Lax")
    response.headers["Cache-Control"] = "no-store"
    proof = _unseal_state(request.cookies.get(STATE_COOKIE), config["secret"])
    if (proof is None or request.args.get("state") != proof[1]
            or len(request.args) != 2 or not request.args.get("code")
            or len(request.args.get("code", "")) > 2048):
        return response
    verifier, state = proof
    try:
        payload = json.dumps({"auth_code": request.args["code"],
                              "code_verifier": verifier}).encode("utf-8")
        exchange = Request(config["supabase_url"] + "/auth/v1/token?grant_type=pkce",
                           data=payload, method="POST", headers={
                               "apikey": config["apikey"],
                               "Content-Type": "application/json",
                               "Accept": "application/json"})
        token = _json_response(exchange)
        access_token = token.get("access_token")
        if not isinstance(access_token, str) or not 30 < len(access_token) < 8192:
            return response
        auth_user = Request(config["supabase_url"] + "/auth/v1/user",
                            headers={"apikey": config["apikey"],
                                     "Authorization": "Bearer " + access_token,
                                     "Accept": "application/json"}, method="GET")
        identity = _json_response(auth_user)
        subject = str(uuid.UUID(identity["id"]))
        if subject != identity["id"]:
            return response
        # Trust the server-side Supabase Auth user, never browser email or metadata.
        providers = identity.get("identities")
        if not isinstance(providers, list) or not any(
            isinstance(item, dict) and item.get("provider") == "google"
            for item in providers):
            return response
        # OAuth metadata is untrusted for roles/account merging; display only.
        metadata = identity.get("user_metadata")
        display = metadata.get("full_name") or metadata.get("name") if isinstance(metadata, dict) else ""
        account_id = ensure_google_staging_account(config, subject, display)
        ticket = issue_google_identity_ticket(account_id, config["secret"])
    except (GoogleAccountUnavailable, RuntimeError, KeyError, TypeError, ValueError, AttributeError):
        return jsonify({"error": "Pengesahan Google belum tersedia"}), 503

    # Google identity verified, but no canonical Web user or entitlements yet.
    # Do NOT set the old Telegram login cookie or expose the existing workspace.
    success = make_response(jsonify({
        "google_verified": True, "dashboard_access": False,
        "note": "Identiti Google dan akaun staging telah disahkan. Akses RPH belum dibuka."
    }), 200)
    success.delete_cookie(STATE_COOKIE, path="/api/auth/google",
                          secure=True, httponly=True, samesite="Lax")
    # A normal Google browser callback leads to the staging payment page.
    # Test/API clients keep the JSON response to verify access isolation.
    if request.accept_mimetypes.accept_html and not request.accept_mimetypes.accept_json:
        success = redirect(config["origin"] + "/google-staging-payments", code=303)
        success.delete_cookie(STATE_COOKIE, path="/api/auth/google",
                              secure=True, httponly=True, samesite="Lax")
    success.set_cookie(TICKET_COOKIE, ticket, secure=True, httponly=True,
                       samesite="Lax", max_age=3600, path="/")
    success.headers["Cache-Control"] = "no-store"
    return success


@bp.get("/api/auth/google/status")
def google_status():
    config = _enabled_config()
    if not config:
        return jsonify({"google_verified": False}), 503
    subject = verify_google_identity_ticket(request.cookies.get(TICKET_COOKIE),
                                            config["secret"])
    reply = make_response(jsonify({
        "google_verified": subject is not None,
        "dashboard_access": False,
    }), 200 if subject else 401)
    reply.headers["Cache-Control"] = "no-store, private"
    return reply


@bp.post("/api/auth/google/logout")
def google_logout():
    config = _enabled_config()
    if not config:
        return jsonify({"error": "Google staging login not configured"}), 503
    # This only revokes the independent Google staging ticket. The original
    # Telegram browser session remains untouched.
    response = make_response(jsonify({"google_verified": False}))
    response.delete_cookie(TICKET_COOKIE, path="/",
                           secure=True, httponly=True, samesite="Lax")
    response.headers["Cache-Control"] = "no-store"
    return response
