"""Opt-in Telegram Pioneer integration; installs without replacing existing handlers.

Install only after the bot's existing callback/menu/access helpers are defined.
"""
from pioneer_supabase import effective_access, grant_pioneer, has_pioneer, pioneer_availability


def install(ns):
    original_callback = ns["callback"]
    original_menu = ns["menu"]
    original_access = ns["_access_info"]
    original_card = ns["_admin_pending_card"]
    original_user_card = ns["_admin_user_card"]
    send = ns["send"]
    state = ns["state"]
    sb = ns["_sb_request"]

    def send_pioneer_qr(cid, rid):
        import base64
        import json
        from io import BytesIO
        import requests
        caption = ("🏆 <b>PIONEER EARLY BIRD CIKGULAJU — RM10</b>\n\n"
                   "Imbas QR DuitNow ini dan bayar RM10 sekali sahaja.\n"
                   "Hantar resit untuk semakan admin. Status hanya aktif selepas disahkan.")
        markup = {"inline_keyboard": [
            [{"text": "📎 Hantar Resit RM10", "callback_data": "pioneer_receipt"}],
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
        # The main menu already has a 'Jadi Pioneer' button.
        # Show Pioneer price and benefits only when that button is selected.
        return original_menu(cid, show_persistent=show_persistent)

    def admin_pioneer_status(user_id):
        """Reusable status for the existing admin user-detail view."""
        try:
            active = has_pioneer(sb, user_id)
            count, remaining = pioneer_availability(sb)
            return ("🏆 Pioneer: " + ("AKTIF (seumur hidup)" if active else "TIDAK AKTIF")
                    + f"\n📊 {count}/500 Pioneer | {remaining} tempat berbaki")
        except Exception:
            return "🏆 Pioneer: Tidak dapat disemak"

    def admin_user_card(cid, target):
        # Preserve existing admin card and append a separate, verified status.
        result = original_user_card(cid, target)
        if ns["_is_admin"](cid):
            buttons = [[{"text": "👥 Senarai Pengguna", "callback_data": "admin_list|all|0"}]]
            if has_pioneer(sb, target):
                buttons.insert(0, [{"text": "🛑 Batalkan Status Pioneer", "callback_data": f"pioneer_revoke_ask|{target}"}])
            send(cid, f"👤 ID: <code>{target}</code>\\n" + admin_pioneer_status(target), buttons)
        return result

    def admin_card(cid, request_id):
        req = ns["_payment_request"](request_id)
        if req and float(req["amount"]) == 10.0 and req["status"] == "pending":
            if not ns["_is_admin"](cid):
                return send(cid, "⛔ Admin sahaja.")
            return send(cid, "🏆 <b>PENGESAHAN PIONEER RM10</b>\n"
                        f"Permohonan #{request_id}, pengguna {req['chat_id']}\n"
                        "Semak transaksi masuk dalam TNG Merchant secara manual sebelum lulus.",
                        [[{"text": "✅ Sahkan Pioneer", "callback_data": f"admin_approve|{request_id}"}],
                         [{"text": "❌ Tolak", "callback_data": f"admin_reject|{request_id}"}]])
        return original_card(cid, request_id)

    def quota_text():
        count, remaining = pioneer_availability(sb)
        return f"📊 {count}/500 Pioneer telah menyertai. {remaining} tempat berbaki."

    def callback(cid, d):
        if str(d).startswith(("pioneer_revoke_ask|", "pioneer_revoke_confirm|")):
            if not ns["_is_admin"](cid):
                return send(cid, "⛔ Admin sahaja.")
            try:
                action, raw_uid = str(d).split("|", 1)
                uid = int(raw_uid)
                if uid <= 0:
                    raise ValueError("Invalid user")
            except (ValueError, TypeError):
                return send(cid, "⚠️ ID tidak sah.")
            if action == "pioneer_revoke_ask":
                if not has_pioneer(sb, uid):
                    return send(cid, "ℹ️ Pioneer tidak aktif.")
                return send(cid, f"⚠️ Sahkan pembatalan Pioneer untuk ID <code>{uid}</code>. Rekod pembayaran tidak dipadam.",
                            [[{"text": "🛑 SAHKAN PEMBATALAN", "callback_data": f"pioneer_revoke_confirm|{uid}"}],
                             [{"text": "↩️ Kembali", "callback_data": f"admin_user|{uid}"}]])
            if not has_pioneer(sb, uid):
                return send(cid, "ℹ️ Pioneer sudah tidak aktif.")
            try:
                sb("POST", "rpc/revoke_pioneer_entitlement", json={"p_telegram_user_id": uid, "p_revoked_by": int(cid)})
            except Exception:
                return send(cid, "⚠️ Pembatalan gagal. Status tidak diubah.")
            return send(cid, f"✅ Pioneer ID <code>{uid}</code> telah dibatalkan.",
                        [[{"text": "👤 Lihat Pengguna", "callback_data": f"admin_user|{uid}"}]])
        if d == "pioneer_join":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Pioneer anda sudah aktif.")
            count, remaining = pioneer_availability(sb)
            return send(cid, "🏆 <b>PIONEER EARLY BIRD CIKGULAJU — RM10 SEKALI SAHAJA</b>\n"
                        "<b>Kelebihan Pioneer:</b>\n✅ Bayar RM10 sekali sahaja.\n✅ Guna CikguLaju AI tanpa perlu bayar langganan bulanan atau tahunan.\n♾️ Akses Pioneer seumur hidup.\n👩‍🏫 Sediakan RPH untuk pelbagai subjek.\n\nTerhad kepada 500 guru.\n" + quota_text() + "\n"
                        "Status Pioneer kekal walaupun sistem dikemas kini.",
                        [[{"text": "💳 Papar QR & Hantar Resit", "callback_data": "pioneer_pay"}],
                         [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        if d == "pioneer_receipt":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Pioneer anda sudah aktif.")
            pending = ns["_latest_pending_payment"](cid)
            if not pending or float(pending.get("amount", 0)) != 10.0:
                return send(cid, "⚠️ Mulakan permohonan Pioneer RM10 dahulu sebelum menghantar resit.")
            if pending.get("notes") == "proof_received_admin_notified":
                return send(cid, "⌛ Resit Pioneer RM10 sudah diterima. Tunggu semakan admin; tidak perlu hantar semula.")
            state.setdefault(cid, {})["waiting"] = "payment_proof"
            return send(cid, "📎 Sila hantar gambar atau PDF resit bayaran RM10.")
        if d == "pioneer_pay":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Pioneer anda sudah aktif.")
            if pioneer_availability(sb)[1] == 0:
                return send(cid, "⛔ Kuota 500 Pioneer Early Bird sudah penuh.")
            pending = ns["_latest_pending_payment"](cid)
            if pending and float(pending["amount"]) != 10.0:
                return send(cid, "⚠️ Ada permohonan pembayaran lain yang belum selesai. "
                            "Sila selesaikan permohonan tersebut dahulu.")
            if pending and pending.get("notes") == "proof_received_admin_notified":
                return send(cid, "⌛ Resit Pioneer RM10 sudah diterima dan menunggu semakan admin. Tidak perlu hantar semula.")
            if pending:
                rid = pending["id"]
            else:
                rid = ns["_new_payment_request"](cid, None, 10.0)
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
            if req and float(req["amount"]) == 10.0:
                if req["status"] != "pending":
                    return admin_card(cid, rid)
                if req.get("notes") != "proof_received_admin_notified":
                    return send(cid, "⚠️ Resit belum direkodkan. Jangan aktifkan Pioneer.")
                # Admin has manually verified the bank transaction before clicking Approve.
                try:
                    grant_pioneer(sb, req["chat_id"], f"pioneer-payment-request:{rid}", cid, verified=True)
                except Exception as exc:
                    # Do not mark payment approved when the entitlement grant fails.
                    # Expose a safe, actionable category to admin; full details stay in logs.
                    import re
                    detail = str(exc)
                    print('PIONEER APPROVAL FAILED:', f'payment_id={rid}',
                          f'user_id={req["chat_id"]}', repr(exc), flush=True)
                    if '403' in detail or '42501' in detail or 'permission denied' in detail.lower():
                        reason = 'Supabase menolak akses (HTTP 403 / kebenaran pangkalan data).'
                    elif '404' in detail or 'PGRST202' in detail:
                        reason = 'Fungsi kelulusan Pioneer tidak ditemui di Supabase.'
                    elif '409' in detail or 'already exists' in detail.lower() or 'duplicate' in detail.lower():
                        reason = 'Rekod Pioneer mungkin sudah wujud. Semak status sebelum cuba lagi.'
                    elif 'quota full' in detail.lower():
                        reason = 'Kuota Pioneer telah penuh.'
                    elif 'not configured' in detail.lower():
                        reason = 'Konfigurasi Supabase belum lengkap.'
                    else:
                        reason = f'Ralat sambungan atau pangkalan data ({type(exc).__name__}).'
                    return send(cid, f"⚠️ Pioneer belum diaktifkan untuk Payment ID #{rid}.\\n"
                                f"Sebab: {reason}\\n"
                                "Bayaran masih menunggu pengesahan. Jangan minta pengguna bayar semula.")
                ns["_mark_payment_request"](rid, "approved", cid, "Pioneer RM10 manually verified by admin")
                send(cid, f"✅ Pioneer diaktifkan untuk {req['chat_id']}.")
                return send(req["chat_id"], "🏆 <b>Status Pioneer Anda: AKTIF</b>\n\nAnda menikmati akses tanpa bayaran langganan bulanan atau tahunan sepanjang CikguLaju AI beroperasi.",
                            [[{"text": "🏠 Kembali ke Menu Utama", "callback_data": "home"}]])
        return original_callback(cid, d)

    ns["_access_info"] = access_info
    ns["_admin_pending_card"] = admin_card
    ns["_admin_user_card"] = admin_user_card
    ns["callback"] = callback
    ns["menu"] = menu
    ns["_admin_pioneer_status"] = admin_pioneer_status
    return True
