"""Production-native dual-proof Google <-> Telegram association (OFF by default).

Google's signed UUID cookie + the ORIGINAL Telegram Web signed cookie must
both be verified on this Web host. The teacher explicitly confirms an exact
credit-balance preview. The private SQL function atomically reconciles trials:
Google credits already consumed plus Telegram credits already consumed never
grant more than the shared ten free RPH generations. Existing lifetime and
subscriptions stay in their original Telegram tables and are NOT modified.

Never match accounts by email alone or rely on a staging/Render bridge.
"""
import json
from pathlib import Path

from flask import Blueprint, jsonify, request, make_response, redirect, send_file

from web.google_native_canonical_login_routes import _config as google_config
from web.native_google_principal_store import (
    PROD_SUPABASE, _headers, _read_json, read_google_principal,
    CanonicalAccountUnavailable,
)
from web_v1_canonical_sessions import (
    COOKIE as GOOGLE_COOKIE, verify_google_principal_ticket,
)
from web_v1_telegram_auth_routes import COOKIE as TELEGRAM_COOKIE, _lookup
from web_v1_sessions import verify_session_ticket
from urllib.request import Request

bp = Blueprint("cikgulaju_google_native_link", __name__)


def _verified_pair():
    cfg = google_config()
    if cfg is None:
        return None, None, (jsonify({"error": "Google login belum diaktifkan"}), 503)
    google_id = verify_google_principal_ticket(
        request.cookies.get(GOOGLE_COOKIE), cfg["secret"])
    telegram_id = verify_session_ticket(
        request.cookies.get(TELEGRAM_COOKIE), cfg["secret"])
    if google_id is None or telegram_id is None:
        return None, None, (jsonify({
            "error": "Log masuk Google dan Telegram diperlukan sebelum memautkan akaun"}), 401)
    try:
        principal = read_google_principal(cfg, google_id)
        account = _lookup(cfg, telegram_id)
    except (CanonicalAccountUnavailable, ValueError, TypeError, KeyError, OSError):
        return None, None, (jsonify({
            "error": "Identiti kedua-dua akaun belum boleh disahkan"}), 503)
    if (not isinstance(account, dict)
            or account.get("authenticated") is not True
            or account.get("telegram_user_id") != telegram_id):
        return None, None, (jsonify({"error": "Akaun Telegram tidak disahkan"}), 403)
    linked = principal["legacy_telegram_user_id"]
    if linked is not None and linked != telegram_id:
        return None, None, (jsonify({
            "error": "Akaun Google telah dipautkan kepada Telegram lain"}), 409)
    telegram_remaining = account.get("free_remaining")
    if type(telegram_remaining) is not int or not 0 <= telegram_remaining <= 10:
        return None, None, (jsonify({"error": "Baki Telegram tidak sah"}), 503)
    return cfg, {"google": principal, "telegram_uid": telegram_id,
                 "telegram_remaining": telegram_remaining}, None


def _preview(pair):
    google = pair["google"]
    tg = pair["telegram_remaining"]
    if google["legacy_telegram_user_id"] is not None:
        return {"linked": True, "login_id": google["login_id"],
                "telegram_remaining": tg,
                "after_link_remaining": tg,
                "already_linked": True}
    remaining = google["google_only_trial_remaining"]
    if type(remaining) is not int or not 0 <= remaining <= 10:
        raise ValueError("Google trial balance unavailable")
    expected = max(0, tg - (10 - remaining))
    return {"linked": False, "login_id": google["login_id"],
            "google_remaining": remaining,
            "telegram_remaining": tg,
            "after_link_remaining": expected,
            "credits_used_on_google": 10 - remaining,
            "explicit_confirmation_required": True}


