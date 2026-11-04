"""Do not persist pending payments until an actual receipt is submitted.

A QR view and "Hantar Resit" button set only a transient in-memory plan
intent. The existing webhook validates the uploaded photo/PDF, calls the
normal Supabase new-payment operation and forwards the receipt to admin.
No payment, credit, referral or entitlement records are modified here.
"""
from __future__ import annotations

import base64
import json
from io import BytesIO


def _valid_receipt_message(rt, cid):
    try:
        u = rt.request.get_json(silent=True) or {}
        msg = u.get("message") or {}
        chat = msg.get("chat") or {}
        sender = msg.get("from") or {}
        if (str(chat.get("type")) != "private"
                or str(chat.get("id")) != str(cid)
                or str(sender.get("id")) != str(cid)
                or not isinstance(msg.get("message_id"), int)
                or msg["message_id"] <= 0):
            return None
        photos = msg.get("photo") or []
        document = msg.get("document") or {}
        if (isinstance(photos, list) and photos
                and isinstance(photos[-1], dict)
                and photos[-1].get("file_id")):
            return msg
        if isinstance(document, dict) and document.get("file_id"):
            mime = str(document.get("mime_type") or "").lower()
            name = str(document.get("file_name") or "").lower()
            if (mime in ("application/pdf", "image/jpeg", "image/png", "image/webp")
                    or name.endswith((".pdf", ".jpg", ".jpeg", ".png", ".webp"))):
                return msg
    except (AttributeError, KeyError, TypeError, ValueError):
        pass
    return None


