"""Opt-in production Google OAuth using canonical UUID CikguLaju principals.

Routes are registered but disabled unless a separate operator-reviewed rollout
enables Google Auth in the EXISTING production Supabase. No staging Supabase,
cross-Render entitlement bridge, fake Telegram IDs or automatic email matching.
Google-only users receive a separate v2 canonical session; linked users may
reuse the existing v1 Telegram Web UI after a fresh same-DB validation.

DO NOT ENABLE until both canonical migrations, native RPH private storage and
the end-to-end Google-only generation gate have been reviewed.
"""
import base64
from html import escape
import hashlib
import json
import os
import secrets
import time
import uuid
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from flask import Blueprint, jsonify, make_response, redirect, request
from web.google_auth_staging_routes import _seal_state, _unseal_state
from web.google_account_store import verified_google_email
from web.native_google_principal_store import (
    PROD_SUPABASE, CanonicalAccountUnavailable,
    register_verified_google_principal, read_google_principal,
    canonical_rph_access,
)
from web_v1_telegram_auth_routes import COOKIE as LEGACY_COOKIE, _config as legacy_config, _lookup
from web_v1_sessions import issue_session_ticket, verify_session_ticket
from web_v1_canonical_sessions import (
    COOKIE as GOOGLE_COOKIE, issue_google_principal_ticket,
    verify_google_principal_ticket,
)

bp = Blueprint("cikgulaju_native_google_canonical_login", __name__)
STATE_COOKIE = "cikgulaju_native_google_canonical_oauth_state"
HOST = "cikgulaju-web.onrender.com"


class CanonicalGoogleLoginUnavailable(RuntimeError):
    pass


def _config():
    if (os.environ.get("CIKGULAJU_NATIVE_GOOGLE_CANONICAL_ENABLED") != "1"
            or request.host != HOST):
        return None
    old = legacy_config()
    pubkey = os.environ.get("CIKGULAJU_NATIVE_GOOGLE_PUBLISHABLE_KEY", "")
    if (not isinstance(old, dict) or old.get("account_backend") != "supabase"
            or old.get("supabase_url", "").rstrip("/") != PROD_SUPABASE
            or len(old.get("supabase_key", "")) < 24
            or not isinstance(pubkey, str) or len(pubkey) < 20):
        return None
    secret = old.get("CIKGULAJU_WEB_SESSION_SECRET", "")
    if len(secret) < 32:
        return None
    return {**old, "origin": "https://" + HOST,
            "apikey": pubkey, "secret": secret}


def _read_json(req, *, limit=16384):
    try:
        with urlopen(req, timeout=12) as res:
            raw = res.read(limit + 1)
            if res.status != 200 or len(raw) > limit:
                raise CanonicalGoogleLoginUnavailable("Invalid OAuth response")
        return json.loads(raw)
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        raise CanonicalGoogleLoginUnavailable("Google OAuth not available") from None


def _existing_google_account(cfg):
    account_id = verify_google_principal_ticket(
        request.cookies.get(GOOGLE_COOKIE), cfg["secret"])
    if account_id is None:
        return None
    return read_google_principal(cfg, account_id)


@bp.after_request
def _private(resp):
    resp.headers["Cache-Control"] = "no-store, private"
    resp.headers["Vary"] = "Cookie"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@bp.get("/api/auth/google-native/options")
def login_options():
    # Public capability discovery, no secrets or user data.
    # Do not advertise a login-only half-finished feature to teachers.
    # The original Web offers Google only after the RPH release gate is
    # deliberately enabled alongside verified canonical OAuth.
    return jsonify({"google_available": (_config() is not None and
                    os.environ.get("CIKGULAJU_NATIVE_GOOGLE_RPH_ENABLED") == "1"),
                    "login_provider": "google",
                    "same_account_backend": True})


