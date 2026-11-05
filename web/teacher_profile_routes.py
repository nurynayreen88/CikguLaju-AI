"""Cookie-authenticated private profile and timetable endpoints for CikguLaju Web.

No user identifier accepted from browser. The Telegram session is the only
identity source, looked up against the existing account in Supabase.
"""
from flask import Blueprint, jsonify, make_response, request
from web_v1_telegram_auth_routes import COOKIE, _config, _lookup
from web_v1_sessions import verify_session_ticket
from web.teacher_profile_store import (
    ProfileConflict, ProfileUnavailable, ProfileValidation,
    get_profile, get_schedule, save_profile, save_schedule,
)

bp = Blueprint("teacher_profile_web", __name__)


@bp.after_request
def protect_response(resp):
    resp.headers["Cache-Control"] = "no-store, private"
    resp.headers["Vary"] = "Cookie"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


def _auth():
    conf = _config()
    if conf is None:
        return None, None, (jsonify({"error": "Konfigurasi akaun belum tersedia"}), 503)
    uid = verify_session_ticket(request.cookies.get(COOKIE),
                                conf["CIKGULAJU_WEB_SESSION_SECRET"])
    if type(uid) is not int or uid <= 0:
        return None, None, (jsonify({"error": "Sila log masuk"}), 401)
    if conf.get("account_backend") != "supabase":
        return None, None, (jsonify({"error": "Storan profil belum tersedia"}), 503)
    try:
        account = _lookup(conf, uid)
    except Exception:
        return None, None, (jsonify({"error": "Semakan akaun belum tersedia"}), 503)
    if not account or account.get("telegram_user_id") != uid:
        return None, None, (jsonify({"error": "Akaun berdaftar diperlukan"}), 403)
    return conf, uid, None


def _body():
    # Same-origin guard on cookie-authenticated writes; require browser Origin.
    if request.headers.get("Origin") != "https://" + request.host:
        raise ProfileValidation("Asal permintaan tidak sah")
    if not request.is_json or request.content_length is None or request.content_length > 17000:
        raise ProfileValidation("Format atau saiz maklumat tidak sah")
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ProfileValidation("Maklumat JSON tidak sah")
    return body


def _failure(exc):
    if isinstance(exc, ProfileValidation):
        return jsonify({"error": str(exc)}), 400
    if isinstance(exc, ProfileConflict):
        return jsonify({"error": "Maklumat telah berubah pada peranti lain. Muat semula sebelum simpan."}), 409
    return jsonify({"error": "Maklumat guru belum dapat disimpan. Data sedia ada tidak diubah."}), 503


@bp.get("/api/web/teacher/profile")
def teacher_profile_get():
    conf, uid, err = _auth()
    if err is not None:
        return err
    if request.args:
        return jsonify({"error": "Parameter tidak dijangka"}), 400
    try:
        profile = get_profile(conf["supabase_url"], conf["supabase_key"], uid)
        schedule = get_schedule(conf["supabase_url"], conf["supabase_key"], uid)
    except (ProfileValidation, ProfileUnavailable, ProfileConflict) as exc:
        return _failure(exc)
    return make_response(jsonify({"profile": profile, "timetable": schedule}))


@bp.put("/api/web/teacher/profile")
def teacher_profile_put():
    conf, uid, err = _auth()
    if err is not None:
        return err
    if request.args:
        return jsonify({"error": "Parameter tidak dijangka"}), 400
    try:
        version = save_profile(conf["supabase_url"], conf["supabase_key"],
                               uid, _body())
    except (ProfileValidation, ProfileUnavailable, ProfileConflict) as exc:
        return _failure(exc)
    return jsonify({"saved": True, "version": version})


@bp.put("/api/web/teacher/timetable")
def teacher_timetable_put():
    conf, uid, err = _auth()
    if err is not None:
        return err
    if request.args:
        return jsonify({"error": "Parameter tidak dijangka"}), 400
    try:
        version = save_schedule(conf["supabase_url"], conf["supabase_key"],
                                uid, _body())
    except (ProfileValidation, ProfileUnavailable, ProfileConflict) as exc:
        return _failure(exc)
    return jsonify({"saved": True, "version": version})
