"""Private, read-only CikguLaju user directory for verified Web admins.

The browser never accesses Supabase credentials, auth.users or numeric email
identity keys directly. An explicitly allowlisted admin session is rechecked
against the authoritative account table for every query. Search and status
pagination occur inside a service-role-only database RPC, not in browser JS.
"""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPSHandler, build_opener

from flask import Blueprint, current_app, jsonify, request

from web.admin_usage_web import _api_config, allowed_admin_ids
from web.web_login_analytics import _NoRedirect
from web_v1_sessions import verify_session_ticket
from web_v1_telegram_auth_routes import COOKIE, _config, _lookup


bp = Blueprint("cikgulaju_admin_users", __name__)
ALLOWED_STATUS = frozenset(("all", "free", "rakan", "langganan"))
PAGE_SIZE = 20
MAX_RESULT = 262144


@bp.after_request
def _private_headers(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _admin_users_data(conf, status, search, page, *, opener=None):
    base, headers = _api_config(conf)
    payload = {"p_status": status, "p_search": search, "p_page": page}
    req = Request(
        base + "/rest/v1/rpc/admin_user_directory",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        method="POST",
        headers={**headers, "Content-Type": "application/json"},
    )
    client = opener or build_opener(HTTPSHandler(), _NoRedirect())
    with client.open(req, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("Admin directory source rejected request")
        raw = response.read(MAX_RESULT + 1)
    if len(raw) > MAX_RESULT:
        raise RuntimeError("Admin directory exceeded safe response limit")
    result = json.loads(raw)
    if (not isinstance(result, dict)
            or type(result.get("total")) is not int or result["total"] < 0
            or type(result.get("page")) is not int or result["page"] != page
            or result.get("page_size") != PAGE_SIZE
            or not isinstance(result.get("items"), list)
            or len(result["items"]) > PAGE_SIZE):
        raise RuntimeError("Admin directory returned invalid data")
    safe = []
    for entry in result["items"]:
        if not isinstance(entry, dict):
            raise RuntimeError("Invalid admin directory item")
        if (entry.get("access_status") not in ("free", "rakan", "langganan")
                or entry.get("account_type") not in ("email", "telegram")):
            raise RuntimeError("Invalid user classification")
        # Do not return unrecognized columns from a privileged query.
        safe.append({key: entry.get(key) for key in (
            "account_type", "telegram_id", "email", "display_name",
            "registered_at", "last_login_at", "access_status",
            "subscription_expires_at", "trial_remaining",
        )})
    return {"items": safe, "total": result["total"], "page": page,
            "page_size": PAGE_SIZE, "more": (page + 1) * PAGE_SIZE < result["total"]}


@bp.get("/api/web/admin/users")
def admin_users():
    conf = _config()
    if conf is None:
        return jsonify({"error": "Sambungan akaun belum tersedia"}), 503
    uid = verify_session_ticket(
        request.cookies.get(COOKIE), conf["CIKGULAJU_WEB_SESSION_SECRET"])
    if type(uid) is not int or uid <= 0:
        return jsonify({"error": "Sila log masuk"}), 401
    if uid not in allowed_admin_ids():
        return jsonify({"error": "Akses admin diperlukan"}), 403
    if conf.get("account_backend") != "supabase":
        return jsonify({"error": "Senarai pengguna belum tersedia"}), 503

    args = request.args
    if set(args) - {"status", "search", "page"}:
        return jsonify({"error": "Penapis tidak sah"}), 400
    if any(len(args.getlist(key)) != 1 for key in args):
        return jsonify({"error": "Penapis tidak sah"}), 400
    status = args.get("status", "all")
    search = args.get("search", "").strip()
    page_raw = args.get("page", "0")
    if (status not in ALLOWED_STATUS or len(search) > 100
            or any(ord(char) < 32 or ord(char) == 127 for char in search)
            or not re.fullmatch(r"[0-9]{1,5}", page_raw)
            or int(page_raw) > 50000):
        return jsonify({"error": "Penapis tidak sah"}), 400
    try:
        account = _lookup(conf, uid)
        if not account or account.get("telegram_user_id") != uid:
            return jsonify({"error": "Akaun admin belum disahkan"}), 403
        return jsonify(_admin_users_data(conf, status, search, int(page_raw)))
    except (HTTPError, URLError, OSError, RuntimeError, ValueError,
            TypeError, KeyError, json.JSONDecodeError) as exc:
        current_app.logger.warning("Web admin directory unavailable: %s",
                                   type(exc).__name__)
        return jsonify({"error": "Senarai pengguna tidak dapat dimuatkan. Cuba semula."}), 503
