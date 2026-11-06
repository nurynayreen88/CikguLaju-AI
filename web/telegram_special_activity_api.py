"""Private Telegram-owned source API for Special Activity RPHs.

This blueprint is opt-in and must only be registered on the authenticated
Telegram backend. The public Web must proxy requests after its own existing
login, paid/free quota checks and receipt/payment verification. Never mount
this blueprint as a public Web endpoint.
"""
import hmac
import os
from flask import Blueprint, Response, jsonify, request

from rph_standalone.aktiviti_khas.engine import (
    MIMES, SELEPAS, STATUS, TRANSISI, SourceUnavailable, list_options, render,
    select,
)

MAX_BODY = 3000
MAX_RESULT = 15 * 1024 * 1024


def _authorized():
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    return (
        os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED") == "1"
        and os.environ.get("CIKGULAJU_SPECIAL_RPH_ENABLED") == "1"
        and len(token) >= 32
        and hmac.compare_digest(request.headers.get("Authorization", ""),
                                "Bearer " + token)
    )


def create_special_rph_blueprint():
    bp = Blueprint("telegram_special_activity_rph", __name__)

    @bp.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Authorization"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.before_request
    def security():
        if not _authorized():
            return jsonify({"error": "Unauthorized activity source"}), 401

    @bp.get("/internal/rph/v1/aktiviti-khas/options")
    def options():
        if not (set(request.args) in ({"kind", "year"}, {"kind", "year", "phase"})
                and all(len(request.args.getlist(k)) == 1 for k in request.args)):
            return jsonify({"error": "Invalid selection"}), 400
        kind, year_str = request.args.get("kind"), request.args.get("year")
        if not isinstance(year_str, str) or not year_str in "123456" or len(year_str) != 1:
            return jsonify({"error": "Invalid year"}), 400
        try:
            rows, digest = list_options(kind, int(year_str),
                                        phase=request.args.get("phase"))
        except SourceUnavailable:
            return jsonify({"error": "Activity source unavailable"}), 503
        except (ValueError, KeyError, TypeError):
            return jsonify({"error": "Invalid selection"}), 400
        except OSError:
            return jsonify({"error": "Activity source unavailable"}), 503
        return jsonify({"items": rows, "source_digest": digest, "status": STATUS,
                        "formats": list(MIMES)})

    @bp.post("/internal/rph/v1/aktiviti-khas/render")
    def document():
        if (not request.is_json or request.content_length is None
                or request.content_length > MAX_BODY):
            return jsonify({"error": "Invalid document request"}), 400
        payload = request.get_json(silent=True)
        if (not isinstance(payload, dict)
                or set(payload) != {"selection", "teacher", "format", "source_digest"}
                or not isinstance(payload["selection"], dict)
                or set(payload["selection"]) != {"kind", "year", "activity_id", "subject"}
                or not isinstance(payload["format"], str)
                or payload["format"] not in MIMES):
            return jsonify({"error": "Invalid document selection"}), 400
        s = payload["selection"]
        try:
            row = select(s["kind"], s["year"], s["activity_id"], payload["source_digest"])
            subject = s["subject"]
            content = render(row, s["year"], payload["teacher"], payload["format"],
                             subject=subject)
            if not isinstance(content, bytes) or not 900 < len(content) <= MAX_RESULT:
                raise SourceUnavailable("Document size or format invalid")
            if payload["format"] == "pdf" and not content.startswith(b"%PDF-"):
                raise SourceUnavailable("Invalid PDF document")
            if payload["format"] == "word" and not content.startswith(b"PK"):
                raise SourceUnavailable("Invalid Word document")
        except (ValueError, TypeError, KeyError, OSError):
            return jsonify({"error": "Activity selection, source or document unavailable"}), 400
        filename = "CikguLaju_Aktiviti_Khas_%s_Tahun_%s_DRAF.%s" % (
            row["id"], s["year"], "docx" if payload["format"] == "word" else "pdf")
        response = Response(content, mimetype=MIMES[payload["format"]])
        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        response.headers["X-CikguLaju-Source-Status"] = STATUS
        return response

    return bp


def register_if_enabled(flask_app):
    """Opt-in registration; never touches Telegram state, webhook or DB."""
    if os.environ.get("CIKGULAJU_SPECIAL_RPH_ENABLED") != "1":
        return False
    if os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED") != "1":
        return False
    if len(os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")) < 32:
        return False
    flask_app.register_blueprint(create_special_rph_blueprint())
    return True
