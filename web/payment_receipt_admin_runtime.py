"""Read-only Telegram receipt preview for admin, backed by Supabase."""
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

    def card(cid, rid):
        if not is_admin(cid):
            return send(cid, "⛔ Admin sahaja.")
        try:
            req = lookup(rid)
        except Exception:
            return send(cid, "⚠️ Supabase tidak dapat membaca rekod bayaran.")
        if not req:
            return send(cid, "⚠️ Rekod bayaran tidak ditemui.")
        result = old_card(cid, rid)
        proof = bool(req.get("proof_telegram_file_id") or req.get("proof_telegram_message_id"))
        buttons = ([ [{"text":"🧾 Papar Resit","callback_data":f"admin_receipt|{rid}"}] ]
                   if proof else [])
        buttons.append([{"text":"🔄 Muat Semula","callback_data":f"admin_pending|{rid}"}])
        message = ("🧾 <b>REKOD RESIT</b>\n"
            f"ID permohonan: #{rid}\n"
            f"ID pelanggan: <code>{req['chat_id']}</code>\n"
            "Permohonan dibuat: " + malaysia_time(req.get("submitted_at")) + "\n"
            "Resit dihantar: " + malaysia_time(req.get("proof_received_at")) + "\n"
            + ("✅ Fail resit boleh dibuka." if proof else
               "⚠️ Tiada fail resit tersimpan. Semak chat asal; "
               "minta hantar SEMULA resit sedia ada, bukan bayar lagi."))
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
