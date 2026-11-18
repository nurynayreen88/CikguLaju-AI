"""Email/password login and secure email linking for CikguLaju Web.

Supabase Auth stores and verifies passwords. This module stores no passwords or
Supabase access tokens; it maps a verified Supabase Auth user to the existing
CikguLaju account key through one restricted Postgres RPC.
"""
import json
import os
import re
import uuid
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, jsonify, make_response, request

from web_v1_sessions import issue_session_ticket, verify_session_ticket
from web_v1_telegram_auth_routes import COOKIE, _config, _lookup

bp = Blueprint("web_v1_email_auth", __name__)
WEB_ORIGIN = "https://cikgulaju-web.onrender.com"
MAX_BODY_BYTES = 8192
MAX_PASSWORD_BYTES = 72
TELEGRAM_ID_LIMIT = 10**18


class IdentityConflict(Exception):
    """Email identity already belongs to a different CikguLaju account."""


def _reply(payload, status=200):
    response = make_response(jsonify(payload), status)
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _same_origin():
    return request.headers.get("Origin", "") == WEB_ORIGIN


def _request_payload():
    if (not request.is_json or request.content_length is None
            or request.content_length > MAX_BODY_BYTES):
        return None
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else None


def _credentials(payload):
    if payload is None:
        return None
    email = payload.get("email")
    password = payload.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return None
    email = email.strip().casefold()
    if (len(email) > 254 or email.count("@") != 1
            or not re.fullmatch(r"[^\s@]{1,64}@[^\s@]{1,189}", email)):
        return None
    try:
        password_bytes = password.encode("utf-8")
    except UnicodeEncodeError:
        return None
    if len(password_bytes) < 8 or len(password_bytes) > MAX_PASSWORD_BYTES:
        return None
    return email, password


def _supabase_base():
    value = os.environ.get("SUPABASE_URL", "").strip()
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname
            or not parts.hostname.endswith(".supabase.co")
            or parts.username or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment):
        raise RuntimeError("Invalid Supabase URL")
    return value.rstrip("/")


def _auth_configuration():
    config = _config()
    publishable_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    if (not config or config.get("account_backend") != "supabase"
            or not publishable_key.startswith("sb_publishable_")):
        return None
    return {
        "base": _supabase_base(),
        "publishable_key": publishable_key,
        "service_key": config["supabase_key"],
        "session_secret": config["CIKGULAJU_WEB_SESSION_SECRET"],
    }


def _decode_body(raw):
    if len(raw) > MAX_BODY_BYTES:
        raise RuntimeError("Oversized Supabase response")
    if not raw:
        return {}
    data = json.loads(raw.decode("utf-8"))
    return data if isinstance(data, (dict, list, int)) else {}


def _auth_post(auth, path, payload):
    url = auth["base"] + "/auth/v1/" + path
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = Request(url, data=body, method="POST", headers={
        "apikey": auth["publishable_key"],
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Client-Info": "cikgulaju-web-email-auth/1",
    })
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, _decode_body(response.read(MAX_BODY_BYTES + 1))
    except HTTPError as exc:
        return exc.code, _decode_body(exc.read(MAX_BODY_BYTES + 1))


def _auth_user_id(payload):
    if not isinstance(payload, dict):
        return None
    user = payload.get("user")
    raw_id = user.get("id") if isinstance(user, dict) else None
    if not isinstance(raw_id, str):
        return None
    try:
        return str(uuid.UUID(raw_id))
    except (TypeError, ValueError, AttributeError):
        return None


