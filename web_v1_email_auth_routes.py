"""Email/password login for the production CikguLaju Web.

Passwords are handled only by Supabase Auth. A verified Auth UUID maps to one
existing Telegram account or to a reserved Web-only account key. Browser input
never selects an account key.
"""
import json
import os
import re
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, make_response, request

from web_v1_telegram_auth_routes import COOKIE, _config as telegram_config, _lookup
from web_v1_sessions import issue_session_ticket, verify_session_ticket

email_auth_blueprint = Blueprint("web_v1_email_auth", __name__)
MAX_BODY = 4096


def _config():
    config = telegram_config()
    if (not config or config.get("account_backend") != "supabase"
            or os.environ.get("CIKGULAJU_WEB_EMAIL_AUTH_ENABLED") != "1"):
        return None
    publishable = (os.environ.get("SUPABASE_PUBLISHABLE_KEY")
                   or os.environ.get("SUPABASE_ANON_KEY") or "")
    redirect_url = os.environ.get("CIKGULAJU_WEB_EMAIL_REDIRECT_URL", "")
    parsed = urlsplit(redirect_url)
    if (not config.get("supabase_url", "").startswith("https://")
            or len(publishable) < 20
            or parsed.scheme != "https" or not parsed.hostname or parsed.port is not None
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ("", "/", "/")):
        return None
    origin = f"https://{parsed.netloc}"
    result = {**config, "publishable_key": publishable,
              "email_redirect_url": redirect_url.rstrip("/"),
              "email_origin": origin, "email_host": parsed.netloc}
    if not _settings_ready(result):
        return None
    return result


@email_auth_blueprint.get("/api/auth/email/capabilities")
def email_auth_capabilities():
    return jsonify({"email_auth_enabled": _config() is not None})


def _same_origin(config):
    return (request.headers.get("Origin") == config["email_origin"]
            and request.host == config["email_host"]
            and request.headers.get("Sec-Fetch-Site", "same-origin")
            in ("same-origin", "none"))


def _body():
    if (not request.is_json or request.content_length is None
            or request.content_length <= 0 or request.content_length > MAX_BODY):
        return None
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def _credentials(body):
    if not isinstance(body, dict) or set(body) != {"email", "password"}:
        return None
    email, password = body.get("email"), body.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return None
    email = email.strip().lower()
    if (len(email) > 254 or not re.fullmatch(
            r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+",
            email)
            or not 8 <= len(password) <= 128 or "\x00" in password):
        return None
    return email, password


def _read_json(response, *, limit=16384):
    data = response.read(limit + 1)
    if len(data) > limit:
        raise RuntimeError("Oversized authentication response")
    if not data:
        return {}
    return json.loads(data)


def _settings_ready(config):
    """Require email signup and confirmation before offering this login path."""
    req = Request(config["supabase_url"].rstrip("/") + "/auth/v1/settings",
                  headers={"apikey": config["publishable_key"],
                           "Accept": "application/json"})
    try:
        with urlopen(req, timeout=5) as response:
            settings = _read_json(response, limit=4096)
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        return False
    providers = settings.get("external") if isinstance(settings, dict) else None
    return (isinstance(providers, dict) and providers.get("email") is True
            and settings.get("disable_signup") is False
            and settings.get("mailer_autoconfirm") is False)


def _auth_call(config, path, payload):
    url = config["supabase_url"].rstrip("/") + "/auth/v1/" + path
    req = Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                  headers={"apikey": config["publishable_key"],
                           "Content-Type": "application/json",
                           "Accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, _read_json(response)
    except HTTPError as exc:
        try:
            return exc.code, _read_json(exc)
        except Exception:
            return exc.code, {}
    except (URLError, OSError, ValueError, TypeError):
        return 503, {}


def _service_headers(config):
    key = config.get("supabase_key", "")
    if not isinstance(key, str) or len(key) < 20:
        raise RuntimeError("Account backend unavailable")
    headers = {"apikey": key, "Accept": "application/json",
               "Content-Type": "application/json"}
    # Modern sb_secret_ keys are opaque API keys, not JWT bearer tokens.
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    return headers


def _rpc(config, name, payload):
    url = config["supabase_url"].rstrip("/") + "/rest/v1/rpc/" + name
    req = Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                  headers=_service_headers(config))
    try:
        with urlopen(req, timeout=10) as response:
            return _read_json(response)
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        raise RuntimeError("Email account mapping unavailable") from None


