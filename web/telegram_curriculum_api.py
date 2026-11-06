"""Read-only curriculum API mounted in the Telegram runtime, never the Web snapshot.

Register with app.register_blueprint(create_curriculum_blueprint(lambda: DB_PATH))
only after reviewing the production integration. The callback must resolve the
active master database on each request.
"""
import hmac
import os
from flask import Blueprint, jsonify, request
from web_v1_dropdown_catalog import (
    available_subject_options, unit_options, pdp_options,
    bm_theme_options, bm_unit_options, bm_topic_options, bm_pdp_options,
)


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

    def read_bm_hierarchy(kind):
        """Source-only: BM hierarchy comes directly from Telegram master SQLite."""
        required = {
            "bm-themes": {"year", "subject"},
            "bm-units": {"year", "subject", "theme"},
            "bm-topics": {"year", "subject", "theme", "unit"},
            "bm-pdp": {"year", "subject", "theme", "unit", "topic"},
        }[kind]
        try:
            args = request.args
            if (set(args) != required or
                    any(len(args.getlist(k)) != 1 for k in required) or
                    args["subject"] != "BM" or
                    args["year"] not in "123456" or len(args["year"]) != 1):
                raise ValueError("Invalid BM hierarchy request")
            year = int(args["year"])
            for field in ("theme", "unit", "topic"):
                if field in args and (not args[field].strip()
                                      or len(args[field]) > 300):
                    raise ValueError("Invalid BM hierarchy key")
            db = database_path_provider()
            if not db:
                raise FileNotFoundError("Master database unavailable")
            if kind == "bm-themes":
                items = bm_theme_options(db, year)
            elif kind == "bm-units":
                items = bm_unit_options(db, year, args["theme"])
            elif kind == "bm-topics":
                items = bm_topic_options(db, year, args["theme"], args["unit"])
            else:
                items = bm_pdp_options(db, year, args["theme"],
                                       args["unit"], args["topic"])
            if len(items) > 500:
                raise ValueError("Oversized BM hierarchy")
            return jsonify({"source": "telegram-runtime-v1", "items": items})
        except ValueError:
            return jsonify({"error": "invalid BM selection"}), 400
        except Exception:
            return jsonify({"error": "verified BM hierarchy unavailable"}), 503

    @bp.get("/internal/curriculum/v1/bm-themes")
    def bm_themes():
        return read_bm_hierarchy("bm-themes")

    @bp.get("/internal/curriculum/v1/bm-units")
    def bm_units():
        return read_bm_hierarchy("bm-units")

    @bp.get("/internal/curriculum/v1/bm-topics")
    def bm_topics():
        return read_bm_hierarchy("bm-topics")

    @bp.get("/internal/curriculum/v1/bm-pdp")
    def bm_pdps():
        return read_bm_hierarchy("bm-pdp")

    @bp.get("/internal/curriculum/v1/approved-materials")
    def approved_materials():
        # No material is exposed without a verified approval mapping and
        # authorized delivery. Never manufacture downloadable file URLs.
        return jsonify({"error": "approved material mapping unavailable"}), 503

    return bp
