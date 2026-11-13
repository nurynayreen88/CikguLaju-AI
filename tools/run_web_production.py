"""CikguLaju dedicated Web WSGI entrypoint (independent of Telegram runtime).

Start: gunicorn --bind 0.0.0.0:$PORT tools.run_web_production:app
Server secrets remain in Render environment variables, never source control.
"""
import os
from flask import jsonify
from tools.run_web_v1_preview import app
from web_v1_telegram_auth_routes import _config
from web.teacher_profile_routes import bp as teacher_profile_bp
app.register_blueprint(teacher_profile_bp)
from web.rph_hari_ini_web import bp as rph_hari_ini_bp
app.register_blueprint(rph_hari_ini_bp)
from web.pbd_routes import bp as pbd_bp
app.register_blueprint(pbd_bp)
from web.web_payment_routes import bp as web_payment_bp
app.register_blueprint(web_payment_bp)

# Opt-in, read-only production paid-status API. Requires a separate, long
# dedicated private bearer token and explicit production feature flag.
# Never change payment approval, subscription or generation logic here.
from web.telegram_prod_paid_status_bridge import bp as read_only_paid_status_bp
app.register_blueprint(read_only_paid_status_bp)
from web.web_referral_routes import install as install_web_referral
install_web_referral(app)

from web.special_activities_web import bp as special_activities_bp
app.register_blueprint(special_activities_bp)
from web.admin_usage_web import bp as admin_usage_bp
app.register_blueprint(admin_usage_bp)
from web.web_feedback_routes import bp as web_feedback_bp
app.register_blueprint(web_feedback_bp)




def _web_config_status():
    auth_configured = _config() is not None
    url = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    source_configured = url.startswith("https://") and len(token) >= 32
    return auth_configured, source_configured


@app.get("/assets/cikgulaju-logo.svg")
def web_brand_logo():
    """Logo supplied by CikguLaju owner with transparent image background."""
    from pathlib import Path
    from flask import send_file
    path = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "cikgulaju-logo.svg"
    return send_file(path, mimetype="image/svg+xml", conditional=True, max_age=86400)


@app.get("/assets/pbd.js")
@app.get("/assets/pbd.css")
@app.get("/assets/Templat_Rekod_PBD_CikguLaju.xlsx")
def pbd_asset():
    from pathlib import Path
    from flask import request, send_file
    name = request.path.rsplit("/", 1)[-1]
    file = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / name
    return send_file(file, conditional=True, max_age=1800,
                     as_attachment=name.endswith(".xlsx"))


@app.get("/assets/rph-today.js")
def daily_rph_script():
    """Read-only timetable UI; RPH generation remains the existing native flow."""
    from pathlib import Path
    from flask import send_file
    file = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "rph-today.js"
    return send_file(file, mimetype="application/javascript", max_age=1800, conditional=True)


@app.get("/assets/special-activities.js")
def special_activities_script():
    """Static activity selector; downloads remain private and quota-gated."""
    from pathlib import Path
    from flask import send_file
    path = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "special-activities.js"
    return send_file(path, mimetype="application/javascript", max_age=1800, conditional=True)


@app.get("/assets/pdf-lib.min.js")
def self_hosted_pdf_lib():
    """Pinned PDF-lib is copied from a reviewed package into this release.
    All teacher profile details stay within the browser and same-origin APIs.
    """
    from pathlib import Path
    from flask import send_file
    path=Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"pdf-lib.min.js"
    return send_file(path,mimetype="application/javascript",max_age=86400,conditional=True)


@app.get("/assets/pdp-pdf-copy.js")
def pdp_pdf_copy_script():
    from pathlib import Path
    from flask import send_file
    path = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "pdp-pdf-copy.js"
    return send_file(path, mimetype="application/javascript", max_age=1800, conditional=True)


@app.get("/assets/rpt-original-cover-layout.json")
def original_rpt_cover_layout():
    """Fixed public PDF cover coordinates and hashes only; no teacher data."""
    from pathlib import Path
    from flask import send_file
    path=(Path(__file__).resolve().parents[1]/"rpt_2027"/
          "web_2027_pdfs"/"original_cover_layout_verified.json")
    response=send_file(path,mimetype="application/json",max_age=0,conditional=False)
    response.headers["Cache-Control"]="no-store"
    response.headers["X-Content-Type-Options"]="nosniff"
    return response


@app.get("/assets/rpt-personalize.js")
def personalized_rpt_script():
    """Browser-side private PDF cover without modifying curriculum bytes."""
    from pathlib import Path
    from flask import send_file
    path=Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"rpt-personalize.js"
    return send_file(path,mimetype="application/javascript",max_age=1800,conditional=True)


@app.get("/assets/teacher-profile.js")
def teacher_profile_script():
    """Static browser editor. Personal data remains behind authenticated routes."""
    from pathlib import Path
    from flask import send_file
    file = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "teacher-profile.js"
    return send_file(file, mimetype="application/javascript", max_age=1800, conditional=True)


@app.get("/assets/web-payment.js")
def web_payment_script():
    """Same-origin payment UI; no credentials or payment state in static JS."""
    from pathlib import Path
    from flask import send_file
    file = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "web-payment.js"
    return send_file(file, mimetype="application/javascript", max_age=1800,
                     conditional=True)


@app.get("/assets/web-feedback.js")
def web_feedback_script():
    """Serve only static UI; private comments require cookie-auth endpoints."""
    from pathlib import Path
    from flask import send_file
    source = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "web-feedback.js"
    response = send_file(source, mimetype="application/javascript")
    response.headers["Cache-Control"] = "public, max-age=300"
    return response


