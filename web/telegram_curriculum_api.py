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

    @bp.after_request
    def prevent_curriculum_caching(response):
        # These authenticated responses must never be stored by shared proxies.
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Vary"] = "Authorization"
        return response

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
            subject = request.args.get("subject", "")
            allowed = {"year"} if kind == "subjects" else ({"year", "subject"} if kind == "units" else {"year", "subject", "unit"})
            if kind != "subjects" and subject == "PJPK":
                allowed = allowed | {"component"}
            if set(request.args) != allowed or any(len(request.args.getlist(key)) != 1 for key in allowed):
                raise ValueError("unexpected or repeated query parameters")
            year_raw = request.args.get("year", "")
            if len(year_raw) != 1 or year_raw not in "123456":
                raise ValueError("year")
            year = int(year_raw)
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
                component = request.args.get("component")
                if kind == "units":
                    items = unit_options(db, year, subject, component)
                else:
                    items = pdp_options(db, year, subject, request.args.get("unit", ""), component)
            if len(items) > 500:
                return jsonify({"error": "curriculum result exceeds safe limit"}), 503
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
        try:
            if set(request.args) != {"year", "subject", "lesson"} or any(
                len(request.args.getlist(k)) != 1 for k in ("year", "subject", "lesson")
            ):
                raise ValueError("invalid query")
            year = request.args["year"]
            subject = request.args["subject"]
            lesson = request.args["lesson"]
            if not year.isascii() or not year.isdecimal() or int(year) not in range(1, 7):
                raise ValueError("invalid year")
            if not lesson.isascii() or not lesson.isdecimal() or len(lesson) > 12:
                raise ValueError("invalid lesson")
            if subject != "ENGLISH" or int(year) not in (1, 2, 3):
                return jsonify({"source": "telegram-runtime-v1", "items": []})
            from web.telegram_english_rph_bridge import verified_english_rph_metadata
            items = verified_english_rph_metadata(database_path_provider(), int(year), int(lesson))
            return jsonify({"source": "telegram-runtime-v1", "items": items})
        except ValueError:
            return jsonify({"error": "invalid selection"}), 400
        except Exception:
            return jsonify({"error": "authoritative source unavailable"}), 503

    return bp
