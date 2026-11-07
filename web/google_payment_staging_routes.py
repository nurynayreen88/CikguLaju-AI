"""Staging-only Google Web receipt queue and Telegram-admin review endpoints.

Google-only users never need a Telegram account. Legacy Telegram payments are
unmodified. All data is in a SEPARATE staging Supabase project.
"""
import json
import os
import uuid
from flask import Blueprint, jsonify, make_response, request, send_file, current_app
from io import BytesIO
from pathlib import Path

from web.google_auth_staging_routes import (
    TICKET_COOKIE, _enabled_config,
)
from web_google_identity_sessions import verify_google_identity_ticket
from web.google_payment_store import (
    MAX_RECEIPT, PaymentConflict, PaymentUnavailable,
    admin_payment, admin_pending, account_display_name, eligible_plans, my_payments,
    private_receipt, review_payment, submit_receipt, web_payment_access,
)
from web.provider_neutral_payment import verified_payment_actor

bp = Blueprint("google_web_payment_staging", __name__)


@bp.after_request
def private_headers(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _config():
    cfg = _enabled_config()
    if cfg is None:
        return None
    return cfg


def _google_account():
    config = _config()
    if not config:
        return None, None, (jsonify({"error": "Staging Google tidak tersedia"}), 503)
    account_id = verify_google_identity_ticket(
        request.cookies.get(TICKET_COOKIE), config["secret"])
    if not account_id:
        return None, None, (jsonify({"error": "Log masuk Google diperlukan"}), 401)
    try:
        actor = verified_payment_actor(account_id, "google")
    except ValueError:
        return None, None, (jsonify({"error": "Akaun Google tidak sah"}), 401)
    return config, actor.account_id, None


def _reviewer():
    config = _config()
    if not config:
        return None, None, (jsonify({"error": "Staging tidak tersedia"}), 503)
    raw = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ADMIN_TELEGRAM_IDS", "")
    try:
        allowed = {int(x) for x in raw.split(",") if x.strip() and x.strip().isdigit()}
    except ValueError:
        allowed = set()
    if not allowed:
        return None, None, (jsonify({"error": "Admin staging belum ditetapkan"}), 503)

    from web_v1_telegram_auth_routes import COOKIE, _config as legacy_config, _lookup
    from web_v1_sessions import verify_session_ticket
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["secret"])
    if type(uid) is not int or uid not in allowed:
        return None, None, (jsonify({"error": "Admin Telegram diperlukan"}), 403)
    # Only an allowlisted, signed Telegram identity may hit the legacy
    # account backend, preventing data/config probing by anonymous browsers.
    old = legacy_config()
    if old is None:
        return None, None, (jsonify({"error": "Pengesahan admin belum tersedia"}), 503)
    try:
        account = _lookup(old, uid)
    except Exception:
        return None, None, (jsonify({"error": "Semakan admin gagal"}), 503)
    if not account or account.get("telegram_user_id") != uid:
        return None, None, (jsonify({"error": "Admin tidak disahkan"}), 403)
    return config, uid, None


def _catalog():
    # Prices are authoritative only after explicit staging configuration.
    raw = os.environ.get("CIKGULAJU_GOOGLE_STAGING_PAYMENT_CATALOG_JSON", "")
    if not raw or len(raw) > 3072:
        raise PaymentUnavailable("Katalog bayaran belum diluluskan")
    try:
        result = json.loads(raw)
    except ValueError:
        raise PaymentUnavailable("Katalog bayaran tidak sah") from None
    if not isinstance(result, dict):
        raise PaymentUnavailable("Katalog bayaran tidak sah")
    return result


def _same_origin(cfg):
    return (request.headers.get("Origin") == cfg["origin"]
            and request.headers.get("Sec-Fetch-Site", "same-origin") in
                ("same-origin", "none"))


@bp.get("/google-staging-payments")
def google_payment_page():
    config, uid, error = _google_account()
    if error:
        return error
    return send_file(Path(__file__).with_name("google_staging_payment.html"),
                     mimetype="text/html", max_age=0)


@bp.get("/admin/google-staging-payments")
def google_payment_admin_page():
    config, admin_uid, error = _reviewer()
    if error:
        return error
    return send_file(Path(__file__).with_name("google_staging_admin_payments.html"),
                     mimetype="text/html", max_age=0)


@bp.get("/api/web/google/payments")
def own_payments():
    config, uid, error = _google_account()
    if error:
        return error
    try:
        return jsonify({"payments": my_payments(config, uid),
                        "access": web_payment_access(config, uid),
                        "plans": eligible_plans(config, _catalog()),
                        "payment_url": os.environ.get("CIKGULAJU_GOOGLE_STAGING_PAYMENT_URL", "")})
    except (PaymentUnavailable, ValueError):
        return jsonify({"error": "Status pembayaran belum tersedia"}), 503