@app.get("/assets/admin-usage.js")
def admin_usage_script():
    """Static UI only. All admin data require verified server-side access."""
    from pathlib import Path
    from flask import send_file
    path = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "admin-usage.js"
    return send_file(path, mimetype="application/javascript", max_age=1800, conditional=True)


@app.get("/assets/web-referral.js")
def web_referral_script():
    """Private referral sharing UI, authenticated API only."""
    from pathlib import Path
    from flask import send_file
    path = Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "web-referral.js"
    return send_file(path, mimetype="application/javascript", max_age=1800, conditional=True)


@app.get("/healthz")
def web_liveness():
    """Liveness only: never confuse a booted worker with an approved product."""
    return jsonify({"service": "cikgulaju-web", "live": True})


@app.get("/readyz")
def web_readiness():
    """Readiness requires configured account backend and actual Telegram catalog."""
    auth, source = _web_config_status()
    live_source = False
    if auth and source:
        try:
            from web.authoritative_http_source import AuthoritativeHttpCurriculumSource
            rows = AuthoritativeHttpCurriculumSource(
                os.environ["CIKGULAJU_AUTHORITATIVE_API_URL"],
                os.environ["CIKGULAJU_AUTHORITATIVE_API_TOKEN"]).list_subjects(2)
            live_source = bool(rows)
        except Exception:
            live_source = False
    ready = auth and source and live_source
    return jsonify({
        "service": "cikgulaju-web",
        "account_lookup_configured": auth,
        "authoritative_curriculum_configured": source,
        "authoritative_curriculum_reachable": live_source,
        "ready": ready,
        "all_subject_rph_final_verified": False,
        "note": "Akses RPH hanya bagi rekod yang mempunyai sumber dokumen disahkan.",
    }), 200 if ready else 503


@app.after_request
def web_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


def _production_deployment_status():
    """Separate a deployed production Web from fully launched content coverage."""
    auth, catalog = _web_config_status()
    return jsonify({
        "environment": "production-web",
        "hosting": "render",
        "telegram_production_separate": True,
        "account_lookup_configured": auth,
        "authoritative_catalog_configured": catalog,
        "rph_source_preview_enabled": auth and catalog,
        "all_subject_rph_final_verified": False,
        "public_launch_ready": False,
    })


def _production_health():
    """Liveness is not proof of payments, RPH quality, or login readiness."""
    auth, catalog = _web_config_status()
    return jsonify({
        "status": "web-service-running",
        "account_lookup_configured": auth,
        "authoritative_catalog_configured": catalog,
        "all_subject_rph_final_verified": False,
    })


# Reuse the independently tested Web routes while fixing legacy preview
# metadata in this production-only launcher. Do not mutate Telegram handlers.
app.view_functions["deployment_status"] = _production_deployment_status
app.view_functions["health"] = _production_health


@app.get("/api/auth/telegram/bot-identity")
def telegram_login_bot_identity():
    """Check bot token <-> public widget username without disclosing credentials.

    The legacy Telegram widget is bound to the username of the token's bot.
    A BotFather domain set on any other bot will not authorize this Web.
    """
    from urllib.request import Request, urlopen
    import json

    configured = os.environ.get("CIKGULAJU_WEB_BOT_USERNAME", "").strip().lstrip("@")
    token = os.environ.get("CIKGULAJU_WEB_BOT_TOKEN", "").strip()
    expected_domain = "cikgulaju-web.onrender.com"
    safe_configured = configured if configured and configured.replace("_", "").isalnum() else ""
    result = {
        "expected_domain": expected_domain,
        "configured_widget_bot": safe_configured,
        "telegram_bot_identity_checked": False,
        "username_matches_token": False,
        "telegram_token_bot_username": "",
        "note": "Configure this exact bot in BotFather > Login Widget / allowed URLs.",
    }
    if not safe_configured or not token or ":" not in token:
        return jsonify(result), 503

    try:
        request = Request(
            "https://api.telegram.org/bot" + token + "/getMe",
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urlopen(request, timeout=6) as response:
            raw = response.read(4097)
        if len(raw) > 4096:
            return jsonify(result), 503
        answer = json.loads(raw)
        identity = answer.get("result") if answer.get("ok") is True else None
        name = identity.get("username", "") if isinstance(identity, dict) else ""
        if not isinstance(name, str) or not name or not name.replace("_", "").isalnum():
            return jsonify(result), 503
        result["telegram_token_bot_username"] = name
        result["telegram_bot_identity_checked"] = True
        result["username_matches_token"] = name.casefold() == safe_configured.casefold()
        result["note"] = (
            "Bot identity matches. Check this exact bot's BotFather allowed domain."
            if result["username_matches_token"] else
            "Widget username and token belong to different Telegram bots."
        )
    except Exception:
        # No exception logging: urllib errors can contain the bot token in URL.
        return jsonify(result), 503

    response = jsonify(result)
    response.headers["Cache-Control"] = "no-store"
    return response, 200 if result["username_matches_token"] else 409


# Explicitly opt-in one-shot Science Web→Telegram real network diagnostic.
# No browser route or user account; disabled by default. Does not change
# quota, entitlement, subscription, or expose RPH source/secret to the UI.
# DRAF/HOLD authoring bank remains isolated from the verified DB runtime.
try:
    from tools.web_sains_native_telegram_e2e_smoke_20261108 import (
        log_when_enabled as _sains_web_download_network_test,
    )
    WEB_SAINS_NATIVE_SMOKE_RESULT = _sains_web_download_network_test()
except Exception as _sains_web_network_smoke_exc:
    WEB_SAINS_NATIVE_SMOKE_RESULT = None
    print("CIKGULAJU_SAINS_WEB_REAL_DOWNLOAD_SMOKE_UNAVAILABLE",
          type(_sains_web_network_smoke_exc).__name__,flush=True)