def install(rt):
    """Install after durable Supabase adapter and all existing callback bridges."""
    if getattr(rt, "CIKGULAJU_PROOF_FIRST_PAYMENT_ACTIVE", False):
        return True
    required = ("_new_payment_request", "_latest_pending_payment",
                "_payment_request", "send_subscription_payment",
                "send", "_is_admin")
    if any(not callable(getattr(rt, x, None)) for x in required):
        return False
    if not isinstance(getattr(rt, "state", None), dict):
        return False
    if not getattr(rt, "API", None) or not getattr(rt, "DONATION_QR_B64", None):
        return False

    original_new = rt._new_payment_request
    original_latest = rt._latest_pending_payment
    send = rt.send

    def draft(cid):
        state = rt.state.get(cid, {})
        if not isinstance(state, dict) or state.get("waiting") != "payment_proof":
            return None
        amount = state.get("payment_amount")
        try:
            amount = float(amount)
        except (TypeError, ValueError, OverflowError):
            return None
        return amount if amount in (5.00, 10.00) else None

    def pending(cid):
        existing = original_latest(cid)
        # Read-only "virtual" record. It has NO ID and is never written to DB.
        # Only the webhook's currently uploaded photo/PDF may reveal it.
        if existing:
            return existing
        amount = draft(cid)
        if amount is None or _valid_receipt_message(rt, cid) is None:
            return None
        return {"id": None, "amount": amount, "status": "pending",
                "notes": "awaiting_proof"}

    def new_on_receipt(cid, message_id=None, amount=5.00):
        selected_amount = draft(cid)
        media = _valid_receipt_message(rt, cid)
        if (selected_amount is None or media is None
                or message_id != media["message_id"]):
            raise ValueError("Payment request requires a private user-uploaded receipt")
        # The amount argument from old app.py is a legacy default (RM5).
        # The selected plan is authoritative for this receipt.
        rid = original_new(cid, message_id, selected_amount)
        record = rt._payment_request(rid)
        if (not record or str(record.get("chat_id")) != str(cid)
                or float(record.get("amount", -1)) != selected_amount
                or record.get("status") != "pending"):
            raise RuntimeError("Pending receipt does not match selected plan/customer")
        return rid

    def subscription_qr(cid):
        try:
            existing = original_latest(cid)
        except Exception as exc:
            print("PROOF-FIRST subscription status unavailable:",
                  type(exc).__name__, flush=True)
            return send(cid, "⚠️ Status bayaran tidak dapat disemak. "
                        "Cuba semula sebelum membuat bayaran.")
        if existing and float(existing.get("amount", 0)) != 5.00:
            return send(cid, "⚠️ Ada permohonan bayaran lain yang sedang menunggu. "
                        "Sila semak permohonan itu dahulu.")
        if existing and existing.get("notes") == "proof_received_admin_notified":
            return send(cid, "⌛ Resit bayaran telah diterima dan sedang disemak admin. "
                        "Tidak perlu membayar semula.")

        intent = rt.state.setdefault(cid, {})
        intent["waiting"] = "payment_proof"
        intent["payment_amount"] = 5.00
        caption = (
            "💳 <b>BAYARAN CIKGULAJU</b>\n\n"
            "📦 Pakej: <b>AKSES 30 HARI</b>\n"
            "💰 Jumlah: <b>RM5.00</b>\n\n"
            "<b>CARA BAYAR:</b>\n"
            "1️⃣ Imbas QR DuitNow ini dan bayar RM5.00.\n"
            "2️⃣ Ambil gambar atau PDF resit pembayaran.\n"
            "3️⃣ Hantar resit itu dalam chat ini.\n\n"
            "Permohonan hanya direkod apabila resit dihantar.\n"
            "Akses diaktifkan selepas pengesahan admin."
        )
        keyboard = {"inline_keyboard": [
            [{"text": "📎 Hantar Resit", "callback_data": "subscribe_500"}],
            [{"text": "❌ Batal", "callback_data": "cancel_payment"}],
            [{"text": "🏠 Menu Utama", "callback_data": "home"}],
        ]}
        markup = json.dumps(keyboard, ensure_ascii=False)
        try:
            import requests
            qr = base64.b64decode(rt.DONATION_QR_B64, validate=True)
            cached = getattr(rt, "_donation_qr_file_id", None)
            if cached:
                sent = requests.post(rt.API + "/sendPhoto", data={
                    "chat_id": str(cid), "photo": cached,
                    "caption": caption, "parse_mode": "HTML",
                    "reply_markup": markup}, timeout=30)
                if sent.ok and sent.json().get("ok") is True:
                    return sent
            sent = requests.post(rt.API + "/sendPhoto", data={
                "chat_id": str(cid), "caption": caption,
                "parse_mode": "HTML", "reply_markup": markup
            }, files={"photo": ("CikguLaju_DuitNow_QR.jpg",
                                BytesIO(qr), "image/jpeg")}, timeout=45)
            if sent.ok and sent.json().get("ok") is True:
                try:
                    photos = sent.json()["result"].get("photo") or []
                    if photos:
                        rt._donation_qr_file_id = photos[-1].get("file_id")
                except (KeyError, TypeError, AttributeError):
                    pass
                return sent
            fallback = requests.post(rt.API + "/sendDocument", data={
                "chat_id": str(cid), "caption": caption,
                "parse_mode": "HTML", "reply_markup": markup
            }, files={"document": ("CikguLaju_DuitNow_QR.jpg",
                                   BytesIO(qr), "image/jpeg")}, timeout=45)
            if fallback.ok and fallback.json().get("ok") is True:
                return fallback
        except Exception as exc:
            print("PROOF-FIRST subscription QR failure:",
                  type(exc).__name__, flush=True)
        return send(cid, "⚠️ QR tidak berjaya dihantar. Tekan Cuba Semula.",
                    [[{"text": "🔄 Cuba Semula", "callback_data": "subscribe_500"}],
                     [{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    rt._new_payment_request = new_on_receipt
    rt._latest_pending_payment = pending
    rt.send_subscription_payment = subscription_qr
    rt.CIKGULAJU_PROOF_FIRST_PAYMENT_ACTIVE = True
    return True
