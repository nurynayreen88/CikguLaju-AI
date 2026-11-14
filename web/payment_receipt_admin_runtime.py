"""Admin-only inline receipt and payment review; Supabase remains authoritative."""
from decimal import Decimal, InvalidOperation
from html import escape
import re
from datetime import datetime, timedelta, timezone

MYT = timezone(timedelta(hours=8))

def malaysia_time(value):
    if not value:
        return "Belum direkodkan"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(MYT).strftime("%d/%m/%Y %H:%M:%S") + " MYT"
    except (ValueError, TypeError, OverflowError):
        return "Masa tidak tersedia"


def install(rt):
    if getattr(rt, "_PAYMENT_RECEIPT_ADMIN_INSTALLED", False):
        return True
    old_card, old_callback = rt._admin_pending_card, rt.callback
    lookup, send, is_admin = rt._payment_request, rt.send, rt._is_admin

    def _pioneer_buttons(rid, uid, *, may_approve):
        # The approval callback binds BOTH the payment ID and the current
        # payer. Existing handler checks them again against current Supabase.
        buttons = []
        if may_approve:
            buttons.append([{"text": "✅ Sahkan Rakan Pembangun",
                             "callback_data": f"admin_approve|{rid}|{uid}"}])
        buttons.append([{"text": "❌ Tolak Bayaran",
                         "callback_data": f"admin_reject|{rid}"}])
        buttons.append([{"text": "🔄 Muat Semula", "callback_data": f"admin_pending|{rid}"},
                        {"text": "📋 Senarai Pending",
                         "callback_data": "admin_pending_all"}])
        return buttons

    def _payer_name(uid):
        # Display only; NEVER use profile names to bind approvals.
        try:
            rows = rt._sb_request(
                "GET", "cikgulaju_users?telegram_user_id=eq."
                + str(uid) + "&select=first_name,last_name,username")
            row = rows[0] if isinstance(rows, list) and rows else {}
            name = " ".join(str(row.get(field) or "").strip()
                            for field in ("first_name", "last_name")).strip()
            return escape(name[:120] or str(row.get("username") or "Pengguna")[:120])
        except (AttributeError, TypeError, ValueError, RuntimeError):
            return "Pengguna"

    def _telegram_proof_sent(response, *, copied=False, cid=None):
        try:
            if not response.ok:
                return False
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("ok") is not True:
                return False
            result = payload.get("result")
            if not isinstance(result, dict) or type(result.get("message_id")) is not int:
                return False
            if result["message_id"] < 1:
                return False
            return copied or (isinstance(result.get("chat"), dict)
                              and str(result["chat"].get("id")) == str(cid))
        except (ValueError, TypeError, AttributeError):
            return False

    def _pioneer_receipt_card(cid, rid, req):
        """One Telegram image/document with details + review buttons.

        No separate "Papar Resit" step. Failure to display proof must never
        result in an actionable Approve button, even when the row is Pending.
        """
        try:
            uid = int(req["chat_id"])
            if uid <= 0:
                raise ValueError("Invalid payer")
            amount = Decimal(str(req["amount"]))
            if amount not in (Decimal("10.00"), Decimal("20.00")):
                raise ValueError("Invalid plan")
            if int(req["id"]) != int(rid):
                raise ValueError("Payment ID changed")
        except (KeyError, TypeError, ValueError, InvalidOperation):
            return send(cid, "⚠️ ID permohonan atau pelanggan tidak sepadan. "
                        "Sila muat semula Panel Admin.",
                        [[{"text": "📋 Senarai Pending",
                           "callback_data": "admin_pending_all"}]])

        fid = str(req.get("proof_telegram_file_id") or "").strip()
        raw_mid = req.get("proof_telegram_message_id")
        mid = raw_mid if type(raw_mid) is int and raw_mid > 0 else None
        caption = (
            "🏆 <b>PENGESAHAN RAKAN PEMBANGUN</b>\n"
            f"👤 Nama: <b>{_payer_name(uid)}</b>\n"
            f"🆔 ID pelanggan: <code>{uid}</code>\n"
            f"🧾 Payment ID: <b>#{rid}</b>\n"
            "📦 Pakej: <b>Rakan Pembangun</b>\n"
            f"💰 Jumlah: <b>RM{amount:.2f}</b>\n"
            "📅 Permohonan: " + malaysia_time(req.get("submitted_at")) + "\n"
            "📎 Resit diterima: " + malaysia_time(req.get("proof_received_at")) + "\n"
            "⌛ Status: <b>PENDING</b>\n\n"
            "Semak resit dan transaksi sebenar sebelum sahkan."
        )
        # Telegram media captions are limited to 1024 characters.
        if len(caption) > 950:
            return send(cid, "⚠️ Maklumat pengesahan terlalu panjang.",
                        [[{"text": "🔄 Muat Semula",
                           "callback_data": f"admin_pending|{rid}"}]])
        if not fid and not mid:
            return send(
                cid, caption + "\n\n⚠️ Fail resit tidak tersimpan. "
                "Tidak boleh sahkan sehingga bukti boleh disemak.",
                _pioneer_buttons(rid, uid, may_approve=False))
        buttons = _pioneer_buttons(rid, uid, may_approve=True)
        markup = {"inline_keyboard": buttons}
        try:
            import requests
            if fid:
                photo = req.get("proof_mime_type") == "telegram/photo"
                endpoint = "sendPhoto" if photo else "sendDocument"
                field = "photo" if photo else "document"
                response = requests.post(
                    rt.API + "/" + endpoint,
                    json={"chat_id": str(cid), field: fid,
                          "caption": caption, "parse_mode": "HTML",
                          "reply_markup": markup},
                    timeout=20,
                )
                if _telegram_proof_sent(response, cid=cid):
                    return response
            # If file_id expired, Telegram may still be able to copy the
            # immutable original message by its saved owner and message ID.
            if mid:
                response = requests.post(
                    rt.API + "/copyMessage",
                    json={"chat_id": str(cid), "from_chat_id": str(uid),
                          "message_id": mid, "caption": caption,
                          "parse_mode": "HTML", "reply_markup": markup},
                    timeout=20,
                )
                if _telegram_proof_sent(response, copied=True):
                    return response
        except Exception as exc:
            print("ADMIN INLINE RECEIPT DELIVERY ERROR:",
                  type(exc).__name__, flush=True)
        # Do not show an approval button if the receipt couldn't be displayed.
        return send(cid, caption + "\n\n⚠️ Resit tidak dapat dipaparkan. "
                    "Tiada kelulusan dibuat; cuba muat semula.",
                    [[{"text": "🔄 Cuba Lagi",
                       "callback_data": f"admin_pending|{rid}"},
                      {"text": "📋 Pending", "callback_data": "admin_pending_all"}]])

    def card(cid, rid):
        if not is_admin(cid):
            return send(cid, "⛔ Admin sahaja.")
        try:
            rid = int(rid)
            if rid <= 0:
                raise ValueError("Invalid payment ID")
            req = lookup(rid)
        except (ValueError, TypeError):
            return send(cid, "⚠️ ID bayaran tidak sah.")
        except Exception:
            return send(cid, "⚠️ Supabase tidak dapat membaca rekod bayaran.")
        if not req:
            return send(cid, "⚠️ Rekod bayaran tidak ditemui.")
        try:
            is_rakan = (Decimal(str(req.get("amount"))) in (Decimal("10.00"), Decimal("20.00"))
                        and req.get("status") == "pending")
        except (InvalidOperation, TypeError, ValueError):
            is_rakan = False
        if is_rakan:
            return _pioneer_receipt_card(cid, rid, req)

        # Other plans / historical records retain their original review flow.
        result = old_card(cid, rid)
        proof = bool(req.get("proof_telegram_file_id") or
                     req.get("proof_telegram_message_id"))
        buttons = ([ [{"text":"🧾 Papar Resit",
                       "callback_data":f"admin_receipt|{rid}"}] ]
                   if proof else [])
        buttons.append([{"text":"🔄 Muat Semula",
                         "callback_data":f"admin_pending|{rid}"}])
        message = ("🧾 <b>REKOD RESIT</b>\n"
            f"ID permohonan: #{rid}\n"
            f"ID pelanggan: <code>{req['chat_id']}</code>\n"
            "Permohonan dibuat: " + malaysia_time(req.get("submitted_at")) + "\n"
            "Resit dihantar: " + malaysia_time(req.get("proof_received_at")) + "\n"
            + ("✅ Fail resit boleh dibuka." if proof else
               "⚠️ Tiada fail resit tersimpan. Semak chat asal; "
               "minta hantar SEMULA resit sedia ada, bukan bayar lagi.")
        )
        send(cid, message, buttons)
        return result

    def callback(cid, data):
        d = str(data or "")
        if not d.startswith("admin_receipt|"):
            return old_callback(cid, data)
        if not is_admin(cid):
            return send(cid, "⛔ Admin sahaja.")
        match = re.fullmatch(r"admin_receipt\|([1-9][0-9]{0,17})", d)
        if not match:
            return send(cid, "⚠️ ID resit tidak sah.")
        rid = int(match.group(1))
        try:
            req = lookup(rid)
        except Exception:
            return send(cid, "⚠️ Rekod resit tidak dapat dibaca.")
        if not req:
            return send(cid, "⚠️ Rekod resit tidak ditemui.")
        fid = str(req.get("proof_telegram_file_id") or "").strip()
        mid = req.get("proof_telegram_message_id")
        if not fid and not mid:
            return send(cid, "⚠️ Fail resit belum direkodkan. "
                        "Semak mesej asal; jangan bayar semula.")
        caption = (f"Resit #{rid} | ID {req['chat_id']} | "
                   + malaysia_time(req.get("proof_received_at")))
        try:
            import requests
            if fid:
                photo = req.get("proof_mime_type") == "telegram/photo"
                endpoint = "sendPhoto" if photo else "sendDocument"
                field = "photo" if photo else "document"
                r = requests.post(rt.API + "/" + endpoint,
                    json={"chat_id":str(cid), field:fid, "caption":caption},
                    timeout=20)
                if r.ok and r.json().get("ok") is True:
                    return r
            if mid and str(req.get("chat_id", "")).isdigit():
                r = requests.post(rt.API + "/copyMessage",
                    json={"chat_id":str(cid),"from_chat_id":str(req["chat_id"]),
                          "message_id":int(mid),"caption":caption},timeout=20)
                if r.ok and r.json().get("ok") is True:
                    return r
        except Exception as exc:
            print("RECEIPT ADMIN PREVIEW ERROR:", type(exc).__name__,flush=True)
        return send(cid, "⚠️ Telegram tidak dapat memaparkan resit tersimpan. "
                    "Semak mesej asal dalam chat admin; jangan bayar lagi.")

    rt._admin_pending_card = card
    rt.callback = callback
    rt._PAYMENT_RECEIPT_ADMIN_INSTALLED = True
    return True
