"""Opt-in Telegram Pioneer integration; installs without replacing existing handlers.

Install only after the bot's existing callback/menu/access helpers are defined.
"""
from pioneer_supabase import effective_access, grant_pioneer, has_pioneer


def install(ns):
    original_callback = ns["callback"]
    original_menu = ns["menu"]
    original_access = ns["_access_info"]
    original_card = ns["_admin_pending_card"]
    send = ns["send"]
    state = ns["state"]
    sb = ns["_sb_request"]

    def send_pioneer_qr(cid, rid):
        import base64
        import json
        from io import BytesIO
        import requests
        caption = ("🏆 <b>PIONEER CIKGULAJU — RM20</b>\n\n"
                   "Imbas QR DuitNow ini dan bayar RM20 sekali sahaja.\n"
                   "Hantar resit untuk semakan admin. Status hanya aktif selepas disahkan.")
        markup = {"inline_keyboard": [
            [{"text": "📎 Hantar Resit RM20", "callback_data": "pioneer_receipt"}],
            [{"text": "🏠 Menu Utama", "callback_data": "home"}]]}
        data = {"chat_id": str(cid), "caption": caption,
                "parse_mode": "HTML", "reply_markup": json.dumps(markup)}
        file_id = ns.get("_donation_qr_file_id")
        if file_id:
            response = requests.post(ns["API"] + "/sendPhoto",
                                     data=dict(data, photo=file_id), timeout=30)
        else:
            qr = base64.b64decode(ns["DONATION_QR_B64"])
            response = requests.post(ns["API"] + "/sendPhoto", data=data,
                                     files={"photo": ("CikguLaju_DuitNow_QR.jpg", BytesIO(qr), "image/jpeg")},
                                     timeout=45)
        if not response.ok:
            return send(cid, "⚠️ QR tidak dapat dihantar. Cuba lagi sebentar.")
        return response

    def access_info(cid):
        # Pioneer is independent of subscription expiry or subscription API failures.
        if has_pioneer(sb, cid):
            return {"active": True, "status": "pioneer", "access_start": None,
                    "access_until": None, "days_left": None,
                    "plan_code": "PIONEER_LIFETIME"}
        return original_access(cid)

    def menu(cid, show_persistent=False):
        # Permanent Pioneer entry is included in app.py main menu.
        return original_menu(cid, show_persistent=show_persistent)

    def admin_card(cid, request_id):
        req = ns["_payment_request"](request_id)
        if req and float(req["amount"]) == 20.0 and req["status"] == "pending":
            if not ns["_is_admin"](cid):
                return send(cid, "⛔ Admin sahaja.")
            return send(cid, "🏆 <b>PENGESAHAN PIONEER RM20</b>\n"
                        f"Permohonan #{request_id}, pengguna {req['chat_id']}\n"
                        "Semak transaksi masuk dalam TNG Merchant secara manual sebelum lulus.",
                        [[{"text": "✅ Sahkan Pioneer", "callback_data": f"admin_approve|{request_id}"}],
                         [{"text": "❌ Tolak", "callback_data": f"admin_reject|{request_id}"}]])
        return original_card(cid, request_id)

    def callback(cid, d):
        if d == "pioneer_join":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Pioneer anda sudah aktif.")
            return send(cid, "🏆 <b>PIONEER CIKGULAJU — RM20 SEKALI SAHAJA</b>\n"
                        "Tiada yuran bulanan atau tahunan. Tempat terhad.\n"
                        "Status Pioneer kekal walaupun sistem dikemas kini.",
                        [[{"text": "💳 Papar QR & Hantar Resit", "callback_data": "pioneer_pay"}],
                         [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        if d == "pioneer_receipt":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Pioneer anda sudah aktif.")
            pending = ns["_latest_pending_payment"](cid)
            if not pending or float(pending.get("amount", 0)) != 20.0:
                return send(cid, "⚠️ Mulakan permohonan Pioneer RM20 dahulu sebelum menghantar resit.")
            if pending.get("notes") == "proof_received_admin_notified":
                return send(cid, "⌛ Resit Pioneer RM20 sudah diterima. Tunggu semakan admin; tidak perlu hantar semula.")
            state.setdefault(cid, {})["waiting"] = "payment_proof"
            return send(cid, "📎 Sila hantar gambar atau PDF resit bayaran RM20.")
        if d == "pioneer_pay":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Pioneer anda sudah aktif.")
            pending = ns["_latest_pending_payment"](cid)
            if pending and float(pending["amount"]) != 20.0:
                return send(cid, "⚠️ Ada permohonan pembayaran lain yang belum selesai. "
                            "Sila selesaikan permohonan tersebut dahulu.")
            if pending and pending.get("notes") == "proof_received_admin_notified":
                return send(cid, "⌛ Resit Pioneer RM20 sudah diterima dan menunggu semakan admin. Tidak perlu hantar semula.")
            if pending:
                rid = pending["id"]
            else:
                rid = ns["_new_payment_request"](cid, None, 20.0)
                ns["_set_payment_note"](rid, "awaiting_proof")
            state.setdefault(cid, {})["waiting"] = "payment_proof"
            # Existing QR bytes are reused, not copied into a new asset.
            return send_pioneer_qr(cid, rid)
        if str(d).startswith("admin_approve|"):
            if not ns["_is_admin"](cid):
                return send(cid, "⛔ Admin sahaja.")
            try:
                rid = int(str(d).split("|", 1)[1])
            except (ValueError, IndexError):
                return original_callback(cid, d)
            req = ns["_payment_request"](rid)
            if req and float(req["amount"]) == 20.0:
                if req["status"] != "pending":
                    return admin_card(cid, rid)
                if req.get("notes") != "proof_received_admin_notified":
                    return send(cid, "⚠️ Resit belum direkodkan. Jangan aktifkan Pioneer.")
                # Admin has manually verified the bank transaction before clicking Approve.
                try:
                    grant_pioneer(sb, req["chat_id"], f"pioneer-payment-request:{rid}", cid, verified=True)
                except Exception as exc:
                    return send(cid, f"⚠️ Pioneer belum diaktifkan: {type(exc).__name__}. Semak rekod.")
                ns["_mark_payment_request"](rid, "approved", cid, "Pioneer RM20 manually verified by admin")
                send(cid, f"✅ Pioneer diaktifkan untuk {req['chat_id']}.")
                return send(req["chat_id"], "🏆 <b>Status Pioneer Anda: AKTIF</b>\n\nAnda menikmati akses tanpa bayaran langganan bulanan atau tahunan sepanjang CikguLaju AI beroperasi.",
                            [[{"text": "🏠 Kembali ke Menu Utama", "callback_data": "home"}]])
        return original_callback(cid, d)

    ns["_access_info"] = access_info
    ns["_admin_pending_card"] = admin_card
    ns["callback"] = callback
    ns["menu"] = menu
    return True
