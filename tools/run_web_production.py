"""CikguLaju dedicated Web WSGI entrypoint (independent of Telegram runtime).

Start: gunicorn --bind 0.0.0.0:$PORT tools.run_web_production:app
Server secrets remain in Render environment variables, never source control.
"""
import os
from flask import jsonify
from tools.run_web_v1_preview import app
from web_v1_telegram_auth_routes import _config


def _web_config_status():
    auth_configured = _config() is not None
    url = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    source_configured = url.startswith("https://") and len(token) >= 32
    return auth_configured, source_configured


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