@bp.post("/api/web/google/payments")
def upload_payment():
    config, uid, error = _google_account()
    if error:
        return error
    if not _same_origin(config):
        return jsonify({"error": "Asal permintaan tidak disahkan"}), 403
    if request.content_length is None or request.content_length > MAX_RECEIPT + 16384:
        return jsonify({"error": "Resit melebihi had 4 MB"}), 413
    if request.mimetype != "multipart/form-data":
        return jsonify({"error": "Gunakan borang resit"}), 400
    if set(request.form) != {"plan_code"} or len(request.form.getlist("plan_code")) != 1:
        return jsonify({"error": "Pakej tidak sah"}), 400
    if set(request.files) != {"receipt"} or len(request.files.getlist("receipt")) != 1:
        return jsonify({"error": "Sila muat naik satu resit"}), 400
    file = request.files["receipt"]
    raw = file.stream.read(MAX_RECEIPT + 1)
    mime = file.mimetype
    try:
        request_id = submit_receipt(
            config, uid, request.form["plan_code"], _catalog(), raw, mime)
    except PaymentConflict as exc:
        return jsonify({"error": str(exc)}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except PaymentUnavailable as exc:
        return jsonify({"error": str(exc)}), 503

    # Best effort Telegram admin notification; the durable pending DB row
    # always remains available to Web admin if messaging fails.
    notified = False
    try:
        from web.google_payment_admin_notify import notify_google_payment_admin
        try:
            display_name = account_display_name(config, uid)
        except PaymentUnavailable:
            display_name = ""
        notified = notify_google_payment_admin(
            config, request_id, uid, request.form["plan_code"], mime, raw,
            display_name=display_name)
    except Exception:
        current_app.logger.warning("Google staging payment admin notification unavailable")
    response = jsonify({"payment_id": request_id, "status": "pending",
                        "telegram_admin_notified": notified})
    response.status_code = 201
    return response


@bp.get("/api/web/google/admin/payments")
def admin_pending_list():
    config, admin_uid, error = _reviewer()
    if error:
        return error
    try:
        return jsonify({"payments": admin_pending(config)})
    except PaymentUnavailable:
        return jsonify({"error": "Senarai bayaran belum tersedia"}), 503


@bp.get("/api/web/google/admin/payments/<request_id>")
def admin_detail(request_id):
    config, admin_uid, error = _reviewer()
    if error:
        return error
    try:
        row = admin_payment(config, request_id)
    except (ValueError, PaymentUnavailable):
        return jsonify({"error": "Rekod bayaran tidak sah"}), 503
    if not row:
        return jsonify({"error": "Rekod tidak ditemui"}), 404
    # Only authenticated admin sees the private receipt path. Browser should
    # use the authenticated receipt proxy, never a Storage public URL.
    row.pop("receipt_storage_path", None)
    return jsonify({"payment": row})


@bp.get("/api/web/google/admin/payments/<request_id>/receipt")
def admin_receipt(request_id):
    config, admin_uid, error = _reviewer()
    if error:
        return error
    try:
        result = private_receipt(config, request_id)
    except (ValueError, PaymentUnavailable):
        return jsonify({"error": "Resit belum dapat dibaca"}), 503
    if result is None:
        return jsonify({"error": "Resit tidak ditemui"}), 404
    raw, mime = result
    response = send_file(BytesIO(raw), mimetype=mime, as_attachment=False,
                         download_name="CikguLaju_resit" + {
                             "application/pdf": ".pdf", "image/png": ".png",
                             "image/jpeg": ".jpg", "image/webp": ".webp"}[mime],
                         max_age=0)
    return response


@bp.post("/api/web/google/admin/payments/<request_id>/review")
def admin_review(request_id):
    config, admin_uid, error = _reviewer()
    if error:
        return error
    if not _same_origin(config):
        return jsonify({"error": "Asal permintaan tidak sah"}), 403
    if (request.mimetype != "application/json" or request.content_length is None
            or request.content_length > 1024):
        return jsonify({"error": "Permintaan tidak sah"}), 400
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) - {"action", "note"}:
        return jsonify({"error": "Tindakan tidak sah"}), 400
    action, note = body.get("action"), body.get("note", "")
    if (action not in ("approve", "reject") or not isinstance(note, str)
            or (action == "reject" and not note.strip())):
        return jsonify({"error": "Tindakan tidak sah"}), 400
    try:
        return jsonify(review_payment(config, request_id, action, admin_uid, note))
    except PermissionError:
        return jsonify({"error": "Pengesahan admin diperlukan"}), 403
    except ValueError:
        return jsonify({"error": "Rekod atau nota tidak sah"}), 400
    except PaymentUnavailable:
        return jsonify({"error": "Pengesahan bayaran belum dapat dipastikan"}), 503
