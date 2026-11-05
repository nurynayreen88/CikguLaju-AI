"""Private QR/payment plan source for the separate CikguLaju Web service.

Never creates a payment record, accepts a receipt, or changes subscription
entitlements. Keep the existing Telegram QR and amount as the source of truth.
"""
import base64
import binascii
import hmac
import os
import re
from flask import Blueprint, Response, jsonify, request

MIN_TOKEN=32
MAX_QR=2*1024*1024


def _qr_data(runtime):
    encoded=getattr(runtime, "DONATION_QR_B64", None)
    if not isinstance(encoded,str) or len(encoded)>MAX_QR*2 or not encoded:
        raise ValueError("Payment QR unavailable")
    try:
        raw=base64.b64decode(encoded,validate=True)
    except (binascii.Error,ValueError):
        raise ValueError("Invalid payment QR")
    if not 800<=len(raw)<=MAX_QR:
        raise ValueError("Invalid payment QR length")
    if raw.startswith(b"\xff\xd8\xff"):
        return raw,"image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return raw,"image/png"
    raise ValueError("Invalid payment QR image")


def create_web_payment_source(runtime):
    bp=Blueprint("telegram_web_payment_source",__name__)

    @bp.after_request
    def no_cache(response):
        response.headers["Cache-Control"]="no-store, private"
        response.headers["X-Content-Type-Options"]="nosniff"
        return response

    def authorized():
        token=os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN","")
        header=request.headers.get("Authorization","")
        return len(token)>=MIN_TOKEN and hmac.compare_digest(header,"Bearer "+token)

    def active():
        # Web must not advertise payments when the durable proof-first queue
        # is unavailable on Telegram. Web writes the exact same Supabase table.
        return (bool(getattr(runtime,"CIKGULAJU_PROOF_FIRST_PAYMENT_ACTIVE",False))
                and os.environ.get("CIKGULAJU_SUPABASE_USER_RECORDS","0").lower()
                in ("1","true","yes"))

    @bp.get("/internal/payment/v1/catalog")
    def catalog():
        if not authorized():
            return jsonify({"error":"unauthorized"}),401
        if not active():
            return jsonify({"error":"proof-first payment queue unavailable"}),503
        try:
            _qr_data(runtime)
        except ValueError:
            return jsonify({"error":"payment QR unavailable"}),503
        # Use the ID from Telegram's *active bot API*, not a browser username.
        # A Web widget configured for a different bot must never submit a
        # receipt whose Telegram file_id the real admin bot cannot open.
        match=re.search(r"/bot([0-9]{5,15}):[A-Za-z0-9_-]{20,}$",
                        str(getattr(runtime,"API","")))
        if not match:
            return jsonify({"error":"Active Telegram bot identity unavailable"}),503
        return jsonify({
            "telegram_bot_id":match.group(1),
            "plans":[
                {"code":"rakan_pembangun","label":"Rakan Pembangun",
                 "amount":"10.00","description":"Bayaran sekali, akses seumur hidup"},
                {"code":"langganan_30_hari","label":"Langganan 30 Hari",
                 "amount":"5.00","description":"Akses selama 30 hari"},
            ],
            "currency":"MYR",
            "mode":"manual_receipt_review",
            "note":"QR tidak mencipta Pending. Resit diperlukan; admin sahkan secara manual.",
        })

    @bp.get("/internal/payment/v1/qr")
    def qr():
        if not authorized():
            return jsonify({"error":"unauthorized"}),401
        if not active():
            return jsonify({"error":"payment queue unavailable"}),503
        try:
            data,mime=_qr_data(runtime)
        except ValueError:
            return jsonify({"error":"QR unavailable"}),503
        return Response(data,mimetype=mime)
    return bp