@bp.get("/google-login")
def landing():
    if _config() is None:
        return jsonify({"error": "Log masuk Google baharu belum dibuka"}), 503
    html = ('<!doctype html><html lang="ms"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>CikguLaju AI — Log masuk Google</title>'
            '<main style="max-width:540px;margin:9vh auto;font:17px system-ui">'
            '<h1>CikguLaju AI</h1><p>Log masuk menggunakan akaun Google '
            'yang disahkan. Akaun Telegram lama kekal seperti biasa.</p>'
            '<p><a href="/api/auth/google-native/start">Teruskan dengan Google</a></p>'
            '<p><a href="/">Log masuk dengan Telegram</a></p></main></html>')
    return make_response(html, 200, {"Content-Type":"text/html; charset=utf-8"})


@bp.get("/api/auth/google-native/start")
def start():
    cfg = _config()
    if cfg is None or request.args:
        return jsonify({"error": "Login Google belum diaktifkan"}), 503
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode("ascii")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    state = secrets.token_hex(16)
    callback = cfg["origin"] + "/api/auth/google-native/callback?state=" + state
    target = PROD_SUPABASE + "/auth/v1/authorize?" + urlencode({
        "provider": "google", "redirect_to": callback,
        "code_challenge": challenge, "code_challenge_method": "s256",
    })
    res = redirect(target, code=302)
    res.set_cookie(STATE_COOKIE,
                   _seal_state(verifier, state, int(time.time()), cfg["secret"]),
                   secure=True, httponly=True, samesite="Lax",
                   max_age=300, path="/api/auth/google-native")
    return res


@bp.get("/api/auth/google-native/callback")
def callback():
    cfg = _config()
    if cfg is None:
        return jsonify({"error": "Login Google belum diaktifkan"}), 503
    proof = _unseal_state(request.cookies.get(STATE_COOKIE), cfg["secret"])
    if (proof is None or set(request.args) != {"state", "code"}
            or request.args.get("state") != proof[1]
            or not 0 < len(request.args.get("code", "")) <= 2048):
        return jsonify({"error": "Pengesahan Google tamat atau tidak sah"}), 401
    try:
        token = _read_json(Request(
            PROD_SUPABASE + "/auth/v1/token?grant_type=pkce",
            data=json.dumps({"auth_code":request.args["code"],
                             "code_verifier":proof[0]}).encode("utf-8"),
            method="POST",
            headers={"apikey":cfg["apikey"],"Content-Type":"application/json",
                     "Accept":"application/json"})).get("access_token")
        if not isinstance(token, str) or not 30 < len(token) < 8192:
            raise CanonicalGoogleLoginUnavailable("Invalid OAuth token")
        identity = _read_json(Request(
            PROD_SUPABASE + "/auth/v1/user", method="GET",
            headers={"apikey":cfg["apikey"],"Authorization":"Bearer "+token,
                     "Accept":"application/json"}))
        # Exact Google provider email and confirmation are checked again by
        # the canonical principal adapter before the private database RPC.
        verified_google_email(identity)
        principal_id = register_verified_google_principal(cfg, identity)
        principal = read_google_principal(cfg, principal_id)
        current_legacy = verify_session_ticket(
            request.cookies.get(LEGACY_COOKIE), cfg["secret"])
        uid = principal["legacy_telegram_user_id"]
        # Two independently verified sessions MAY coexist before the
        # teacher explicitly chooses to link. Do not merge them by email.
        # Only reject a conflict if this Google principal is ALREADY linked.
        if (current_legacy is not None and uid is not None
                and current_legacy != uid):
            return jsonify({"error":
                "Dua sesi akaun berlainan. Log keluar dahulu sebelum masuk Google."}), 409
        if uid is not None:
            existing = _lookup(cfg, uid)
            if (not isinstance(existing, dict)
                    or existing.get("authenticated") is not True
                    or existing.get("telegram_user_id") != uid):
                raise CanonicalGoogleLoginUnavailable("Linked legacy account unavailable")
    except (CanonicalGoogleLoginUnavailable, CanonicalAccountUnavailable,
            ValueError, KeyError, TypeError, AttributeError):
        return jsonify({"error":"Identiti Google belum dapat disahkan. Kredit tidak dipotong."}),503

    res = redirect("/" if uid is not None else "/google-account", code=303)
    res.delete_cookie(STATE_COOKIE, path="/api/auth/google-native",
                      secure=True, httponly=True, samesite="Lax")
    res.set_cookie(GOOGLE_COOKIE,issue_google_principal_ticket(principal_id,cfg["secret"]),
                   secure=True,httponly=True,samesite="Lax",max_age=43200,path="/")
    if uid is not None:
        # Same legacy Web session and direct original Supabase account lookup.
        res.set_cookie(LEGACY_COOKIE,issue_session_ticket(uid,cfg["secret"]),
                       secure=True,httponly=True,samesite="Lax",max_age=43200,path="/")
    return res


