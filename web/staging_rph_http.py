"""Staging-only HTTP adapter. Not registered in the public Flask app.

Call create_staging_rph_blueprint with a trusted session authorization callback
and an audited server-side RPHLookupConfig. Never accept approval configuration
from the browser. This route is disabled unless explicitly enabled on staging.
"""
import os
from flask import Blueprint, abort, make_response, request

from web.approved_rph_reader import load_approved_rph
from web.rph_document_renderer import render_approved_rph


def create_staging_rph_blueprint(config, authorize):
    if os.environ.get("CIKGULAJU_WEB_RPH_STAGING_ENABLED") != "1":
        raise RuntimeError("Staging RPH endpoint disabled")
    if os.environ.get("CIKGULAJU_ENV") != "staging":
        raise RuntimeError("RPH endpoint cannot be enabled outside staging")
    if config is None:
        raise TypeError("Audited RPH lookup configuration required")
    if not callable(authorize):
        raise TypeError("Trusted authorization callback required")

    blueprint = Blueprint("web_rph_staging", __name__)

    @blueprint.post("/api/staging/rph/generate")
    def generate():
        # Authorization must check server-side user identity and entitlement.
        # A caller-provided user ID or Telegram ID is not authorization.
        if not authorize(request):
            abort(403)
        if not request.is_json:
            abort(415)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            abort(400)
        if set(payload) != {"lesson_id", "format"}:
            abort(400)
        lesson_id = payload["lesson_id"]
        fmt = payload["format"]
        if type(lesson_id) is not int or lesson_id <= 0:
            abort(400)
        if fmt not in ("docx", "pdf"):
            abort(400)
        try:
            approved = load_approved_rph(config, lesson_id)
        except (LookupError, ValueError):
            abort(404)
        document, mime = render_approved_rph(approved, fmt)
        response = make_response(document)
        response.headers["Content-Type"] = mime
        response.headers["Content-Disposition"] = (
            f'attachment; filename="cikgulaju-rph-{lesson_id}.{fmt}"'
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    return blueprint
