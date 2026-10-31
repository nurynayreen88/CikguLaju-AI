"""Isolated, opt-in CikguLaju web blueprint.

This module is NOT imported or registered by app.py. It must remain disabled
until authentication, entitlements and existing generation services are audited.
"""
from flask import Blueprint, jsonify

web_v1 = Blueprint("cikgulaju_web_v1", __name__, url_prefix="/web")


@web_v1.get("/health")
def health():
    """Non-sensitive readiness marker; not a production health check."""
    return jsonify({"component": "cikgulaju-web-v1", "status": "scaffold-only"})


def register_web_v1(app, *, enabled=False):
    """Explicit registration; safe by default and refuses accidental enablement."""
    if not enabled:
        return False
    raise RuntimeError(
        "CikguLaju Web V1 cannot be enabled until auth, quotas, "
        "RPH service and deployment tests are approved."
    )