def _verified_auth_user(payload, email):
    user = payload.get("user") if isinstance(payload.get("user"), dict) else payload
    if not isinstance(user, dict):
        return None
    raw_id = user.get("id")
    try:
        auth_id = str(uuid.UUID(raw_id))
    except (TypeError, ValueError, AttributeError):
        return None
    if (auth_id != raw_id or not isinstance(user.get("email"), str)
            or user["email"].strip().lower() != email
            or not (user.get("email_confirmed_at") or user.get("confirmed_at"))):
        return None
    return auth_id


def _set_session(response, config, account_id):
    ticket = issue_session_ticket(account_id, config["CIKGULAJU_WEB_SESSION_SECRET"])
    response.set_cookie(COOKIE, ticket, secure=True, httponly=True,
                        samesite="Lax", max_age=43200, path="/")
    response.headers["Cache-Control"] = "no-store"
    return response


def _finish_email_login(config, payload, email):
    auth_id = _verified_auth_user(payload, email)
    if auth_id is None:
        return None
    account_id = _rpc(config, "ensure_web_email_account", {
        "p_auth_user_id": auth_id, "p_email": email,
    })
    if isinstance(account_id, list) and len(account_id) == 1:
        account_id = next(iter(account_id[0].values()), None)
    if isinstance(account_id, dict):
        account_id = next(iter(account_id.values()), None)
    try:
        account_id = int(account_id)
    except (TypeError, ValueError):
        raise RuntimeError("Email account registration was not confirmed") from None
    if account_id <= 0:
        raise RuntimeError("Email account registration was not confirmed")
    account = _lookup(config, account_id)
    if not account or account.get("telegram_user_id") != account_id:
        raise RuntimeError("Email account lookup was not confirmed")
    return account_id


def _session_uid(config):
    return verify_session_ticket(request.cookies.get(COOKIE),
                                 config["CIKGULAJU_WEB_SESSION_SECRET"])


@email_auth_blueprint.post("/api/auth/email/signup")
def email_signup():
    config = _config()
    if config is None:
        return jsonify({"error": "Pendaftaran e-mel belum tersedia."}), 503
    if not _same_origin(config):
        return jsonify({"error": "Permintaan rentas laman ditolak."}), 403
    credentials = _credentials(_body())
    if credentials is None:
        return jsonify({"error": "Masukkan e-mel sah dan kata laluan sekurang-kurangnya 8 aksara."}), 400
    email, password = credentials
    status, answer = _auth_call(
        config,
        "signup?" + urlencode({"redirect_to": config["email_redirect_url"]}),
        {"email": email, "password": password},
    )
    if status not in (200, 201):
        # Avoid exposing whether an address is already registered.
        return jsonify({"accepted": True,
                        "message": "Jika alamat ini boleh didaftarkan, pautan pengesahan akan dihantar. Semak e-mel anda."}), 202
    return jsonify({"accepted": True,
                    "message": "Akaun dihantar untuk pengesahan. Semak e-mel sebelum log masuk."}), 202


@email_auth_blueprint.post("/api/auth/email/login")
def email_login():
    config = _config()
    if config is None:
        return jsonify({"error": "Log masuk e-mel belum tersedia."}), 503
    if not _same_origin(config):
        return jsonify({"error": "Permintaan rentas laman ditolak."}), 403
    credentials = _credentials(_body())
    if credentials is None:
        return jsonify({"error": "E-mel atau kata laluan tidak sah."}), 400
    email, password = credentials
    status, answer = _auth_call(config, "token?grant_type=password",
                                {"email": email, "password": password})
    if status != 200:
        detail = str(answer.get("msg") or answer.get("message") or "").lower()
        if "confirm" in detail or "verify" in detail:
            return jsonify({"error": "Sahkan alamat e-mel melalui pautan yang dihantar sebelum log masuk."}), 403
        return jsonify({"error": "E-mel atau kata laluan tidak sah."}), 401
    if _verified_auth_user(answer, email) is None:
        return jsonify({"error": "Sahkan alamat e-mel sebelum log masuk."}), 403
    try:
        account_id = _finish_email_login(config, answer, email)
    except Exception:
        return jsonify({"error": "Akaun belum dapat disahkan. Cuba lagi sebentar."}), 503
    response = make_response(jsonify({"authenticated": True}), 200)
    return _set_session(response, config, account_id)


