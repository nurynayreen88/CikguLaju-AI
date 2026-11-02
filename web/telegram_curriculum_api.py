"""Read-only curriculum API mounted in the Telegram runtime, never the Web snapshot.

Register with app.register_blueprint(create_curriculum_blueprint(lambda: DB_PATH))
only after reviewing the production integration. The callback must resolve the
active master database on each request.
"""
import hmac
import os
from flask import Blueprint, jsonify, request
from web_v1_dropdown_catalog import available_subject_options, unit_options, pdp_options


def create_curriculum_blueprint(database_path_provider):
    bp = Blueprint("telegram_curriculum_v1", __name__)

    @bp.before_request
    def authorize():
        if os.environ.get("CIKGULAJU_CURRICULUM_API_ENABLED") != "1":
            return jsonify({"error": "curriculum API disabled"}), 503
        configured = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
        header = request.headers.get("Authorization", "")
        if len(configured) < 32 or not hmac.compare_digest(header, "Bearer " + configured):
            return jsonify({"error": "unauthorized"}), 401

    def read_options(kind):
        try:
            year = int(request.args.get("year", ""))
            if year not in range(1, 7):
                raise ValueError("year")
            db = database_path_provider()
            if not db:
                raise FileNotFoundError("master database missing")
            from pathlib import Path
            if not Path(db).is_file():
                raise FileNotFoundError("master database missing")
            if kind == "subjects":
                items = available_subject_options(db, year)
            else:
                subject = request.args.get("subject", "")
                if kind == "units":
                    items = unit_options(db, year, subject)
                else:
                    items = pdp_options(db, year, subject, request.args.get("unit", ""))
            return jsonify({"source": "telegram-runtime-v1", "items": items})
        except ValueError:
            return jsonify({"error": "invalid selection"}), 400
        except Exception:
            return jsonify({"error": "authoritative source unavailable"}), 503

    @bp.get("/internal/curriculum/v1/subjects")
    def subjects():
        return read_options("subjects")

    @bp.get("/internal/curriculum/v1/units")
    def units():
        return read_options("units")

    @bp.get("/internal/curriculum/v1/lessons")
    def lessons():
        return read_options("lessons")

    @bp.get("/internal/curriculum/v1/approved-materials")
    def approved_materials():
        # No material is exposed without a verified approval mapping and
        # authorized delivery. Never manufacture downloadable file URLs.
        return jsonify({"error": "approved material mapping unavailable"}), 503

    return bp