@bp.after_request
def protect(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/google-link-telegram")
def page():
    cfg = google_config()
    if cfg is None:
        return jsonify({"error": "Pautan akaun belum diaktifkan"}), 503
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    if verify_google_principal_ticket(
            request.cookies.get(GOOGLE_COOKIE), cfg["secret"]) is None:
        return redirect("/google-login", code=303)
    return make_response(send_file(
        Path(__file__).with_name("google_native_link.html"),
        mimetype="text/html", max_age=0))


@bp.get("/api/auth/google-native/link-preview")
def preview():
    cfg, pair, problem = _verified_pair()
    if problem is not None:
        return problem
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    try:
        return jsonify(_preview(pair))
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Baki tidak dapat disahkan"}), 503


@bp.post("/api/auth/google-native/link-telegram")
def link():
    cfg, pair, problem = _verified_pair()
    if problem is not None:
        return problem
    if (request.headers.get("Origin") != cfg["origin"]
            or request.headers.get("Sec-Fetch-Site", "same-origin")
            not in ("same-origin", "none")):
        return jsonify({"error": "Asal permintaan tidak sah"}), 403
    if (not request.is_json or request.content_length is None
            or request.content_length > 512):
        return jsonify({"error": "Permintaan tidak sah"}), 400
    data = request.get_json(silent=True)
    if (not isinstance(data, dict)
            or set(data) != {"confirm", "google_remaining", "telegram_remaining"}
            or data.get("confirm") is not True
            or type(data.get("google_remaining")) is not int
            or type(data.get("telegram_remaining")) is not int):
        return jsonify({"error": "Persetujuan dan baki yang disahkan diperlukan"}), 400
    try:
        current = _preview(pair)
        if current["linked"]:
            return jsonify({"linked": True, "already_linked": True,
                            "telegram_remaining": current["telegram_remaining"]})
        if (data["google_remaining"] != current["google_remaining"]
                or data["telegram_remaining"] != current["telegram_remaining"]):
            return jsonify({"error": "Baki berubah. Sahkan baki terkini dahulu."}), 409
        backend = PROD_SUPABASE + "/rest/v1/rpc/link_native_google_telegram_principal"
        payload = {"p_principal_id": pair["google"]["account_id"],
                   "p_telegram_user_id": pair["telegram_uid"],
                   "p_merge_confirmed": True,
                   "p_expected_google_remaining": current["google_remaining"],
                   "p_expected_telegram_remaining": current["telegram_remaining"]}
        req = Request(backend, data=json.dumps(payload).encode("utf-8"),
                      headers={**_headers(cfg), "Content-Type": "application/json"},
                      method="POST")
        result = _read_json(req, limit=2048)
        if (not isinstance(result, dict)
                or result.get("linked") is not True
                or result.get("telegram_user_id") != pair["telegram_uid"]
                or type(result.get("telegram_remaining_after")) is not int
                or not 0 <= result["telegram_remaining_after"] <= 10):
            raise CanonicalAccountUnavailable("Link not confirmed")
        # Re-check BOTH independent records after the private transaction.
        revised = read_google_principal(cfg, pair["google"]["account_id"])
        new_telegram = _lookup(cfg, pair["telegram_uid"])
        if (revised["legacy_telegram_user_id"] != pair["telegram_uid"]
                or revised["google_only_trial_remaining"] is not None
                or not isinstance(new_telegram, dict)
                or new_telegram.get("authenticated") is not True
                or new_telegram.get("telegram_user_id") != pair["telegram_uid"]
                or new_telegram.get("free_remaining") != result["telegram_remaining_after"]):
            raise CanonicalAccountUnavailable("Link read-back not confirmed")
    except (CanonicalAccountUnavailable, ValueError, TypeError, KeyError, OSError):
        return jsonify({
            "error": "Pemautan belum dapat disahkan. Semak status sebelum cuba lagi."}), 503
    return jsonify({"linked": True,
                    "telegram_remaining": result["telegram_remaining_after"],
                    "already_linked": bool(result.get("replayed")),
                    "note": "Akaun digabungkan dengan pengesahan kedua-duanya. "
                            "Akses berbayar kekal pada rekod Telegram asal."})
