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
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen, HTTPSHandler, build_opener
from uuid import UUID
from io import BytesIO
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import Blueprint, request, jsonify, send_file
from web.web_login_analytics import _NoRedirect
from web.admin_usage_web import allowed_admin_ids

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
    parts = urlsplit(base)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or parts.port is not None or parts.path or parts.query or parts.fragment or len(key) < 20):
        raise RuntimeError("Shared Supabase not configured")
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {"apikey": key, "Accept": "application/json", "Content-Type": "application/json"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    req = Request(base + "/rest/v1/" + path, data=data, method=method, headers=headers)
    limit = 4 * 1024 * 1024 + 4096 if path.startswith("affiliate_claim_proofs?") else 131072
    with build_opener(HTTPSHandler(), _NoRedirect()).open(req, timeout=12) as result:
        blob = result.read(limit + 1)
        if len(blob) > limit:
            raise RuntimeError("Response too large")
        return json.loads(blob or b"null")


def capture_after_verified_login(uid, *, notify=True):
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
        if captured and notify:
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
        if not members:
            try:
                can_join = _overview(uid).get("open") is True
            except (RuntimeError, OSError):
                can_join = False
            return jsonify({"enabled": False, "can_join": can_join})
        if members[0].get("enabled") is not True:
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



MAX_PROOF = 2 * 1024 * 1024


def _rpc(name, **body):
    return _rest("POST", "rpc/" + name, body=body)


def _overview(uid):
    return _rpc("affiliate_overview", p_user=uid)


@bp.after_request
def _private_response(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _affiliate_identity(*, admin=False, write=False):
    uid = _auth_uid()
    if uid is None:
        return None, (jsonify(error="Sila log masuk semula."), 401)
    if admin and uid not in allowed_admin_ids():
        return None, (jsonify(error="Akses admin diperlukan."), 403)
    if write and request.headers.get("Origin") != WEB_ORIGIN:
        return None, (jsonify(error="Permintaan tidak sah."), 403)
    return uid, None


def _claim_result(data, success=200):
    errors = {
        "closed": (403, "Program affiliate belum dibuka."),
        "disabled": (403, "Akaun affiliate ini tidak aktif."),
        "invalid": (400, "Semak butiran yang diisi."),
        "balance": (409, "Baki mata tersedia tidak mencukupi."),
        "wallet_changed": (409, "Simpan dan sahkan semula nombor akaun TNG eWallet."),
        "account_required": (409, "Tuntutan ini memerlukan nombor akaun TNG eWallet. Jika masih menunggu, tolak tuntutan supaya affiliate boleh hantar semula."),
        "request_conflict": (409, "Maklumat tuntutan ini telah berubah. Muat semula dan semak sejarah tuntutan."),
        "missing": (404, "Tuntutan tidak dijumpai."),
        "status": (409, "Status telah berubah atau tuntutan sedang diproses oleh admin lain."),
        "reference_used": (409, "Rujukan transaksi ini sudah direkodkan."),
    }
    if not isinstance(data, dict):
        raise RuntimeError("Invalid affiliate response")
    if "error" in data:
        code, message = errors.get(data["error"], (503, "Tuntutan belum dapat diproses."))
        return jsonify(error=message), code
    return jsonify(data), success


def _confirmed_account_number(body):
    if not isinstance(body, dict) or body.get("confirmed") is not True:
        raise ValueError("Confirmation required")
    value = body.get("account_number")
    if not isinstance(value, str) or len(value) > 32:
        raise ValueError("Invalid account number")
    account_number = re.sub(r"[ -]", "", value.strip())
    if not re.fullmatch(r"[0-9]{12}", account_number):
        raise ValueError("Invalid account number")
    return account_number


def _json_body():
    if not request.is_json or not 0 < (request.content_length or 0) <= 4096:
        raise ValueError("Invalid JSON request")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Invalid JSON object")
    return data


@bp.get("/api/web/affiliate")
def affiliate_overview():
    uid, error = _affiliate_identity()
    return error if error is not None else _claim_result(_overview(uid))


@bp.post("/api/web/affiliate/wallet")
def affiliate_wallet():
    uid, error = _affiliate_identity(write=True)
    if error is not None:
        return error
    try:
        account_number = _confirmed_account_number(_json_body())
    except ValueError:
        return jsonify(error="Isi dan sahkan nombor akaun TNG eWallet (DuitNow) 12 digit."), 400
    return _claim_result(_rpc("affiliate_save_account", p_user=uid, p_account_number=account_number))


@bp.post("/api/web/affiliate/claims")
def affiliate_submit():
    uid, error = _affiliate_identity(write=True)
    if error is not None:
        return error
    try:
        body = _json_body()
        account_number = _confirmed_account_number(body)
        points = body.get("points")
        if not isinstance(points, str) or not re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,2})?", points) or Decimal(points) < 10:
            raise ValueError("Minimum claim")
        key = str(UUID(body.get("key", "")))
    except (ValueError, TypeError, AttributeError):
        return jsonify(error="Sahkan nombor akaun TNG eWallet dan masukkan sekurang-kurangnya 10 mata."), 400
    return _claim_result(_rpc("affiliate_submit_account_claim", p_user=uid, p_points=points, p_account_number=account_number, p_key=key), 201)


