"""Cookie-authenticated private profile and timetable endpoints for CikguLaju Web.

No user identifier accepted from browser. The Telegram session is the only
identity source, looked up against the existing account in Supabase.
"""
from io import BytesIO
from flask import Blueprint, jsonify, make_response, request, send_file
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


@bp.get("/api/web/teacher/school-logo")
def teacher_school_logo_get():
    conf, uid, err = _auth()
    if err is not None:
        return err
    if request.args:
        return jsonify({"error": "Parameter tidak dijangka"}), 400
    from web.school_logo_store import logo_png
    try:
        logo = logo_png(conf["supabase_url"], conf["supabase_key"], uid)
    except ProfileUnavailable:
        return jsonify({"error": "Logo sekolah belum dapat dibaca"}), 503
    if logo is None:
        return jsonify({"error": "Logo sekolah belum dimuat naik"}), 404
    return send_file(BytesIO(logo), mimetype="image/png", max_age=0,
                     conditional=False)


@bp.post("/api/web/teacher/school-logo")
def teacher_school_logo_put():
    conf, uid, err = _auth()
    if err is not None:
        return err
    if request.headers.get("Origin") != "https://" + request.host:
        return jsonify({"error": "Asal permintaan tidak sah"}), 400
    if (request.args or request.content_length is None
            or request.content_length > 2 * 1024 * 1024 + 8192
            or request.mimetype != "multipart/form-data"):
        return jsonify({"error": "Logo tidak sah atau melebihi 2 MB"}), 400
    upload = request.files.get("logo")
    if upload is None or len(request.files) != 1:
        return jsonify({"error": "Sila pilih satu logo sekolah"}), 400
    from web.school_logo_store import MAX_INPUT, save_logo_png
    data = upload.stream.read(MAX_INPUT + 1)
    try:
        count = save_logo_png(conf["supabase_url"], conf["supabase_key"],
                              uid, data)
    except (ProfileValidation, ProfileUnavailable) as exc:
        return _failure(exc)
    return jsonify({"saved": True, "bytes": count})
