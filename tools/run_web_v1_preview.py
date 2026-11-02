"""Run the isolated Web V1 preview without importing production app.py.

Local-only command:
    python tools/run_web_v1_preview.py

The preview optionally reads a local SQLite database in read-only mode.
It has no authentication, credit or generation endpoints.
Do not expose this development server to the public internet.
"""
import os
import sqlite3
from pathlib import Path
import sys

from flask import Flask, send_file, jsonify, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web_v1_dropdown_catalog import subject_options, available_subject_options, unit_options, pdp_options, component_options
from web_v1_verified_pdp import list_explicit_pjpk_entries
from web_v1_entitlements import display_trusted_account
PREVIEW = ROOT / "web_v1_static_preview" / "index.html"
app = Flask(__name__)
from web_v1_telegram_auth_routes import auth_blueprint
app.register_blueprint(auth_blueprint)
from web.english_catalog_http import create_english_catalog_blueprint
app.register_blueprint(create_english_catalog_blueprint())


@app.get("/")
def preview():
    response = send_file(PREVIEW, mimetype="text/html", conditional=True)
    response.headers["Cache-Control"] = "no-store, private"
    return response


@app.get("/health")
def health():
    db = os.environ.get("CIKGULAJU_WEB_PREVIEW_DB", "")
    connected = False
    if db and Path(db).is_file():
        try:
            # URI mode=ro guarantees that a health check cannot create or alter the DB.
            from urllib.parse import quote
            uri = "file:" + quote(str(Path(db).resolve()), safe="/:") + "?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=2) as connection:
                connected = connection.execute("PRAGMA quick_check(1)").fetchone()[0] == "ok"
        except (sqlite3.Error, OSError, ValueError):
            connected = False
    return {"status": "preview-only", "database_connected": connected, "generation_enabled": False}


@app.get("/api/options")
def options():
    """Read-only dropdowns for authenticated existing accounts only."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    config = _config()
    if config is None:
        return jsonify({"error": "Login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "Authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "Account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "Existing account required"}), 403
    try:
        year = int(request.args.get("year", ""))
        if year not in range(1, 7):
            return jsonify({"error": "invalid year"}), 400
        kind = request.args.get("kind", "")
        if kind not in ("subjects", "units", "pdp", "components"):
            return jsonify({"error": "invalid option kind"}), 400
        if kind == "components":
            return jsonify(component_options(request.args.get("subject", "")))
        db = os.environ.get("CIKGULAJU_WEB_PREVIEW_DB", "")
        if not db or not Path(db).is_file():
            return jsonify({"error": "preview database not configured"}), 503
        if kind == "subjects":
            return jsonify(available_subject_options(db, year))
        subject = request.args.get("subject", "")
        if subject == "PJPK":
            component = request.args.get("component", "")
            if component not in ("PJ", "PK"):
                return jsonify({"error": "select PJ or PK"}), 400
            records = list_explicit_pjpk_entries(db, year, component)
            if kind == "units":
                names = dict.fromkeys((r.get("unit_title") or "").strip() for r in records)
                return jsonify([{"value": n, "label": n} for n in names if n])
            unit = request.args.get("unit", "")
            if not unit or len(unit) > 300:
                return jsonify({"error": "invalid unit"}), 400
            return jsonify([{"value": str(r["id"]), "label": "PdP " + str(r["pdp_no"]) + " — " + str(r.get("subtopic") or r.get("topic") or ""), "standalone_rph_verified": False} for r in records if (r.get("unit_title") or "").strip() == unit])
        if kind == "units":
            return jsonify(unit_options(db, year, subject))
        if kind == "pdp":
            return jsonify(pdp_options(db, year, subject, request.args.get("unit", "")))
        return jsonify({"error": "invalid option kind"}), 400
    except (ValueError, FileNotFoundError, OSError):
        return jsonify({"error": "invalid selection or unavailable database"}), 400
    except Exception:
        app.logger.exception("Preview dropdown read failed")
        return jsonify({"error": "dropdown temporarily unavailable"}), 503



@app.get("/api/deployment/status")
def deployment_status():
    """Explicit staging-only capabilities for web readiness checks."""
    return jsonify({
        "environment": "staging-preview",
        "hosting": "render",
        "telegram_production_separate": True,
        "account_linked": False,
        "rph_generation_enabled": False,
        "public_launch_ready": False,
    })


@app.get("/api/auth/capabilities")
def auth_capabilities():
    """Public, non-sensitive readiness flags; never infer auth from QR primitives."""
    from web_v1_telegram_auth_routes import _config
    ready = _config() is not None
    bot_username = os.environ.get("CIKGULAJU_WEB_BOT_USERNAME", "").lstrip("@")
    widget_ready = ready and bool(bot_username)
    return jsonify({
        "telegram_login_enabled": widget_ready,
        "telegram_widget_enabled": widget_ready,
        "bot_username": bot_username if widget_ready else "",
        "phone_qr_pairing_enabled": False,
        "existing_account_lookup_enabled": ready,
        "session_cookie_enabled": ready,
        "status": "configured" if widget_ready else "not-configured",
    })


@app.get("/api/shared/status")
def shared_status():
    return jsonify({"shared_backend_connected": False, "telegram_account_linked": False, "generation_enabled": False, "download_enabled": False})

@app.get("/api/account/status")
def account_status():
    """Expose trusted existing-account status, never browser-supplied credits."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    config = _config()
    if config is None:
        return jsonify({"authenticated": False, "error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"authenticated": False}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"authenticated": False, "error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, **display_trusted_account(account), "shared_backend_connected": True})