@bp.get("/api/web/admin/affiliate/claims")
def affiliate_admin_list():
    uid, error = _affiliate_identity(admin=True)
    if error is not None:
        return error
    if _overview(uid).get("open") is not True:
        return jsonify(open=False, items=[])
    status = request.args.get("status", "pending")
    page = request.args.get("page", "0")
    if status not in ("pending", "processing", "paid", "rejected") or not re.fullmatch(r"[0-9]{1,5}", page):
        return jsonify(error="Penapis tidak sah."), 400
    query = urlencode({"status": "eq." + status,
        "select": "id,user_id,points,account_number_snapshot,status,requested_at,reviewer_id,payment_reference,rejection_reason",
        "order": "requested_at.desc,id.desc", "limit": 26, "offset": int(page) * 25})
    items = _rest("GET", "affiliate_claims?" + query)
    return jsonify(open=True, items=items[:25], more=len(items) > 25, admin_id=str(uid))


@bp.get("/api/web/admin/affiliate/members")
def affiliate_admin_members():
    _, error = _affiliate_identity(admin=True)
    if error is not None:
        return error
    page = request.args.get("page", "0")
    if not re.fullmatch(r"[0-9]{1,5}", page):
        return jsonify(error="Halaman tidak sah."), 400
    return _claim_result(_rpc("affiliate_admin_members", p_page=int(page), p_page_size=25))


@bp.post("/api/web/admin/affiliate/claims/<uuid:claim_id>")
def affiliate_admin_review(claim_id):
    uid, error = _affiliate_identity(admin=True, write=True)
    if error is not None:
        return error
    if not 0 < (request.content_length or 0) <= MAX_PROOF + 32768:
        return jsonify(error="Had bukti bayaran ialah 2 MB."), 400
    action = request.form.get("action")
    reference = (request.form.get("reference") or "").strip().upper() or None
    reason = (request.form.get("reason") or "").strip() or None
    proof = content_type = None
    if action == "paid":
        file = request.files.get("proof")
        raw = file.read(MAX_PROOF + 1) if file is not None else b""
        signatures = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff", "application/pdf": b"%PDF-"}
        content_type = next((kind for kind, magic in signatures.items() if raw.startswith(magic)), None)
        if not content_type or len(raw) > MAX_PROOF:
            return jsonify(error="Muat naik bukti PNG, JPEG atau PDF sehingga 2 MB."), 400
        proof = "\\x" + raw.hex()
    return _claim_result(_rpc("affiliate_review_claim", p_claim=str(claim_id), p_admin=uid,
        p_action=action, p_reference=reference, p_reason=reason, p_content_type=content_type, p_proof=proof))


@bp.get("/api/web/admin/affiliate/claims/<uuid:claim_id>/proof")
def affiliate_admin_proof(claim_id):
    _, error = _affiliate_identity(admin=True)
    if error is not None:
        return error
    rows = _rest("GET", "affiliate_claim_proofs?" + urlencode({"claim_id":"eq." + str(claim_id),
                                                               "select":"content_type,content", "limit":1}))
    if not rows:
        return jsonify(error="Bukti tidak dijumpai."), 404
    row = rows[0]
    suffix = {"image/png":"png", "image/jpeg":"jpg", "application/pdf":"pdf"}[row["content_type"]]
    raw = bytes.fromhex(row["content"][2:])
    return send_file(BytesIO(raw), mimetype=row["content_type"], as_attachment=True,
                     download_name=f"Bukti-TNG-{claim_id}.{suffix}")


@bp.errorhandler(RuntimeError)
@bp.errorhandler(OSError)
def affiliate_unavailable(_):
    return jsonify(error="Rekod affiliate belum dapat dibaca. Cuba semula."), 503

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
