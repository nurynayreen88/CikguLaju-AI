"""Opt-in Telegram Rakan Pembangun integration; installs without replacing existing handlers.

Install only after the bot's existing callback/menu/access helpers are defined.
"""
from pioneer_supabase import (
    effective_access, grant_pioneer, has_pioneer, pioneer_availability,
    reactivate_revoked_pioneer,
)
from pioneer_percentage import pioneer_percentage


def _has_recorded_payment_proof(payment):
    """Accept the existing Telegram receipt or a Web-uploaded Telegram file_id.

    A Web note alone is insufficient: the storage reference must also be
    durable and bound to this payment. This only enables *manual* admin review.
    """
    if not isinstance(payment, dict):
        return False
    if payment.get("notes") == "proof_received_admin_notified":
        return True
    if payment.get("notes") != "proof_received_web":
        return False
    try:
        return (bool(str(payment.get("proof_telegram_file_id") or "").strip())
                and int(payment.get("proof_telegram_message_id") or 0) > 0
                and bool(payment.get("proof_received_at")))
    except (TypeError, ValueError):
        return False



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
        caption = ("🏆 <b>RAKAN PEMBANGUN EARLY BIRD CIKGULAJU — RM20</b>\n\n"
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
        # Rakan Pembangun is independent of subscription expiry or subscription API failures.
        if has_pioneer(sb, cid):
            return {"active": True, "status": "pioneer", "access_start": None,
                    "access_until": None, "days_left": None,
                    "plan_code": "PIONEER_LIFETIME"}
        return original_access(cid)

    def menu(cid, show_persistent=False):
        # The main menu already has a 'Jadi Rakan Pembangun' button.
        # Show Rakan Pembangun price and benefits only when that button is selected.
        return original_menu(cid, show_persistent=show_persistent)

    def admin_pioneer_status(user_id):
        """Reusable status for the existing admin user-detail view."""
        try:
            active = has_pioneer(sb, user_id)
            count, remaining = pioneer_availability(sb)
            return ("🏆 Rakan Pembangun: " + ("AKTIF (seumur hidup)" if active else "TIDAK AKTIF")
                    + f"\n📊 {pioneer_percentage(count)} telah menyertai")
        except Exception:
            return "🏆 Rakan Pembangun: Tidak dapat disemak"

    def admin_user_card(cid, target):
        # Preserve existing admin card and append a separate, verified status.
        result = original_user_card(cid, target)
        if ns["_is_admin"](cid):
            buttons = [[{"text": "👥 Senarai Pengguna", "callback_data": "admin_list|all|0"}]]
            if has_pioneer(sb, target):
                buttons.insert(0, [{"text": "🛑 Batalkan Status Rakan Pembangun", "callback_data": f"pioneer_revoke_ask|{target}"}])
            send(cid, f"👤 ID: <code>{target}</code>\\n" + admin_pioneer_status(target), buttons)
        return result

    def admin_card(cid, request_id):
        if not ns["_is_admin"](cid):
            return send(cid, "⛔ Admin sahaja.")
        req = ns["_payment_request"](request_id)
        if req and float(req["amount"]) in (10.0, 20.0) and req["status"] == "pending":
            uid = int(req["chat_id"])
            proof_received = _has_recorded_payment_proof(req)
            status = ("✅ Resit sudah direkodkan"
                      if proof_received else "⚠️ Resit belum direkodkan")
            buttons = [
                [{"text": "👤 Semak ID Pelanggan", "callback_data": f"admin_user|{uid}"}],
            ]
            if proof_received:
                buttons.append([{"text": "✅ Sahkan Rakan Pembangun",
                                 "callback_data": f"admin_approve|{request_id}|{uid}"}])
            buttons.extend([
                [{"text": "🔄 Muat Semula Kad Permohonan",
                  "callback_data": f"pioneer_review|{request_id}"}],
                [{"text": "❌ Tolak", "callback_data": f"admin_reject|{request_id}"}],
                [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}],
            ])
            return send(cid, "🏆 <b>PENGESAHAN RAKAN PEMBANGUN</b>\n"
                        f"ID permohonan: <code>{request_id}</code>\n"
                        f"ID pelanggan Telegram: <code>{uid}</code>\n"
                        f"Jumlah: RM{float(req['amount']):.2f}\n{status}\n\n"
                        "Sahkan ID pelanggan dan transaksi TNG Merchant sebelum lulus. "
                        "Jangan minta pelanggan bayar semula.", buttons)
        return original_card(cid, request_id)

    def quota_text():
        count, remaining = pioneer_availability(sb)
        return f"📊 {pioneer_percentage(count)} telah menyertai"

    def review_durable_rakan(cid, req, decision):
        try:
            result = ns["_review_rakan_payment"](req, cid, decision)
        except Exception as exc:
            print("RAKAN PAYMENT REVIEW unavailable:", type(exc).__name__, flush=True)
            return send(cid, "⚠️ Semakan bayaran belum selesai. Muat semula kad permohonan.")
        if not isinstance(result, dict) or result.get("status") != decision:
            if isinstance(result, dict) and result.get("error") == "already_active":
                return send(cid, "ℹ️ Rakan Pembangun sudah aktif. Semak transaksi asal sebelum memutuskan bayaran ini.")
            return send(cid, "⚠️ Bayaran sudah disemak atau resit berubah. Muat semula kad permohonan.")
        if decision == "rejected":
            send(req["chat_id"], "❌ Bayaran Rakan Pembangun belum disahkan. Semak transaksi dan hantar semula resit sedia ada.")
            return send(cid, f"Bayaran #{req['id']} ditolak.")
        send(cid, f"✅ Rakan Pembangun diaktifkan untuk {req['chat_id']}.")
        return send(req["chat_id"], "🏆 <b>Status Rakan Pembangun Anda: AKTIF</b>",
                    [[{"text": "🏠 Kembali ke Menu Utama", "callback_data": "home"}]])

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
                    return send(cid, "ℹ️ Rakan Pembangun tidak aktif.")
                return send(cid, f"⚠️ Sahkan pembatalan Rakan Pembangun untuk ID <code>{uid}</code>. Rekod pembayaran tidak dipadam.",
                            [[{"text": "🛑 SAHKAN PEMBATALAN", "callback_data": f"pioneer_revoke_confirm|{uid}"}],
                             [{"text": "↩️ Kembali", "callback_data": f"admin_user|{uid}"}]])
            if not has_pioneer(sb, uid):
                return send(cid, "ℹ️ Rakan Pembangun sudah tidak aktif.")
            try:
                sb("POST", "rpc/revoke_pioneer_entitlement", json={"p_telegram_user_id": uid, "p_revoked_by": int(cid)})
            except Exception:
                return send(cid, "⚠️ Pembatalan gagal. Status tidak diubah.")
            return send(cid, f"✅ Rakan Pembangun ID <code>{uid}</code> telah dibatalkan.",
                        [[{"text": "👤 Lihat Pengguna", "callback_data": f"admin_user|{uid}"}]])
        if d == "pioneer_join":
            if has_pioneer(sb, cid):
                try:
                    progress = quota_text()
                except Exception:
                    progress = "📊 Peratus penyertaan belum dapat dipaparkan."
                return send(cid, "🏆 <b>Status Rakan Pembangun anda: AKTIF</b>\n\n" + progress + "\n\n♾️ Akses sepanjang CikguLaju AI beroperasi.",
                            [[{"text": "🏠 Menu Utama", "callback_data": "home"}]])
            count, remaining = pioneer_availability(sb)
            if remaining == 0:
                return send(cid, "⛔ <b>Rakan Pembangun sudah penuh.</b>\n"
                            "Pendaftaran baharu telah ditutup.",
                            [[{"text":"🏠 Menu Utama","callback_data":"home"}]])
            return send(cid, "🏆 <b>RAKAN PEMBANGUN EARLY BIRD CIKGULAJU — RM20 SEKALI SAHAJA</b>\n"
                        "<b>Kelebihan Rakan Pembangun:</b>\n✅ Bayar RM20 sekali sahaja.\n✅ Guna CikguLaju AI tanpa perlu bayar langganan bulanan atau tahunan.\n♾️ Akses Rakan Pembangun seumur hidup.\n👩‍🏫 Sediakan RPH untuk pelbagai subjek.\n\n" + quota_text() + "\n"
                        "Status Rakan Pembangun kekal walaupun sistem dikemas kini.",
                        [[{"text": "💳 Papar QR & Hantar Resit", "callback_data": "pioneer_pay"}],
                         [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        if d == "pioneer_receipt":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Rakan Pembangun anda sudah aktif.")
            pending = ns["_latest_pending_payment"](cid)
            if pending and float(pending.get("amount", 0)) not in (10.0, 20.0):
                return send(cid, "⚠️ Ada permohonan bayaran lain yang masih menunggu semakan.")
            if pending and pending.get("notes") == "proof_received_admin_notified":
                return send(cid, f"⌛ Resit Rakan Pembangun RM{float(pending['amount']):.2f} sudah diterima. Tunggu semakan admin; tidak perlu hantar semula.")
            if not pending and pioneer_availability(sb)[1] == 0:
                return send(cid, "⛔ Kuota Rakan Pembangun sudah penuh. "
                            "Permohonan baharu dan muat naik resit baharu ditutup.")
            # Selecting upload is a draft intent, NOT a payment request.
            draft = state.setdefault(cid, {})
            draft["waiting"] = "payment_proof"
            draft["payment_amount"] = float(pending["amount"]) if pending else 20.0
            return send(cid, "📎 Sila hantar gambar atau PDF resit bayaran RM20. "
                        "Permohonan hanya direkod selepas resit dihantar.")
        if d == "pioneer_pay":
            if has_pioneer(sb, cid):
                return send(cid, "🏆 Status Rakan Pembangun anda sudah aktif.")
            if pioneer_availability(sb)[1] == 0:
                return send(cid, "⛔ Pendaftaran Rakan Pembangun Early Bird sudah penuh.")
            pending = ns["_latest_pending_payment"](cid)
            if pending and float(pending["amount"]) not in (10.0, 20.0):
                return send(cid, "⚠️ Ada permohonan pembayaran lain yang belum selesai. "
                            "Sila selesaikan permohonan tersebut dahulu.")
            if pending and pending.get("notes") == "proof_received_admin_notified":
                return send(cid, f"⌛ Resit Rakan Pembangun RM{float(pending['amount']):.2f} sudah diterima dan menunggu semakan admin. Tidak perlu hantar semula.")
            # Show QR and remember a transient intent only. Do not insert a
            # pending record into SQLite/Supabase before a receipt is uploaded.
            draft = state.setdefault(cid, {})
            draft["waiting"] = "payment_proof"
            draft["payment_amount"] = float(pending["amount"]) if pending else 20.0
            # Existing QR bytes are reused, not copied into a new asset.
            return send_pioneer_qr(cid, pending["id"] if pending else None)
        if str(d).startswith("pioneer_review|"):
            # Read the *current* local request only. This is an admin-only view;
            # it never approves, creates or transfers payments.
            if not ns["_is_admin"](cid):
                return send(cid, "⛔ Admin sahaja.")
            parts = str(d).split("|")
            if len(parts) != 2 or not parts[1].isascii() or not parts[1].isdecimal():
                return send(cid, "⚠️ ID permohonan tidak sah.")
            rid = int(parts[1])
            if rid <= 0 or not ns["_payment_request"](rid):
                return send(cid, f"⚠️ Permohonan #{rid} tidak ditemui pada rekod semasa. "
                            "Semak panel admin. Jangan minta pelanggan bayar semula.",
                            [[{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]])
            return ns["_admin_pending_card"](cid, rid)
        if str(d).startswith("admin_reject|") and ns.get("_review_rakan_payment"):
            if not ns["_is_admin"](cid):
                return send(cid, "⛔ Admin sahaja.")
            _, _, raw_id = str(d).partition("|")
            if not raw_id.isascii() or not raw_id.isdecimal() or not 0 < int(raw_id) < 10**18:
                return send(cid, "⚠️ ID bayaran tidak sah.")
            req = ns["_payment_request"](int(raw_id))
            if req and float(req["amount"]) in (10.0, 20.0):
                return review_durable_rakan(cid, req, "rejected")
        if str(d).startswith("admin_approve|"):
            if not ns["_is_admin"](cid):
                return send(cid, "⛔ Admin sahaja.")
            try:
                parts = str(d).split("|")
                if len(parts) not in (2, 3):
                    raise ValueError("Invalid approval callback")
                rid = int(parts[1])
                expected_uid = int(parts[2]) if len(parts) == 3 else None
                if rid <= 0 or (expected_uid is not None and expected_uid <= 0):
                    raise ValueError("Invalid payment or user")
            except (ValueError, IndexError):
                return send(cid, "⚠️ Butang pengesahan tidak sah. Buka semula kad dalam panel admin.",
                            [[{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]])
            req = ns["_payment_request"](rid)
            if not req:
                return send(cid, f"⚠️ Permohonan #{rid} tidak ditemui pada rekod semasa. "
                            "Semak panel admin. Jangan minta pelanggan bayar semula.",
                            [[{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]])
            if float(req["amount"]) in (10.0, 20.0):
                if expected_uid is None:
                    # Legacy 'admin_approve|id' has no payer binding.
                    # Show the current card and a fresh ID-bound approval button.
                    # Never silently grant from this stale button.
                    return ns["_admin_pending_card"](cid, rid)
                current_uid = int(req["chat_id"])
                if current_uid != expected_uid:
                    # IDs can be reused when SQLite restarts. Show both owners
                    # but do not approve or automatically re-bind this payment.
                    return send(cid,
                        "⚠️ <b>ID PELANGGAN TIDAK SEPADAN</b>\n"
                        f"ID pada butang lama: <code>{expected_uid}</code>\n"
                        f"ID permohonan #{rid} sekarang: <code>{current_uid}</code>\n\n"
                        "Tiada bayaran diluluskan. Semak pemilik dan resit asal "
                        "dalam panel admin. Jangan minta bayaran semula.",
                        [[{"text": "👤 Semak Pelanggan Asal",
                           "callback_data": f"admin_user|{expected_uid}"}],
                         [{"text": "👤 Semak Pelanggan Semasa",
                           "callback_data": f"admin_user|{current_uid}"}],
                         [{"text": "📄 Buka Kad Permohonan Semasa",
                           "callback_data": f"pioneer_review|{rid}"}],
                         [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]])
                if ns.get("_review_rakan_payment"):
                    return review_durable_rakan(cid, req, "approved")
                if has_pioneer(sb, int(req["chat_id"])):
                    # A manually verified entitlement may already be active even
                    # when the local SQLite payment is still pending. Reconcile
                    # only this exact user, never transfer another user's grant.
                    ns["_mark_payment_request"](rid, "approved", cid,
                        "Reconciled: Rakan Pembangun lifetime already active in Supabase")
                    return send(cid,
                        f"✅ Rakan Pembangun pengguna {req['chat_id']} sudah AKTIF.\\n"
                        "Rekod permohonan tempatan diselaraskan; tiada bayaran semula diperlukan.")
                if req["status"] != "pending":
                    return ns["_admin_pending_card"](cid, rid)
                if not _has_recorded_payment_proof(req):
                    return send(cid, "⚠️ Resit belum direkodkan. Jangan aktifkan Rakan Pembangun.")
                # Admin has manually verified the bank transaction before clicking Approve.
                try:
                    # Reconcile only an active entitlement tied to this exact payment.
                    uid = int(req["chat_id"])
                    # Local SQLite payment IDs may restart after deployment.
                    # Scope new references to both user and request; preserve old
                    # references for existing entitlements without modifying them.
                    # A random immutable reference prevents collisions even if the
                    # local SQLite payment counter restarts for the same user.
                    import uuid
                    reference = f"pioneer-payment:{uid}:{uuid.uuid4().hex}"
                    existing = sb("GET", f"pioneer_entitlements?telegram_user_id=eq.{uid}&select=entitlement,payment_reference,revoked_at") or []
                    already_granted = any(
                        row.get("entitlement") == "PIONEER_LIFETIME"
                        and row.get("revoked_at") is None for row in existing
                    )
                    if not already_granted:
                        by_reference = sb("GET",
                            f"pioneer_entitlements?payment_reference=eq.{reference}&select=telegram_user_id,revoked_at") or []
                        if by_reference:
                            return send(cid,
                                f"⚠️ Rujukan bayaran #{rid} sudah digunakan.\\n"
                                "Jangan aktifkan atau minta bayaran semula sebelum audit.")
                        revoked = any(
                            row.get("entitlement") == "PIONEER_LIFETIME"
                            and row.get("revoked_at") is not None
                            for row in existing
                        )
                        if revoked:
                            # An old primary-key row still exists after an
                            # admin revokes lifetime access. Never call the
                            # first-time INSERT RPC for a revoked account.
                            # The reactivation RPC checks the exact Pending
                            # owner, amount and proof, and archives the old
                            # entitlement before restoring this row atomically.
                            result = reactivate_revoked_pioneer(
                                sb, uid, reference, cid, rid, verified=True)
                            if (not isinstance(result, dict)
                                    or result.get("approved") is not True
                                    or result.get("reactivated") is not True):
                                raise RuntimeError("Supabase did not confirm reactivation")
                        else:
                            grant_pioneer(sb, uid, reference, cid, verified=True)
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
                        reason = 'Fungsi kelulusan Rakan Pembangun tidak ditemui di Supabase.'
                    elif '409' in detail or 'already exists' in detail.lower() or 'duplicate' in detail.lower():
                        reason = 'Rekod Rakan Pembangun mungkin sudah wujud. Semak status sebelum cuba lagi.'
                    elif 'quota full' in detail.lower():
                        reason = 'Kuota Rakan Pembangun telah penuh.'
                    elif 'not configured' in detail.lower():
                        reason = 'Konfigurasi Supabase belum lengkap.'
                    else:
                        reason = f'Ralat sambungan atau pangkalan data ({type(exc).__name__}).'
                    return send(cid, f"⚠️ Rakan Pembangun belum diaktifkan untuk Payment ID #{rid}.\\n"
                                f"Sebab: {reason}\\n"
                                "Bayaran masih menunggu pengesahan. Jangan minta pengguna bayar semula.")
                ns["_mark_payment_request"](rid, "approved", cid, f"Rakan Pembangun RM{float(req['amount']):.2f} manually verified by admin")
                send(cid, f"✅ Rakan Pembangun diaktifkan untuk {req['chat_id']}.")
                return send(req["chat_id"], "🏆 <b>Status Rakan Pembangun Anda: AKTIF</b>\n\nAnda menikmati akses tanpa bayaran langganan bulanan atau tahunan sepanjang CikguLaju AI beroperasi.",
                            [[{"text": "🏠 Kembali ke Menu Utama", "callback_data": "home"}]])
        return original_callback(cid, d)

    ns["_access_info"] = access_info
    ns["_admin_pending_card"] = admin_card
    ns["_admin_user_card"] = admin_user_card
    ns["callback"] = callback
    ns["menu"] = menu
    ns["_admin_pioneer_status"] = admin_pioneer_status
    # Admin-only reconciliation for legacy bank-verified RM10 payments whose local
    # SQLite pending rows disappeared after a Render deploy. No auto-approval.
    # Install BEFORE private referrals so the outer webhook-secret guard remains.
    try:
        from pioneer_paid_recovery_telegram import install as _install_paid_recovery
        _install_paid_recovery(ns)
    except Exception as exc:
        print("PIONEER VERIFIED RECOVERY installer error:", type(exc).__name__, flush=True)
    # Hidden referral points is OFF by default; it only adds isolated wrappers.
    try:
        from referral_points_telegram import install as _install_private_referral
        _install_private_referral(ns)
    except Exception as exc:
        print("PRIVATE REFERRAL installer error:", type(exc).__name__, flush=True)
    return True
