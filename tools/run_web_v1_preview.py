"""Run the isolated Web V1 preview without importing production app.py.

Local-only command:
    python tools/run_web_v1_preview.py

The preview optionally reads a local SQLite database in read-only mode.\nIt has no authentication, credit or generation endpoints.
Do not expose this development server to the public internet.
"""
import os
from pathlib import Path
import sys

from flask import Flask, send_file, jsonify, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web_v1_dropdown_catalog import subject_options, unit_options, pdp_options
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
        kind = request.args.get("kind", "")
        if kind == "subjects":
            return jsonify(subject_options(year))
        db = os.environ.get("CIKGULAJU_WEB_PREVIEW_DB", "")
        if not db:
            return jsonify({"error": "preview database not configured"}), 503
        subject = request.args.get("subject", "")
        if kind == "units":
            return jsonify(unit_options(db, year, subject))
        if kind == "pdp":
            return jsonify(pdp_options(db, year, subject, request.args.get("unit", "")))
        return jsonify({"error": "invalid option kind"}), 400
    except (ValueError, FileNotFoundError):
        return jsonify({"error": "invalid selection or unavailable database"}), 400
    except Exception:
        app.logger.exception("Preview dropdown read failed")
        return jsonify({"error": "dropdown temporarily unavailable"}), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
