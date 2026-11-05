"""Authenticated, read-only RPT English 2027 PDF delivery for Web staging.

Loads the exact same Git PDF blobs as Telegram; no generation, DB writes,
credit decrements, or external redirects. This module does not affect RPH.
"""
from datetime import date, datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

ROOT = Path(__file__).resolve().parents[1] / "rpt_2027" / "english"
YEARS = frozenset(range(2, 7))


def pdf_path(root, year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("unsupported English RPT year")
    return Path(root) / ("RPT_ENGLISH_TAHUN_%d_2027_UNTUK_GURU.pdf" % year)


def _has_paid_access(account):
    """Only confirmed lifetime or unexpired paid access; free RPH credits do not qualify."""
    if not isinstance(account, dict):
        return False
    if account.get("rakan_pembangun") is True:
        return True
    stamp = account.get("vip_expires_at")
    if isinstance(stamp, str) and stamp:
        try:
            expires = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            return expires.tzinfo is not None and expires > datetime.now(timezone.utc)
        except (ValueError, TypeError):
            return False
    expires_date = account.get("vip_until")
    if isinstance(expires_date, str) and expires_date:
        try:
            return date.fromisoformat(expires_date) >= date.today()
        except ValueError:
            return False
    return False


def _account():
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    config = _config()
    if config is None:
        return None, (jsonify({"error": "Login not configured"}), 503)
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return None, (jsonify({"error": "Authentication required"}), 401)
    try:
        account = _lookup(config, uid)
    except Exception:
        return None, (jsonify({"error": "Account lookup unavailable"}), 503)
    if not account or account.get("telegram_user_id") != uid or account.get("authenticated") is not True:
        return None, (jsonify({"error": "Existing account required"}), 403)
    return account, None


def create_english_rpt_blueprint(root=ROOT):
    bp = Blueprint("english_rpt_2027_pdf", __name__)

    @bp.after_request
    def private_cache(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.get("/api/rpt/2027/english")
    def inventory():
        account, error = _account()
        if error is not None:
            return error
        return jsonify({"years": [2, 3, 4, 5, 6], "format": "pdf",
                        "allowed": _has_paid_access(account),
                        "note": "RPT ialah akses berbayar; 10 janaan RPH percuma tidak digunakan."})

    @bp.get("/api/rpt/2027/english/<int:year>.pdf")
    def download(year):
        account, error = _account()
        if error is not None:
            return error
        if not _has_paid_access(account):
            return jsonify({"error": "RPT 2027 requires an active paid account or confirmed Rakan Pembangun"}), 403
        if year not in YEARS:
            return jsonify({"error": "RPT English year unavailable"}), 404
        path = pdf_path(root, year)
        if not path.is_file():
            return jsonify({"error": "Verified RPT PDF not present on Web service"}), 503
        from web.rpt_school_cover import for_download
        from web.teacher_profile_store import ProfileUnavailable
        try:
            document = for_download(account, path, "English", year)
        except ProfileUnavailable:
            return jsonify({"error": "RPT dengan identiti sekolah belum dapat disediakan. Sila cuba semula."}), 503
        return send_file(document, mimetype="application/pdf", as_attachment=True,
                         download_name=path.name, conditional=False)

    return bp
