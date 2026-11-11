"""Opt-in internal KP2027 source-status API; never routes into legacy lesson engine.

Only Telegram-hosted backend should register it after explicit staging review.
It exposes source-discovery metadata to authenticated Web service, not public
RPH, guessed SK/SP, or unpublished curriculum files.
"""
from __future__ import annotations
import hmac
import os

from flask import Blueprint, jsonify, request

from curriculum.kp2027.inventory import (
    KP2027SourceUnverified, STATUS, LEVELS, levels, status_for, subjects_for,
    verified_standards_for, request_rph, request_rpt,
)

ENV_FLAG = "CIKGULAJU_KP2027_STAGING_ENABLED"
TOKEN_ENV = "CIKGULAJU_AUTHORITATIVE_API_TOKEN"


def create_kp2027_status_blueprint():
    bp = Blueprint("cikgulaju_kp2027_status_draft", __name__)

    @bp.after_request
    def protected_headers(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Vary"] = "Authorization"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.before_request
    def security():
        if os.environ.get(ENV_FLAG) != "1":
            return jsonify({"error": "KP2027 staging unavailable"}), 503
        token = os.environ.get(TOKEN_ENV, "")
        if (len(token) < 32 or not hmac.compare_digest(
                request.headers.get("Authorization", ""), "Bearer " + token)):
            return jsonify({"error": "Unauthorized"}), 401

    def _params(required):
        p = request.args
        if set(p) != required or any(len(p.getlist(k)) != 1 for k in required):
            raise ValueError("Unexpected selection parameters")
        return p

    @bp.get("/internal/kp2027/v1/levels")
    def available_levels():
        try:
            _params(set())
        except ValueError:
            return jsonify({"error": "Invalid query"}), 400
        return jsonify({"items": levels(), "status": STATUS, "rph_available": False})

    @bp.get("/internal/kp2027/v1/subjects")
    def available_subjects():
        try:
            args = _params({"level"})
            subjects, digest = subjects_for(args["level"])
        except KP2027SourceUnverified:
            return jsonify({"error": "KP2027 inventory unavailable"}), 503
        except ValueError:
            return jsonify({"error": "Year/Tingkatan not supported"}), 400
        except OSError:
            return jsonify({"error": "KP2027 inventory unavailable"}), 503
        return jsonify({"items": subjects, "source_digest": digest,
                        "status": STATUS, "rph_available": False,
                        "rpt_available": False})

    @bp.get("/internal/kp2027/v1/status")
    def one_status():
        try:
            args = _params({"level", "subject", "source_digest"})
            info = status_for(args["level"], args["subject"], args["source_digest"])
        except KP2027SourceUnverified:
            return jsonify({"error": "Source not available or changed"}), 409
        except ValueError:
            return jsonify({"error": "Invalid KP2027 subject"}), 400
        except OSError:
            return jsonify({"error": "KP2027 inventory unavailable"}), 503
        return jsonify(info)

    @bp.get("/internal/kp2027/v1/standards")
    def standards_unavailable():
        try:
            args = _params({"level", "subject"})
            verified_standards_for(args["level"], args["subject"])
        except KP2027SourceUnverified:
            return jsonify({"error": "KP2027 original DK not audited; standards unavailable"}), 503
        except ValueError:
            return jsonify({"error": "Invalid selection"}), 400
        except OSError:
            return jsonify({"error": "KP2027 inventory unavailable"}), 503
        return jsonify({"error": "No verified KP2027 standards"}), 503

    @bp.post("/internal/kp2027/v1/render")
    def render_unavailable():
        # Strictly no legacy RPH or Web-only preview document fallback.
        return jsonify({"error": "KP2027 RPH/RPT not yet approved"}), 503

    return bp


def register_if_enabled(flask_app):
    """Separate staging opt-in: NEVER alter the existing curriculum blueprint."""
    if os.environ.get(ENV_FLAG) != "1":
        return False
    if len(os.environ.get(TOKEN_ENV, "")) < 32:
        return False
    flask_app.register_blueprint(create_kp2027_status_blueprint())
    return True
