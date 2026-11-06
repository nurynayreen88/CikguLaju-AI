"""Private Web referral bridge using the same Supabase data and reward RPC as Telegram.

A signed short-lived HttpOnly cookie retains a first-touch referral across the
Telegram Login Widget redirect. The verified Telegram identity, not browser
input, is used for attribution. This never grants points; existing Telegram
payment approval continues to own reward allocation.
"""
import os
import re
import json
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import Blueprint, request, jsonify, make_response

bp = Blueprint("cikgulaju_web_referral", __name__)
REF_COOKIE = "cikgulaju_web_referral"
REF_AGE = 7 * 86400
REF_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,48}$")
WEB_ORIGIN = "https://cikgulaju-web.onrender.com"


def _signer():
    from web_v1_telegram_auth_routes import _config
    conf = _config()
    if not conf or len(conf.get("CIKGULAJU_WEB_SESSION_SECRET", "")) < 32:
        return None
    return URLSafeTimedSerializer(conf["CIKGULAJU_WEB_SESSION_SECRET"], salt="cikgulaju-referral-first-touch-v1")


def pending_referral():
    signer = _signer()
    if signer is None:
        return None
    try:
        code = signer.loads(request.cookies.get(REF_COOKIE, ""), max_age=REF_AGE)
    except (BadSignature, SignatureExpired, ValueError):
        return None
    return code if isinstance(code, str) and REF_PATTERN.fullmatch(code) else None


def _rest(method, path, *, body=None):
    from web_v1_telegram_auth_routes import _config
    conf = _config()
    if not conf or conf.get("account_backend") != "supabase":
        raise RuntimeError("Shared Supabase not available")
    base, key = conf["supabase_url"].rstrip("/"), conf["supabase_key"]
    if not base.startswith("https://") or len(key) < 20:
        raise RuntimeError("Shared Supabase not configured")
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    req = Request(base + "/rest/v1/" + path, data=data, method=method,
                  headers={"apikey": key, "Authorization": "Bearer " + key,
                           "Accept": "application/json", "Content-Type": "application/json"})
    with urlopen(req, timeout=8) as result:
        blob = result.read(131073)
        if len(blob) > 131072:
            raise RuntimeError("Response too large")
        return json.loads(blob or b"null")


def capture_after_verified_login(uid):
    """Call only after Telegram hash verification AND existing account lookup.

    Fail closed without blocking normal login. A DB RPC owns new-account,
    disabled member, self-referral and duplicate constraints.
    """
    code = pending_referral()
    if not code or type(uid) is not int or uid <= 0:
        return False
    try:
        result = _rest("POST", "rpc/referral_capture_signup",
                       body={"p_referred_user_id": uid, "p_referral_code": code})
        captured = isinstance(result, dict) and result.get("captured") is True
        if captured:
            # Already persisted once by the existing atomic signup RPC. Never
            # notify for old users or repeat logins.
            try:
                _notify_admin_new_web_referral(uid)
            except Exception as exc:
                print("WEB REFERRAL admin notice deferred:", type(exc).__name__, flush=True)
        return captured
    except Exception as exc:
        # Never log credentials/codes or interfere with the login session.
        print("WEB REFERRAL capture temporarily unavailable:", type(exc).__name__, flush=True)
        return False


def _notify_admin_new_web_referral(uid):
    """Only sent after a successful brand-new referral capture in Supabase."""
    from urllib.parse import urlsplit
    from urllib.error import URLError, HTTPError
    base = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    parts = urlsplit(base)
    if (parts.scheme != "https" or not parts.hostname or parts.port is not None
            or parts.username or parts.password or parts.path not in ("", "/")
            or parts.query or parts.fragment or len(token) < 32):
        raise RuntimeError("Telegram authoritative API unavailable")
    body = json.dumps({"telegram_user_id": uid}).encode("utf-8")
    req = Request(base.rstrip("/") + "/internal/referral/v1/new-web-signup-notify",
                  data=body, method="POST", headers={
                      "Authorization": "Bearer " + token,
                      "Content-Type": "application/json",
                      "Accept": "application/json",
                  })
    with urlopen(req, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError("Telegram admin notification unavailable")
        message = json.loads(response.read(2048))
        return message.get("notified") is True


def _auth_uid():
    from web_v1_telegram_auth_routes import _config, _lookup, COOKIE
    from web_v1_sessions import verify_session_ticket
    conf = _config()
    if not conf:
        return None
    uid = verify_session_ticket(request.cookies.get(COOKIE), conf["CIKGULAJU_WEB_SESSION_SECRET"])
    if type(uid) is not int or uid <= 0:
        return None
    user = _lookup(conf, uid)
    if not user or user.get("telegram_user_id") != uid:
        return None
    return uid


@bp.get("/api/web/referral")
def my_referral():
    try:
        uid = _auth_uid()
        if uid is None:
            return jsonify({"error": "authentication required"}), 401
        members = _rest("GET", "referral_members?" + urlencode({
            "referrer_user_id": "eq." + str(uid),
            "select": "referral_code,enabled", "limit": "1"}))
        if not members or members[0].get("enabled") is not True:
            return jsonify({"enabled": False})
        code = members[0]["referral_code"]
        if not isinstance(code, str) or not REF_PATTERN.fullmatch(code):
            return jsonify({"error": "invalid referral configuration"}), 503
        signups = _rest("GET", "referral_signups?" + urlencode({
            "referrer_user_id": "eq." + str(uid), "select": "referred_user_id", "limit": "10000"}))
        events = _rest("GET", "referral_point_events?" + urlencode({
            "referrer_user_id": "eq." + str(uid), "select": "points_delta", "limit": "10000"}))
        points = sum((Decimal(str(e["points_delta"])) for e in events), Decimal("0"))
        response = jsonify({"enabled": True, "link": WEB_ORIGIN + "/?ref=" + code,
                            "registered": len(signups), "paid": len(events),
                            "points": str(points.quantize(Decimal("0.01")))})
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Vary"] = "Cookie"
        return response
    except Exception as exc:
        print("WEB REFERRAL member lookup unavailable:", type(exc).__name__, flush=True)
        return jsonify({"error": "referral temporarily unavailable"}), 503


def install(app):
    app.register_blueprint(bp)

    @app.after_request
    def retain_first_touch_referral(response):
        # Only capture a link opened on the homepage. No untrusted redirects.
        if request.method != "GET" or request.path != "/" or response.status_code != 200:
            return response
        new_code = request.args.get("ref", "")
        signer = _signer()
        if signer and REF_PATTERN.fullmatch(new_code) and not pending_referral():
            response.set_cookie(REF_COOKIE, signer.dumps(new_code), max_age=REF_AGE,
                                httponly=True, secure=True, samesite="Lax", path="/")
            response.headers["Cache-Control"] = "no-store, private"
        return response