@email_auth_blueprint.post("/api/auth/email/reset")
def email_password_reset():
    config = _config()
    if config is None:
        return jsonify({"error": "Tetapan semula kata laluan belum tersedia."}), 503
    if not _same_origin(config):
        return jsonify({"error": "Permintaan rentas laman ditolak."}), 403
    body = _body()
    email = body.get("email") if isinstance(body, dict) and set(body) == {"email"} else None
    if not isinstance(email, str) or len(email.strip()) > 254:
        return jsonify({"error": "Masukkan alamat e-mel yang sah."}), 400
    email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"error": "Masukkan alamat e-mel yang sah."}), 400
    _auth_call(config, "recover?" + urlencode({"redirect_to": config["email_redirect_url"]}),
               {"email": email})
    return jsonify({"accepted": True,
                    "message": "Jika akaun e-mel wujud, arahan tetapan semula akan dihantar."}), 202


@email_auth_blueprint.post("/api/auth/email/password")
def email_password_change():
    config = _config()
    if config is None:
        return jsonify({"error": "Tetapan kata laluan belum tersedia."}), 503
    if not _same_origin(config):
        return jsonify({"error": "Permintaan rentas laman ditolak."}), 403
    body = _body()
    if not isinstance(body, dict) or set(body) != {"access_token", "password"}:
        return jsonify({"error": "Pautan tetapan semula tidak sah atau tamat."}), 400
    token, password = body.get("access_token"), body.get("password")
    if (not isinstance(token, str) or not 30 < len(token) < 8192
            or not isinstance(password, str) or not 8 <= len(password) <= 128
            or "\x00" in password):
        return jsonify({"error": "Pautan tetapan semula atau kata laluan tidak sah."}), 400
    user_req = Request(config["supabase_url"].rstrip("/") + "/auth/v1/user",
                       headers={"apikey": config["publishable_key"],
                                "Authorization": "Bearer " + token,
                                "Accept": "application/json"})
    try:
        with urlopen(user_req, timeout=10) as response:
            auth_user = _read_json(response)
        auth_id = _verified_auth_user({"user": auth_user},
                                      str(auth_user.get("email") or "").lower())
        if auth_id is None:
            return jsonify({"error": "Pautan tetapan semula tidak sah atau tamat."}), 401
        update_req = Request(
            config["supabase_url"].rstrip("/") + "/auth/v1/user",
            data=json.dumps({"password": password}).encode("utf-8"),
            method="PUT",
            headers={"apikey": config["publishable_key"],
                     "Authorization": "Bearer " + token,
                     "Content-Type": "application/json",
                     "Accept": "application/json"},
        )
        with urlopen(update_req, timeout=10) as response:
            _read_json(response)
    except HTTPError as exc:
        if exc.code in (400, 401, 403):
            return jsonify({"error": "Pautan tetapan semula tidak sah atau tamat."}), 401
        return jsonify({"error": "Kata laluan belum dapat dikemas kini."}), 503
    except (URLError, OSError, ValueError, TypeError):
        return jsonify({"error": "Kata laluan belum dapat dikemas kini."}), 503
    return jsonify({"updated": True,
                    "message": "Kata laluan berjaya ditetapkan. Log masuk dengan e-mel anda."}), 200


