"""Isolated opt-in CikguLaju web blueprint.

Only the public, read-only catalog can be enabled independently for staging.
RPH generation, login and entitlements remain disabled until audited.
"""
from flask import Blueprint, jsonify

web_v1 = Blueprint("cikgulaju_web_v1", __name__, url_prefix="/web")


@web_v1.get("/health")
def health():
    return jsonify({"component": "cikgulaju-web-v1", "status": "catalog-preview"})


def register_web_v1(app, *, enabled=False, catalog_only=False):
    """Register only explicitly approved read-only routes in staging."""
    if not enabled:
        return False
    if not catalog_only:
        raise RuntimeError("Full web requires approved auth, quota and RPH integration.")
    from web.english_catalog_http import create_english_catalog_blueprint
    app.register_blueprint(web_v1)
    app.register_blueprint(create_english_catalog_blueprint())
    return True
