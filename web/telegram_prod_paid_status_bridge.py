"""Opt-in, strictly read-only private production entitlement lookup.

Mounted only in the production Web WSGI when that deployment is explicitly
approved. It is NOT automatically deployed by the isolated staging service.
A dedicated internal bearer token and exact production host are mandatory.
No registration, payments, receipts, credit debits, or database changes.
"""
from datetime import datetime, timezone
import hmac
import os

from flask import Blueprint, jsonify, request

bp = Blueprint("cikgulaju_private_production_paid_status", __name__)
PRODUCTION_HOST = "cikgulaju-web.onrender.com"
SOURCE = "cikgulaju-prod-entitlements-v1"
MAX_BODY = 256


def _authorized():
    if os.environ.get("CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED") != "1":
        return False, 503
    token = os.environ.get("CIKGULAJU_PAID_BRIDGE_TOKEN", "")
    if not isinstance(token, str) or len(token) < 48:
        return False, 503
    if request.host != PRODUCTION_HOST:
        return False, 403
    header = request.headers.get("Authorization", "")
    if not hmac.compare_digest(header, "Bearer " + token):
        return False, 401
    return True, None


@bp.after_request
def prevent_private_cache(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Authorization"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.post("/internal/identity/v1/entitlements")
def private_entitlements():
    authorized, error = _authorized()
    if not authorized:
        return jsonify({"error": "Internal entitlement lookup unavailable"}), error
    if request.args or not request.is_json or request.content_length is None or request.content_length > MAX_BODY:
        return jsonify({"error": "Invalid internal request"}), 400
    body = request.get_json(silent=True)
    if (not isinstance(body, dict) or set(body) != {"telegram_user_id"}
            or type(body["telegram_user_id"]) is not int
            or not 0 < body["telegram_user_id"] <= 9223372036854775807):
        return jsonify({"error": "Invalid internal identity"}), 400
    uid = body["telegram_user_id"]
    try:
        from web_v1_telegram_auth_routes import _config, _lookup
        config = _config()
        if (not config or config.get("account_backend") != "supabase"
                or config.get("supabase_url", "").rstrip("/") !=
                "https://soxakntcanbycjoygrcx.supabase.co"):
            raise ValueError("Unexpected production account backend")
        data = _lookup(config, uid)
        if data is None:
            return jsonify({"error": "Existing Telegram account not found"}), 404
        if (not isinstance(data, dict) or data.get("authenticated") is not True
                or type(data.get("telegram_user_id")) is not int
                or data["telegram_user_id"] != uid
                or type(data.get("rakan_pembangun")) is not bool):
            raise ValueError("Unconfirmed account access")
        lifetime = data["rakan_pembangun"]
        expiry = data.get("vip_expires_at")
        active_subscription = False
        if expiry is not None:
            if not isinstance(expiry, str) or len(expiry) > 50:
                raise ValueError("Invalid subscription expiry")
            timestamp = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("Untrusted entitlement timezone")
            active_subscription = timestamp > datetime.now(timezone.utc)
        if not active_subscription:
            expiry = None
        # Do not return user name, profile, payment reference, approval admin,
        # credit history, transaction, or service/database configuration.
        return jsonify({
            "source": SOURCE, "telegram_user_id": uid,
            "registered": True,
            "rakan_pembangun_active": lifetime,
            "subscription_active": active_subscription,
            "subscription_expires_at": expiry,
        })
    except (ValueError, TypeError, KeyError, OSError, RuntimeError):
        return jsonify({"error": "Production entitlement source unavailable"}), 503
