"""Private CikguLaju Web feedback, reusing Telegram's Supabase feedback table.

Only the server-side service key can access the shared bot_user_feedback rows.
Registered users may submit/view *their own* feedback; admin can review all.
No browser-supplied user IDs, credit charges, public feedback or DB migrations.
"""
from datetime import datetime, timedelta, timezone
import json
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPSHandler, build_opener

from flask import Blueprint, current_app, jsonify, request
from web.teacher_profile_routes import _auth
from web.admin_usage_web import allowed_admin_ids
from web.web_login_analytics import _NoRedirect

bp = Blueprint("cikgulaju_web_feedback", __name__)
CATEGORIES = ("Umum", "Cadangan", "Masalah RPH", "Masalah RPT", "Masalah Web")
STATUSES = ("baru", "dibaca", "selesai")
MAX_MESSAGE = 1500
MAX_REQUEST = 6000
MAX_ROWS = 50
MAX_RESPONSE = 131072


class FeedbackUnavailable(Exception):
    pass


def _url_and_headers(conf):
    if not isinstance(conf, dict) or conf.get("account_backend") != "supabase":
        raise FeedbackUnavailable("Private feedback backend not configured")
    base, key = conf.get("supabase_url", ""), conf.get("supabase_key", "")
    if not isinstance(base, str) or not isinstance(key, str) or len(key) < 20:
        raise FeedbackUnavailable("Private feedback backend not configured")
    parsed = urlsplit(base)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.port is not None or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment):
        raise FeedbackUnavailable("Invalid private feedback endpoint")
    headers = {"apikey": key, "Accept": "application/json", "Content-Type": "application/json"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    return base.rstrip("/") + "/rest/v1/bot_user_feedback", headers


def _db(conf, method, params=None, payload=None, *, opener=None):
    """Bounded, no-redirect PostgREST call with server-owned identity."""
    if method not in ("GET", "POST", "PATCH"):
        raise ValueError("Unsupported feedback operation")
    url, headers = _url_and_headers(conf)
    if params:
        url += "?" + urlencode(params)
    if payload is not None:
        headers["Prefer"] = "return=representation"
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    else:
        raw = None
    req = Request(url, data=raw, headers=headers, method=method)
    http = opener or build_opener(HTTPSHandler(), _NoRedirect())
    try:
        with http.open(req, timeout=5) as resp:
            if resp.status not in (200, 201):
                raise FeedbackUnavailable("Unexpected feedback storage response")
            content = resp.read(MAX_RESPONSE + 1)
            if len(content) > MAX_RESPONSE:
                raise FeedbackUnavailable("Feedback response too large")
    except Exception as exc:
        raise FeedbackUnavailable("Feedback storage unavailable") from exc
    try:
        data = json.loads(content.decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError("Expected a list of feedback entries")
        return data
    except (ValueError, UnicodeError) as exc:
        raise FeedbackUnavailable("Invalid feedback storage response") from exc


def _own_rows(conf, uid, *, after=None, limit=20):
    params = {"select": "id,category,feedback_text,created_at,status",
              "chat_id": "eq." + str(uid), "order": "id.desc", "limit": str(limit)}
    if after is not None:
        params["created_at"] = "gte." + after
    return _db(conf, "GET", params)


def _visible(row, *, admin=False):
    if not isinstance(row, dict):
        raise FeedbackUnavailable("Invalid feedback record")
    item = {k: row[k] for k in ("id", "category", "feedback_text", "created_at", "status")}
    if admin:
        item["chat_id"] = str(row["chat_id"])
    return item


@bp.after_request
def protect_feedback(resp):
    resp.headers["Cache-Control"] = "no-store, private"
    resp.headers["Vary"] = "Cookie"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@bp.get("/api/web/feedback")
def my_feedback():
    conf, uid, error = _auth()
    if error:
        return error
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    try:
        return jsonify({"items": [_visible(row) for row in _own_rows(conf, uid)]})
    except FeedbackUnavailable:
        current_app.logger.exception("Private Web feedback list unavailable")
        return jsonify({"error": "Komen belum dapat dimuatkan"}), 503


@bp.post("/api/web/feedback")
def submit_feedback():
    conf, uid, error = _auth()
    if error:
        return error
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    if request.headers.get("Origin") != "https://" + request.host:
        return jsonify({"error": "Asal permintaan tidak sah"}), 403
    if (not request.is_json or request.content_length is None
            or not 0 < request.content_length <= MAX_REQUEST):
        return jsonify({"error": "Format atau saiz komen tidak sah"}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"category", "message"}:
        return jsonify({"error": "Maklumat komen tidak sah"}), 400
    category, message = payload["category"], payload["message"]
    if category not in CATEGORIES or not isinstance(message, str):
        return jsonify({"error": "Kategori atau komen tidak sah"}), 400
    cleaned = " ".join(message.split())
    if not 10 <= len(cleaned) <= MAX_MESSAGE:
        return jsonify({"error": "Tulis komen antara 10 hingga 1,500 aksara"}), 400
    try:
        hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        recent = _own_rows(conf, uid, after=hour_ago, limit=4)
        if len(recent) >= 3:
            return jsonify({"error": "Had 3 komen sejam telah dicapai. Cuba semula kemudian."}), 429
        created = _db(conf, "POST", payload={
            "chat_id": str(uid), "category": category, "feedback_text": cleaned,
        })
        if len(created) != 1 or type(created[0].get("id")) is not int:
            raise FeedbackUnavailable("Feedback insert not confirmed")
        return jsonify({"ok": True, "id": created[0]["id"],
                        "status": "baru", "message": "Komen berjaya dihantar kepada admin."}), 201
    except FeedbackUnavailable:
        current_app.logger.exception("Private Web feedback submission unavailable")
        return jsonify({"error": "Komen belum dapat disimpan. Cuba semula; tiada kredit dipotong."}), 503


@bp.get("/api/web/admin/feedback")
def admin_feedback():
    conf, uid, error = _auth()
    if error:
        return error
    if uid not in allowed_admin_ids():
        return jsonify({"error": "Akses admin diperlukan"}), 403
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    try:
        rows = _db(conf, "GET", {
            "select": "id,chat_id,category,feedback_text,created_at,status",
            "order": "id.desc", "limit": str(MAX_ROWS),
        })
        return jsonify({"items": [_visible(row, admin=True) for row in rows],
                        "limited": len(rows) == MAX_ROWS})
    except FeedbackUnavailable:
        current_app.logger.exception("Private admin feedback list unavailable")
        return jsonify({"error": "Senarai komen admin belum tersedia"}), 503


@bp.patch("/api/web/admin/feedback/<int:feedback_id>")
def admin_feedback_status(feedback_id):
    """Admin-only status management on Telegram's existing feedback ledger.

    Never trust a browser-supplied Telegram ID. No modification to comment
    text, owner, date, credits, payments, or the global account records.
    """
    conf, uid, error = _auth()
    if error:
        return error
    if uid not in allowed_admin_ids():
        return jsonify({"error": "Akses admin diperlukan"}), 403
    if request.args or feedback_id <= 0 or feedback_id > 9223372036854775807:
        return jsonify({"error": "ID komen tidak sah"}), 400
    if request.headers.get("Origin") != "https://" + request.host:
        return jsonify({"error": "Asal permintaan tidak sah"}), 403
    if (not request.is_json or request.content_length is None
            or not 0 < request.content_length <= 256):
        return jsonify({"error": "Format permintaan tidak sah"}), 400
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"status"}:
        return jsonify({"error": "Status komen tidak sah"}), 400
    next_status = body["status"]
    if not isinstance(next_status, str) or next_status not in STATUSES:
        return jsonify({"error": "Status komen tidak sah"}), 400
    try:
        changed = _db(conf, "PATCH",
                      {"id": f"eq.{feedback_id}", "select": "id,status"},
                      {"status": next_status})
        if not changed:
            return jsonify({"error": "Komen tidak ditemui"}), 404
        if (len(changed) != 1 or changed[0].get("id") != feedback_id
                or changed[0].get("status") != next_status):
            raise FeedbackUnavailable("Status update not confirmed")
        return jsonify({"ok": True, "id": feedback_id, "status": next_status})
    except FeedbackUnavailable:
        current_app.logger.exception("Private admin feedback update unavailable")
        return jsonify({"error": "Status komen belum dapat disimpan"}), 503