@app.get("/api/materials")
def materials():
    return jsonify({"error": "authentication and shared backend required"}), 503

@app.post("/api/generate")
def generate():
    """Authorized, approval-gated document generation; no quota mutation."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    from web.approved_rph_reader import RPHLookupConfig, load_approved_rph
    from web.rph_document_renderer import render_approved_rph
    from flask import make_response
    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "existing account required"}), 403
    if os.environ.get("CIKGULAJU_ENV") != "staging" or os.environ.get("CIKGULAJU_WEB_RPH_STAGING_ENABLED") != "1":
        return jsonify({"error": "approved RPH generation not enabled"}), 503
    # A successful HTTP download currently has no shared, atomic Telegram
    # credit debit. Do not permit unlimited free downloads just because
    # the staging renderer flag was enabled. This is intentionally fail-closed.
    return jsonify({"error": "Shared Telegram generation and quota accounting not connected"}), 503
    if not request.is_json or (request.content_length or 0) > 2048:
        return jsonify({"error": "invalid request"}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"lesson_id", "format"}:
        return jsonify({"error": "invalid selection"}), 400
    lesson_id, fmt = payload["lesson_id"], payload["format"]
    if type(lesson_id) is not int or lesson_id <= 0 or fmt not in ("docx", "pdf"):
        return jsonify({"error": "invalid selection"}), 400
    names = ("CIKGULAJU_WEB_APPROVED_DB", "CIKGULAJU_WEB_APPROVED_TABLE",
             "CIKGULAJU_WEB_APPROVED_ID_COLUMN", "CIKGULAJU_WEB_APPROVED_TITLE_COLUMN",
             "CIKGULAJU_WEB_APPROVED_CONTENT_COLUMN", "CIKGULAJU_WEB_APPROVED_STATUS_COLUMN",
             "CIKGULAJU_WEB_APPROVED_STATUS_VALUE", "CIKGULAJU_WEB_APPROVED_REFERENCE_COLUMN")
    values = [os.environ.get(name, "") for name in names]
    if any(not value for value in values):
        return jsonify({"error": "approved content source not configured"}), 503
    try:
        rph = load_approved_rph(RPHLookupConfig(*values), lesson_id)
    except (LookupError, ValueError, sqlite3.Error, OSError):
        return jsonify({"error": "approved RPH not available"}), 404
    try:
        data, mime = render_approved_rph(rph, fmt)
    except (ImportError, ValueError):
        return jsonify({"error": "document renderer unavailable"}), 503
    response = make_response(data)
    response.headers["Content-Type"] = mime
    response.headers["Content-Disposition"] = f'attachment; filename="cikgulaju-rph-{lesson_id}.{fmt}"'
    response.headers["Cache-Control"] = "no-store, private"
    return response

@app.get("/api/web/english/rph/capabilities")
def english_rph_capabilities():
    enabled = (os.environ.get("CIKGULAJU_ENV") == "staging"
               and os.environ.get("CIKGULAJU_WEB_RPH_STAGING_ENABLED") == "1")
    missing = []
    for package in ("docx", "reportlab"):
        try:
            __import__(package)
        except ImportError:
            missing.append("python-docx" if package == "docx" else package)
    return jsonify({
        "download_enabled": False,
        "renderer_ready": not missing,
        "missing_packages": missing,
        "staging_generation_enabled": enabled,
        "telegram_generation_parity_verified": False,
        "shared_quota_debit_verified": False,
        "note": "Staging renderer only; Telegram generation and quota parity not verified.",
    })


@app.post("/api/web/english/rph")
def english_approved_rph():
    """Render only explicitly release-ready English lessons by year and lesson."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    from web.english_release_gate import load_release_ready_english
    from web.rph_document_renderer import ApprovedRPH, render_approved_rph
    from flask import make_response
    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "existing account required"}), 403
    if os.environ.get("CIKGULAJU_ENV") != "staging" or os.environ.get("CIKGULAJU_WEB_RPH_STAGING_ENABLED") != "1":
        return jsonify({"error": "RPH downloads not enabled"}), 503
    if not request.is_json or (request.content_length or 0) > 2048:
        return jsonify({"error": "invalid request"}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"year", "lesson_no", "format"}:
        return jsonify({"error": "invalid request"}), 400
    year, lesson_no, fmt = payload["year"], payload["lesson_no"], payload["format"]
    if type(year) is not int or year not in (1, 2, 3) or type(lesson_no) is not int or not 1 <= lesson_no <= 160 or fmt not in ("docx", "pdf"):
        return jsonify({"error": "invalid selection"}), 400
    try:
        content = load_release_ready_english(year, lesson_no)
    except (LookupError, ValueError, OSError):
        return jsonify({"error": "lesson not approved for release"}), 404
    try:
        data, mime = render_approved_rph(
            ApprovedRPH(lesson_no, f"English Year {year} — Lesson {lesson_no}", content, f"release-ready:english:{year}:{lesson_no}"), fmt)
    except (ImportError, ValueError):
        return jsonify({"error": "document renderer unavailable"}), 503
    response = make_response(data)
    response.headers["Content-Type"] = mime
    response.headers["Content-Disposition"] = f'attachment; filename="english-year{year}-lesson{lesson_no:03d}.{fmt}"'
    response.headers["Cache-Control"] = "no-store, private"
    return response


@app.get("/api/materials/download/<material_id>")
def download_material(material_id):
    return jsonify({"error": "authorized download service not connected"}), 503

@app.after_request
def preview_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store, private"
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
