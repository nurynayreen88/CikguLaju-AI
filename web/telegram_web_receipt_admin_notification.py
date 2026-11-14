"""Private Web -> Telegram admin receipt notification.

Web uploads proof to the SAME bot and saves the authoritative Pending row in
Supabase first. This endpoint checks that exact row before notifying admin with
the original receipt and a safe button to the existing, admin-only review card.

No approval or entitlement grant can occur here. Importing/registering this
blueprint never sends a message. Does not mutate payment/user records.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from html import escape
import hmac
import os
import re

from flask import Blueprint, jsonify, request
import requests

from web.payment_receipt_admin_runtime import malaysia_time

MAX_REQUEST_BYTES = 2048
REVIEW_PATH = "/internal/payment/v1/admin-review-notify"


def _valid_pending_row(row, uid, rid):
    if not isinstance(row, dict):
        return False
    try:
        amount = Decimal(str(row.get("amount")))
    except (InvalidOperation, ValueError, TypeError):
        return False
    return (
        type(row.get("id")) is int
        and row["id"] == rid
        and str(row.get("chat_id")) == str(uid)
        and row.get("status") == "pending"
        and amount in (Decimal("10.00"), Decimal("20.00"))
        and row.get("notes") == "proof_received_web"
        and isinstance(row.get("proof_telegram_file_id"), str)
        and bool(row["proof_telegram_file_id"].strip())
        and type(row.get("proof_telegram_message_id")) is int
        and row["proof_telegram_message_id"] > 0
        and bool(row.get("proof_received_at"))
    )


def _keyboard(rid):
    return {"inline_keyboard": [
        [{"text": "🧾 Semak & Sahkan Bayaran",
          "callback_data": f"pioneer_review|{rid}"}],
        [{"text": "📋 Semua Pending",
          "callback_data": "admin_pending_all"}],
    ]}


def _telegram_ok(response, *, copying=False, admin=None):
    try:
        if not response.ok:
            return False
        data = response.json()
        if not isinstance(data, dict) or data.get("ok") is not True:
            return False
        item = data.get("result")
        if not isinstance(item, dict) or type(item.get("message_id")) is not int:
            return False
        if item["message_id"] < 1:
            return False
        if copying:
            # copyMessage returns MessageId; unlike sendMessage, no chat field.
            return True
        return (isinstance(item.get("chat"), dict)
                and str(item["chat"].get("id")) == str(admin))
    except (AttributeError, TypeError, ValueError):
        return False


def create_web_receipt_admin_notification(runtime):
    bp = Blueprint("web_payment_admin_review_notification", __name__)

    @bp.after_request
    def private_response(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.post(REVIEW_PATH)
    def notify():
        secret = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
        token = request.headers.get("Authorization", "")
        if len(secret) < 32 or not hmac.compare_digest(token, "Bearer " + secret):
            return jsonify({"error": "unauthorized"}), 401

        if (request.content_length is None or request.content_length > MAX_REQUEST_BYTES
                or not request.is_json):
            return jsonify({"error": "invalid request"}), 400
        data = request.get_json(silent=True)
        if (not isinstance(data, dict)
                or set(data) != {"request_id", "telegram_user_id"}
                or any(type(data.get(k)) is not int or not 0 < data[k] < 10**18
                       for k in ("request_id", "telegram_user_id"))):
            return jsonify({"error": "invalid payment identity"}), 400
        rid, uid = data["request_id"], data["telegram_user_id"]

        admin = str(getattr(runtime, "ADMIN_CHAT_ID", "") or "").strip()
        if (not getattr(runtime, "CIKGULAJU_PROOF_FIRST_PAYMENT_ACTIVE", False)
                or not callable(getattr(runtime, "_payment_request", None))
                or not callable(getattr(runtime, "_is_admin", None))
                or not callable(getattr(runtime, "send", None))
                or not getattr(runtime, "_PAYMENT_RECEIPT_ADMIN_INSTALLED", False)
                or not re.fullmatch(r"[1-9][0-9]{4,17}", admin)
                or not runtime._is_admin(admin)):
            return jsonify({"error": "Telegram admin review unavailable"}), 503

        try:
            row = runtime._payment_request(rid)
        except Exception as exc:
            print("WEB PAYMENT ADMIN NOTICE lookup unavailable:",
                  type(exc).__name__, flush=True)
            return jsonify({"error": "Authoritative payment record unavailable"}), 503
        if not _valid_pending_row(row, uid, rid):
            return jsonify({"error": "Payment not pending or proof identity does not match"}), 409

        timestamp = escape(malaysia_time(row.get("proof_received_at")))
        caption = (
            "💳 <b>RESIT BAYARAN WEB CIKGULAJU</b>\n\n"
            f"🧾 Permohonan: <b>#{rid}</b>\n"
            f"👤 ID pengguna: <code>{uid}</code>\n"
            "🏆 Pakej: <b>Rakan Pembangun</b>\n"
            f"💰 Jumlah: <b>RM{Decimal(str(row['amount'])):.2f}</b>\n"
            f"🕒 Resit dihantar: <b>{timestamp}</b>\n"
            "⏳ Status: <b>PENDING</b>\n\n"
            "Semak resit dan transaksi sebenar sebelum mengesahkan."
        )
        kb = _keyboard(rid)
        api = str(getattr(runtime, "API", ""))
        if not api.startswith("https://api.telegram.org/bot"):
            return jsonify({"error": "Telegram bot not configured"}), 503
        try:
            response = requests.post(
                api + "/copyMessage",
                json={"chat_id": admin, "from_chat_id": str(uid),
                      "message_id": row["proof_telegram_message_id"],
                      "caption": caption, "parse_mode": "HTML",
                      "reply_markup": kb},
                timeout=20,
            )
            if _telegram_ok(response, copying=True):
                return jsonify({"notified": True, "request_id": rid,
                                "review": "admin_only", "delivery": "receipt_with_buttons"})
        except requests.RequestException as exc:
            print("WEB PAYMENT ADMIN NOTICE receipt copy failed:",
                  type(exc).__name__, flush=True)

        # Fallback still contains ID-linked buttons. The admin can open the
        # durable receipt from the exact saved Telegram file_id.
        try:
            response = runtime.send(admin, caption, kb["inline_keyboard"])
            if _telegram_ok(response, admin=admin):
                return jsonify({"notified": True, "request_id": rid,
                                "review": "admin_only", "delivery": "review_buttons"})
        except Exception as exc:
            print("WEB PAYMENT ADMIN NOTICE fallback failed:",
                  type(exc).__name__, flush=True)
        return jsonify({"error": "Telegram admin notification unavailable"}), 503

    return bp