@bp.get("/api/auth/google-native/session")
def status():
    cfg = _config()
    if cfg is None:
        return jsonify({"authenticated":False}),503
    if request.args:
        return jsonify({"error":"Query parameters not accepted"}),400
    try:
        account = _existing_google_account(cfg)
        if account is None:
            return jsonify({"authenticated":False}),401
        access = canonical_rph_access(cfg, account)
    except CanonicalAccountUnavailable:
        return jsonify({"authenticated":False}),503
    answer = jsonify({
        "authenticated":True, "provider":"google",
        "login_id":account["login_id"],
        "linked_telegram":account["legacy_telegram_user_id"] is not None,
        **access,
    })
    return answer


@bp.get("/google-account")
def dashboard():
    cfg = _config()
    if cfg is None:
        return jsonify({"error":"Login Google belum diaktifkan"}),503
    try:
        account = _existing_google_account(cfg)
        if account is None:
            return redirect("/google-login",code=303)
        access = canonical_rph_access(cfg, account)
    except CanonicalAccountUnavailable:
        return jsonify({"error":"Profil dan hak akses belum boleh disahkan"}),503
    login_id = escape(account["login_id"], quote=True)
    mode = access["rph_access_mode"]
    remaining = access["rph_trial_remaining"]
    if mode == "paid":
        display = "Akses RPH tanpa had (langganan/Rakan Pembangun)"
    elif mode == "trial":
        display = "Baki janaan percuma: " + str(remaining)
    elif mode == "exhausted":
        display = "10 janaan percuma telah digunakan"
    else:
        return jsonify({"error":"Status hak akses tidak sah"}),503
    linked = account["legacy_telegram_user_id"] is not None
    rph_link = "/" if linked else "/google-rph"
    rph_text = "Buka Web CikguLaju" if linked else "Sediakan RPH"
    html = ('<!doctype html><html lang="ms"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>CikguLaju AI — Akaun Google</title>'
            '<main style="max-width:540px;margin:9vh auto;font:17px system-ui">'
            '<h1>Akaun CikguLaju</h1>'
            '<p>ID log masuk Google: <strong>' + login_id + '</strong></p>'
            '<p>' + escape(display) + '</p>'
            '<p><a href="' + rph_link + '">' + rph_text + '</a></p>'
            '<p><a href="/google-link-telegram">Pautkan/Semak akaun Telegram</a></p>'
            '<a href="/">Kembali ke CikguLaju</a></main></html>')
    return make_response(html,200,{"Content-Type":"text/html; charset=utf-8"})


@bp.post("/api/auth/google-native/logout")
def logout():
    cfg = _config()
    if cfg is None:
        return jsonify({"error":"Login Google belum diaktifkan"}),503
    if (request.headers.get("Origin") != cfg["origin"]
            or request.headers.get("Sec-Fetch-Site", "same-origin")
               not in ("same-origin","none")):
        return jsonify({"error":"Asal permintaan tidak sah"}),403
    # A linked Google sign-in also creates a working legacy Web session.
    # Revoke that session when ending the Google session, otherwise the Web
    # remains authenticated even after the teacher explicitly logged out.
    had_google_session = verify_google_principal_ticket(
        request.cookies.get(GOOGLE_COOKIE), cfg["secret"]) is not None
    res = jsonify({"authenticated":False})
    res.delete_cookie(GOOGLE_COOKIE,path="/",secure=True,httponly=True,samesite="Lax")
    if had_google_session:
        # Also signs out an independently opened Telegram Web session if both
        # methods were active in this browser; this is safer than leaving a
        # hidden privileged v1 session alive after Google logout.
        res.delete_cookie(LEGACY_COOKIE,path="/",secure=True,httponly=True,samesite="Lax")
    return res