@email_auth_blueprint.get("/api/auth/email/link-status")
def email_link_status():
    config = _config()
    if config is None:
        return jsonify({"error": "Pemautan e-mel belum tersedia."}), 503
    uid = _session_uid(config)
    if uid is None:
        return jsonify({"error": "Log masuk Telegram diperlukan."}), 401
    if uid >= 1000000000000000000:
        return jsonify({"can_link": False, "linked": False,
                        "message": "Akaun e-mel ini tidak menggunakan ID Telegram."})
    try:
        account = _lookup(config, uid)
        if not account or account.get("telegram_user_id") != uid:
            return jsonify({"error": "Akaun Telegram tidak dapat disahkan."}), 403
        query = urlencode({"select": "email,status", "account_user_id": "eq." + str(uid),
                           "limit": "2"})
        req = Request(config["supabase_url"].rstrip("/") + "/rest/v1/web_email_identities?" + query,
                      headers=_service_headers(config))
        with urlopen(req, timeout=8) as result:
            rows = _read_json(result, limit=4096)
        if not isinstance(rows, list) or len(rows) > 1:
            raise RuntimeError("Ambiguous email link status")
        if rows and rows[0].get("status") == "active":
            return jsonify({"can_link": False, "linked": True,
                            "email": rows[0].get("email")})
        return jsonify({"can_link": True, "linked": False})
    except Exception:
        return jsonify({"error": "Status e-mel tidak dapat disahkan."}), 503


@email_auth_blueprint.post("/api/auth/email/link")
def email_link():
    config = _config()
    if config is None:
        return jsonify({"error": "Pemautan e-mel belum tersedia."}), 503
    if not _same_origin(config):
        return jsonify({"error": "Permintaan rentas laman ditolak."}), 403
    uid = _session_uid(config)
    if uid is None or uid >= 1000000000000000000:
        return jsonify({"error": "Log masuk Telegram diperlukan untuk memautkan e-mel."}), 401
    credentials = _credentials(_body())
    if credentials is None:
        return jsonify({"error": "Masukkan e-mel sah dan kata laluan sekurang-kurangnya 8 aksara."}), 400
    email, password = credentials
    try:
        account = _lookup(config, uid)
        if not account or account.get("telegram_user_id") != uid:
            return jsonify({"error": "Akaun Telegram tidak dapat disahkan."}), 403
    except Exception:
        return jsonify({"error": "Akaun Telegram tidak dapat disahkan."}), 503

    status, answer = _auth_call(config, "token?grant_type=password",
                                {"email": email, "password": password})
    if status == 200:
        auth_id = _verified_auth_user(answer, email)
        if auth_id is None:
            return jsonify({"error": "Sahkan alamat e-mel sebelum memautkannya."}), 403
    else:
        detail = str(answer.get("msg") or answer.get("message") or "").lower()
        if "confirm" in detail or "verify" in detail:
            return jsonify({"error": "Sahkan alamat e-mel dahulu, kemudian cuba pautkan semula."}), 403
        signup_status, signup = _auth_call(
            config,
            "signup?" + urlencode({"redirect_to": config["email_redirect_url"]}),
            {"email": email, "password": password},
        )
        if signup_status not in (200, 201):
            return jsonify({"error": "E-mel sudah digunakan atau pendaftaran belum tersedia. Semak kata laluan dan cuba lagi."}), 409
        user = signup.get("user") if isinstance(signup.get("user"), dict) else signup
        if user.get("identities") == []:
            return jsonify({"error": "E-mel ini sudah berdaftar. Log masuk dengan e-mel itu dahulu."}), 409
        # Do not reserve the e-mail against the Telegram account until the
        # owner has confirmed it. The user returns here and authenticates the
        # confirmed password before the mapping is committed.
        return jsonify({"pending": True,
                        "message": "Pengesahan dihantar ke e-mel. Selepas mengesahkan alamat, kembali ke akaun Telegram ini dan tekan Pautkan E-mel sekali lagi."}), 202

    try:
        _rpc(config, "link_verified_web_email", {
            "p_auth_user_id": auth_id, "p_email": email,
            "p_telegram_user_id": uid,
        })
    except Exception:
        return jsonify({"error": "Alamat e-mel ini telah dipautkan ke akaun lain atau pemautan belum dapat disahkan."}), 409
    return jsonify({"linked": True,
                    "message": "E-mel berjaya dipautkan. E-mel dan Telegram kini membuka akaun yang sama."}), 200