def _account_id(auth, auth_user_id, telegram_user_id=None):
    base = auth["base"]
    service_key = auth["service_key"]
    if not isinstance(service_key, str) or len(service_key) < 20:
        raise RuntimeError("Supabase server key missing")
    url = base + "/rest/v1/rpc/register_web_email_identity"
    payload = json.dumps({
        "p_auth_user_id": auth_user_id,
        "p_telegram_user_id": telegram_user_id,
    }, separators=(",", ":")).encode("utf-8")
    headers = {
        "apikey": service_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if not service_key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + service_key
    req = Request(url, data=payload, method="POST", headers=headers)
    try:
        with urlopen(req, timeout=10) as response:
            result = _decode_body(response.read(MAX_BODY_BYTES + 1))
    except HTTPError as exc:
        body = _decode_body(exc.read(MAX_BODY_BYTES + 1))
        message = body.get("message", "") if isinstance(body, dict) else ""
        if isinstance(message, str) and (
                "EMAIL_ACCOUNT_ALREADY_CREATED" in message
                or "EMAIL_ALREADY_LINKED" in message):
            raise IdentityConflict() from exc
        raise RuntimeError("Account identity mapping failed") from exc
    if isinstance(result, list) and len(result) == 1:
        result = result[0]
    if type(result) is not int or result <= 0 or result >= 2**63:
        raise RuntimeError("Invalid account identity mapping")
    return result


def _authenticated_response(auth, uid):
    if type(uid) is not int or uid <= 0:
        raise RuntimeError("Invalid account identity")
    account = _lookup(_config(), uid)
    if not account or account.get("telegram_user_id") != uid:
        raise RuntimeError("Account identity could not be verified")
    try:
        from web.web_referral_routes import capture_after_verified_login
        capture_after_verified_login(uid)
    except Exception as exc:
        current_app.logger.warning("Web email referral capture unavailable: %s",
                                   type(exc).__name__)
    ticket = issue_session_ticket(uid, auth["session_secret"])
    response = _reply({"authenticated": True})
    response.set_cookie(COOKIE, ticket, secure=True, httponly=True,
                        samesite="Lax", max_age=43200, path="/")
    return response


@bp.post("/api/auth/email/register")
def email_register():
    if not _same_origin():
        return _reply({"error": "Permintaan tidak sah."}, 403)
    credentials = _credentials(_request_payload())
    if credentials is None:
        return _reply({
            "error": "Masukkan emel yang sah dan kata laluan sekurang-kurangnya 8 aksara."
        }, 400)
    try:
        auth = _auth_configuration()
        if auth is None:
            return _reply({"error": "Pendaftaran emel belum tersedia."}, 503)
        email, password = credentials
        status, result = _auth_post(auth, "signup", {
            "email": email,
            "password": password,
        })
        if status >= 400:
            # Keep duplicate-email and provider errors indistinguishable.
            return _reply({
                "error": "Pendaftaran belum berjaya. Semak emel dan kata laluan, kemudian cuba lagi."
            }, 400)
        auth_user_id = _auth_user_id(result)
        if auth_user_id and isinstance(result, dict) and result.get("access_token"):
            uid = _account_id(auth, auth_user_id)
            return _authenticated_response(auth, uid)
        # Hosted Supabase normally requires email confirmation before sign-in.
        # The account row is created only after a verified sign-in.
        return _reply({
            "registered": True,
            "confirmation_required": True,
            "message": "Semak emel untuk pengesahan. Selepas itu, kembali ke sini dan log masuk."
        }, 202)
    except IdentityConflict:
        return _reply({
            "error": "Emel ini telah dipautkan kepada akaun lain. Log masuk dengan akaun emel itu."
        }, 409)
    except Exception as exc:
        current_app.logger.warning("Web email registration unavailable: %s",
                                   type(exc).__name__)
        return _reply({"error": "Pendaftaran emel tergendala. Cuba lagi sebentar lagi."}, 503)


@bp.post("/api/auth/email/login")
def email_login():
    if not _same_origin():
        return _reply({"error": "Permintaan tidak sah."}, 403)
    credentials = _credentials(_request_payload())
    if credentials is None:
        return _reply({
            "error": "Masukkan emel yang sah dan kata laluan sekurang-kurangnya 8 aksara."
        }, 400)
    try:
        auth = _auth_configuration()
        if auth is None:
            return _reply({"error": "Log masuk emel belum tersedia."}, 503)
        email, password = credentials
        status, result = _auth_post(auth, "token?grant_type=password", {
            "email": email,
            "password": password,
        })
        auth_user_id = _auth_user_id(result)
        if status != 200 or not auth_user_id:
            return _reply({
                "error": "Emel/kata laluan tidak sah atau emel belum disahkan."
            }, 401)
        uid = _account_id(auth, auth_user_id)
        return _authenticated_response(auth, uid)
    except IdentityConflict:
        return _reply({"error": "Pautan emel akaun ini memerlukan bantuan admin."}, 409)
    except Exception as exc:
        current_app.logger.warning("Web email login unavailable: %s",
                                   type(exc).__name__)
        return _reply({"error": "Log masuk emel tergendala. Cuba lagi sebentar lagi."}, 503)


@bp.post("/api/auth/email/link")
def email_link():
    if not _same_origin():
        return _reply({"error": "Permintaan tidak sah."}, 403)
    config = _config()
    if not config or config.get("account_backend") != "supabase":
        return _reply({"error": "Pautan emel belum tersedia."}, 503)
    uid = verify_session_ticket(
        request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None or uid >= TELEGRAM_ID_LIMIT:
        return _reply({"error": "Log masuk Telegram dahulu untuk pautkan emel."}, 401)
    try:
        current_account = _lookup(config, uid)
        if not current_account or current_account.get("telegram_user_id") != uid:
            return _reply({"error": "Akaun Telegram tidak dapat disahkan."}, 403)
        credentials = _credentials(_request_payload())
        if credentials is None:
            return _reply({
                "error": "Masukkan emel yang sah dan kata laluan sekurang-kurangnya 8 aksara."
            }, 400)
        auth = _auth_configuration()
        if auth is None:
            return _reply({"error": "Pautan emel belum tersedia."}, 503)
        email, password = credentials

        # Existing credentials must be proven by Supabase before they can be
        # attached to the current Telegram account.
        status, result = _auth_post(auth, "token?grant_type=password", {
            "email": email,
            "password": password,
        })
        auth_user_id = _auth_user_id(result) if status == 200 else None
        if not auth_user_id:
            # If this is a new email, create its Supabase identity. With hosted
            # confirmation enabled, the user returns and submits the link again.
            signup_status, signup = _auth_post(auth, "signup", {
                "email": email,
                "password": password,
            })
            if signup_status < 400:
                auth_user_id = _auth_user_id(signup)
                if not (auth_user_id and isinstance(signup, dict)
                        and signup.get("access_token")):
                    return _reply({
                        "confirmation_required": True,
                        "message": "Semak emel untuk pengesahan. Selepas itu, log masuk Telegram dan ulangi pautan."
                    }, 202)
            else:
                return _reply({
                    "error": "Tidak dapat mengesahkan emel. Jika emel sudah berdaftar, semak kata laluan."
                }, 401)

        linked_uid = _account_id(auth, auth_user_id, uid)
        if linked_uid != uid:
            return _reply({"error": "Emel ini terikat pada akaun lain."}, 409)
        return _reply({"linked": True})
    except IdentityConflict:
        return _reply({
            "error": "Emel ini sudah digunakan untuk akaun Web berasingan. Hubungi admin sebelum menggabungkan akaun."
        }, 409)
    except Exception as exc:
        current_app.logger.warning("Web email account link unavailable: %s",
                                   type(exc).__name__)
        return _reply({"error": "Pautan emel tergendala. Cuba lagi sebentar lagi."}, 503)
