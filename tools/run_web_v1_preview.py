"""Run the isolated Web V1 preview without importing production app.py.

Local-only command:
    python tools/run_web_v1_preview.py

The preview optionally reads a local SQLite database in read-only mode.
It has no authentication, credit or generation endpoints.
Do not expose this development server to the public internet.
"""
import os
from pathlib import Path
import sys

from flask import Flask, send_file, jsonify, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web_v1_dropdown_catalog import subject_options, available_subject_options, unit_options, pdp_options, component_options
from web_v1_verified_pdp import list_explicit_pjpk_entries
PREVIEW = ROOT / "web_v1_preview" / "index.html"
app = Flask(__name__)


@app.get("/")
def preview():
    return send_file(PREVIEW, mimetype="text/html", conditional=True)


@app.get("/health")
def health():
    db = os.environ.get("CIKGULAJU_WEB_PREVIEW_DB", "")
    return {"status": "preview-only", "database_connected": bool(db and Path(db).is_file()), "generation_enabled": False}


@app.get("/api/options")
def options():
    """Local preview only. Never a production generation or entitlement endpoint."""
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



@app.get("/api/shared/status")
def shared_status():
    return jsonify({"shared_backend_connected": False, "telegram_account_linked": False, "generation_enabled": False, "download_enabled": False})

@app.get("/api/materials")
def materials():
    return jsonify({"error": "authentication and shared backend required"}), 503

@app.post("/api/generate")
def generate():
    return jsonify({"error": "shared generator not connected"}), 503

@app.get("/api/materials/download/<material_id>")
def download_material(material_id):
    return jsonify({"error": "authorized download service not connected"}), 503

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
