"""Private Web bridge for the verified PPKI source in the Telegram runtime."""
from flask import Blueprint, Response, jsonify, request

from staging.ppki.catalog import (
    FORMATS, RPT_COMBINED_FILENAME, RPT_FILENAME, RPT_MANIPULATIVE_FILENAME,
    SUBJECT, YEAR, catalog, lesson_filename, options, selected_lesson,
)
from staging.ppki.render_pengurusan_kehidupan import render_lesson
from staging.ppki.rpt import render_rpt
from web.native_rph_telegram_api import MIMES
from web.telegram_verified_rpt_rph_bridge import _authorization, _teacher_metadata


def create_ppki_blueprint():
    bp = Blueprint("telegram_ppki", __name__, url_prefix="/internal/rph/v1/ppki")

    @bp.before_request
    def auth():
        if not _authorization():
            return jsonify({"error": "Unauthorized"}), 401

    @bp.after_request
    def private(response):
        response.headers.update({
            "Cache-Control": "no-store, private",
            "Vary": "Authorization",
            "X-Content-Type-Options": "nosniff",
        })
        return response

    @bp.get("/catalog")
    def ppki_catalog():
        if request.args:
            return jsonify({"error": "Unexpected query parameters"}), 400
        return jsonify(options())

    @bp.post("/render")
    def ppki_render():
        if not request.is_json or not 0 < (request.content_length or 0) <= 7000:
            return jsonify({"error": "Invalid PPKI request"}), 400
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {"selection", "teacher", "format"}:
            return jsonify({"error": "Invalid PPKI request"}), 400
        selection = data["selection"]
        fmt = data["format"]
        teacher = data["teacher"]
        if (not isinstance(selection, dict) or set(selection) != {"year", "subject", "unit", "lesson"}
                or type(selection["year"]) is not int or selection["year"] != YEAR
                or selection["subject"] != SUBJECT or fmt not in FORMATS):
            return jsonify({"error": "Invalid PPKI selection"}), 400
        unit = selection["unit"]
        if not isinstance(unit, str):
            return jsonify({"error": "Invalid PPKI unit"}), 400
        lesson = selected_lesson(unit, selection["lesson"])
        if lesson is None:
            return jsonify({"error": "PPKI PdP unavailable"}), 404
        try:
            _teacher_metadata(teacher, SUBJECT)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid teacher metadata"}), 400
        extension = "docx" if fmt == "word" else "pdf"
        body = render_lesson(catalog(unit), lesson, extension, teacher)
        response = Response(body, mimetype=MIMES[fmt])
        response.headers["Content-Disposition"] = f'attachment; filename="{lesson_filename(lesson["pdp"], fmt)}"'
        return response

    @bp.get("/rpt.pdf", defaults={"combined": False})
    @bp.get("/rpt-current.pdf", defaults={"combined": True})
    @bp.get("/rpt-manipulatif.pdf", defaults={"combined": False, "manipulative": True})
    def ppki_rpt(combined, manipulative=False):
        if request.args:
            return jsonify({"error": "Unexpected query parameters"}), 400
        response = Response(render_rpt(combined=combined, manipulative=manipulative), mimetype=MIMES["pdf"])
        filename = RPT_COMBINED_FILENAME if combined else RPT_FILENAME
        if manipulative:
            filename = RPT_MANIPULATIVE_FILENAME
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    return bp
