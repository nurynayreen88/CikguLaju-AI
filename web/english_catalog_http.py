"""Read-only English lesson inventory API for Web V1 staging.

Shows real available lesson numbers without exposing draft content.
This is navigation ONLY, not an RPH generation or approval endpoint.
"""
from flask import Blueprint, jsonify
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english"


def create_english_catalog_blueprint(root=ROOT):
    bp = Blueprint("web_english_catalog", __name__)

    @bp.get("/api/web/catalog/english/<int:year>")
    def lessons(year):
        if year not in (1, 2, 3):
            return jsonify({"error": "Unsupported year"}), 404
        folder = Path(root) / f"year{year}"
        entries = []
        for n in range(1, 161):
            if (folder / f"lesson_{n:03d}.md").is_file():
                entries.append({"lesson_no": n, "label": f"Lesson {n}"})
        response = jsonify({
            "year": year, "subject": "ENGLISH",
            "lessons": entries, "count": len(entries),
            "notice": "Inventory only. Lessons are not approved for download.",
        })
        response.headers["Cache-Control"] = "no-store"
        return response

    return bp
