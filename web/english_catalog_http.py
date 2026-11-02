"""Read-only English lesson inventory API for Web V1 staging.

Shows real available lesson numbers without exposing draft content.
This is navigation ONLY, not an RPH generation or approval endpoint.
"""
from flask import Blueprint, jsonify, request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english"


def create_english_catalog_blueprint(root=ROOT):
    bp = Blueprint("web_english_catalog", __name__)

    @bp.get("/api/web/catalog/english/<int:year>")
    def lessons(year):
        from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
        from web_v1_sessions import verify_session_ticket
        config = _config()
        if config is None:
            return jsonify({"error": "Login not configured"}), 503
        uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
        if uid is None:
            return jsonify({"error": "Authentication required"}), 401
        try:
            account = _lookup(config, uid)
        except Exception:
            return jsonify({"error": "Account lookup unavailable"}), 503
        if not account or account.get("telegram_user_id") != uid:
            return jsonify({"error": "Existing account required"}), 403
        if year not in (1, 2, 3):
            return jsonify({"error": "Unsupported year"}), 404
        folder = Path(root) / f"year{year}"
        from web.english_release_gate import load_release_ready_english
        entries = []
        for n in range(1, 161):
            if (folder / f"lesson_{n:03d}.md").is_file():
                try:
                    load_release_ready_english(year, n)
                    approved = True
                except (LookupError, ValueError, OSError):
                    approved = False
                entries.append({"lesson_no": n, "label": f"Lesson {n}", "approved": approved, "status": "ready" if approved else "pending_qa"})
        response = jsonify({
            "year": year, "subject": "ENGLISH",
            "lessons": entries, "count": len(entries),
            "notice": "Lesson yang belum diluluskan masih menunggu pengesahan QA; fail asal tidak diubah.",
        })
        response.headers["Cache-Control"] = "no-store, private"
        return response

    return bp
