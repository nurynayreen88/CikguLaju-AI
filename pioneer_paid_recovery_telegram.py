"""Admin-only recovery for a verified RM10 Rakan Pembangun bank transaction.

This deliberately does NOT recreate a missing SQLite payment request or trust
a legacy payment ID. It requires the admin to independently verify the RM10
transaction in TNG Merchant and enter its actual unique transaction reference.

The persistent entitlement RPC is already used by standard Pioneer approvals.
The same normalized merchant reference always hashes to the same global key,
so the Supabase uniqueness constraint stops a transaction reused across users.
No raw bank reference is sent to Supabase or printed in logs.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time
from urllib.parse import quote

from pioneer_supabase import grant_pioneer, has_pioneer

_TTL_SECONDS = 600
_PREFIX = "pioneer_paid_recover"
_INPUT = re.compile(r"^/tngref(?:@\w+)?\s+(.{6,150})$", re.I)
_POS_ID = re.compile(r"^[1-9][0-9]{0,15}$")


def _merchant_key(raw):
    """Canonicalize a TNG Merchant transaction ID for cross-user deduplication."""
    ref = re.sub(r"[^A-Z0-9]", "", str(raw).strip().upper())
    if not (6 <= len(ref) <= 96):
        return None
    if len(set(ref)) <= 1:  # reject all-zeros / dummy placeholder
        return None
    return "tng-merchant-recovery:" + hashlib.sha256(("TNG-MERCHANT|" + ref).encode()).hexdigest()


def install(ns):
    """Install after pioneer_telegram but before optional secure referral wrapper."""
    secret = os.environ.get("CIKGULAJU_TELEGRAM_WEBHOOK_SECRET", "")
    if not (16 <= len(secret) <= 256) or re.fullmatch(r"[A-Za-z0-9_-]+", secret) is None:
        # Without a valid secret, never intercept Telegram messages or expose
        # a recovery button. The normal approval workflow remains untouched.
        return False

    app = ns.get("app")
    request = ns.get("request")
    previous_callback = ns.get("callback")
    previous_card = ns.get("_admin_user_card")
    send = ns.get("send")
    sb = ns.get("_sb_request")
    states = ns.get("state")
    is_admin = ns.get("_is_admin")
    jsonify = ns.get("jsonify")
    if (app is None or "webhook" not in getattr(app, "view_functions", {})
            or request is None or not isinstance(states, dict)
            or not all(callable(fn) for fn in (previous_callback, previous_card,
                                               send, sb, is_admin, jsonify))):
        return False
    if ns.get("CIKGULAJU_PIONEER_RECOVERY_INSTALLED"):
        return True
    previous_webhook = app.view_functions["webhook"]

    def registered(uid):
        rows = sb("GET", f"cikgulaju_users?telegram_user_id=eq.{uid}"
                          "&select=telegram_user_id&limit=1") or []
        return isinstance(rows, list) and any(int(x["telegram_user_id"]) == uid
                                              for x in rows)

    def status(uid):
        """Fail closed if the database is inaccessible."""
        if not registered(uid):
            return "not_registered"
        return "active" if has_pioneer(sb, uid) else "inactive"

    def old_button(cid, uid):
        return [[{"text": "👤 Lihat Pengguna",
                  "callback_data": f"admin_user|{uid}"}],
                [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]]

    def admin_user_card(cid, target):
        result = previous_card(cid, target)
        if not is_admin(cid) or not _POS_ID.fullmatch(str(target)):
            return result
        uid = int(target)
        try:
            st = status(uid)
            if st == "inactive":
                send(cid, "💳 <b>PEMULIHAN BAYARAN LAMA</b>\n"
                     f"ID pelanggan: <code>{uid}</code>\n"
                     "Hanya gunakan jika resit RM10 telah diterima dahulu, "
                     "tetapi rekod pending hilang selepas deploy.\n"
                     "Semak transaksi sebenar dalam TNG Merchant.",
                     [[{"text": "🧾 Pulihkan Bayaran RM10",
                        "callback_data": f"{_PREFIX}_ask|{uid}"}]])
        except Exception as exc:
            print("PIONEER RECOVERY CARD CHECK FAILED:", type(exc).__name__, flush=True)
        return result

    def callback(cid, data):
        raw = str(data or "")
        if not raw.startswith(_PREFIX + "_"):
            return previous_callback(cid, data)
        if not is_admin(cid):
            return send(cid, "⛔ Admin sahaja.")
        parts = raw.split("|")
        action = parts[0]
        if (action not in (_PREFIX + "_ask", _PREFIX + "_confirm", _PREFIX + "_cancel")
                or len(parts) != (3 if action == _PREFIX + "_confirm" else 2)
                or not _POS_ID.fullmatch(parts[1])):
            return send(cid, "⚠️ Butang pemulihan tidak sah. Buka semula profil pengguna.")
        uid = int(parts[1])
        admin_state = states.setdefault(int(cid), {})
        pending = admin_state.get("pioneer_paid_recovery")

        if action == _PREFIX + "_cancel":
            if isinstance(pending, dict) and pending.get("uid") == uid:
                admin_state.pop("pioneer_paid_recovery", None)
            return send(cid, "Pemulihan dibatalkan. Tiada rekod bayaran atau akses diubah.",
                        old_button(cid, uid))

        if action == _PREFIX + "_ask":
            try:
                st = status(uid)
            except Exception as exc:
                print("PIONEER RECOVERY LOOKUP FAILED:", type(exc).__name__, flush=True)
                return send(cid, "⚠️ Status akaun belum dapat disemak. Tiada kelulusan dibuat.")
            if st == "active":
                return send(cid, "✅ Pengguna ini sudah mempunyai akses Rakan Pembangun. "
                            "Jangan sahkan atau caj sekali lagi.", old_button(cid, uid))
            if st != "inactive":
                return send(cid, "⚠️ ID ini tiada dalam pangkalan data pengguna. "
                            "Semak ID pelanggan dahulu; jangan minta bayaran semula.")
            admin_state["pioneer_paid_recovery"] = {
                "uid": uid, "started": time.time(), "stage": "await_ref",
            }
            return send(
                cid, "🧾 <b>PULIHKAN BAYARAN RAKAN PEMBANGUN</b>\n\n"
                f"ID pelanggan: <code>{uid}</code>\n"
                "1. Buka resit asal dalam Telegram admin.\n"
                "2. Semak di TNG Merchant: bayaran benar-benar BERJAYA, "
                "RM10, belum digunakan untuk pelanggan lain.\n"
                "3. Taip mesej berikut dalam chat bot ini:\n"
                "<code>/tngref NOMBOR_RUJUKAN_TRANSAKSI</code>\n\n"
                "Gunakan rujukan transaksi TNG sebenar, bukan Payment ID bot "
                "#1 atau #2. Proses luput selepas 10 minit. Jangan minta bayar lagi.",
                [[{"text": "❌ Batal Pemulihan",
                   "callback_data": f"{_PREFIX}_cancel|{uid}"}]],
            )

        # Final step: token bound to admin + user + normalized bank reference;
        # token expires, is consumed before an attempted grant and cannot replay.
        if not re.fullmatch(r"[a-f0-9]{16}", parts[2]):
            return send(cid, "⚠️ Butang pengesahan tidak sah.")
        if (not isinstance(pending, dict) or pending.get("uid") != uid
                or pending.get("stage") != "confirm"
                or not hmac.compare_digest(str(pending.get("token", "")), parts[2])
                or time.time() - float(pending.get("started", 0)) > _TTL_SECONDS):
            return send(cid, "⚠️ Pengesahan tamat atau butang lama. Buka semula "
                        "profil pengguna dan semak transaksi sekali lagi.")
        admin_state.pop("pioneer_paid_recovery", None)
        reference = pending.get("merchant_key")
        if not isinstance(reference, str) or not reference.startswith("tng-merchant-recovery:"):
            return send(cid, "⚠️ Rujukan TNG tidak sah. Tiada kelulusan dibuat.")

        try:
            st = status(uid)
            if st == "active":
                return send(cid, "✅ Akaun pengguna sudah aktif; tiada grant kedua.",
                            old_button(cid, uid))
            if st != "inactive":
                return send(cid, "⚠️ Akaun pengguna tidak ditemui. Tiada kelulusan dibuat.")
            # This read is advisory only; unique DB constraint is authoritative.
            # Do not accept a ref that is already used by a different customer.
            other = sb("GET", "pioneer_entitlements?payment_reference=eq."
                       + quote(reference, safe="")
                       + "&select=telegram_user_id&limit=1") or []
            if other:
                return send(cid, "⛔ Rujukan TNG ini telah digunakan untuk "
                            "permohonan lain. Tiada kelulusan dibuat.")
            reply = grant_pioneer(sb, uid, reference, int(cid), verified=True)
            if isinstance(reply, dict) and reply.get("approved") is not True:
                raise RuntimeError("Entitlement RPC did not return an approved status")
            if not has_pioneer(sb, uid):
                raise RuntimeError("Entitlement not visible after RPC")
        except Exception as exc:
            print("PIONEER RECOVERY GRANT ERROR:", type(exc).__name__, flush=True)
            return send(
                cid, "⚠️ Kelulusan belum dapat disahkan di Supabase. "
                     "Semak status pengguna dahulu, jangan ulang transaksi "
                     "atau minta pelanggan bayar semula.",
                old_button(cid, uid),
            )
        send(cid, f"✅ <b>RAKAN PEMBANGUN AKTIF</b>\n"
             f"ID pelanggan: <code>{uid}</code>\n"
             "Bayaran RM10 asal telah diselaraskan di Supabase; "
             "tiada bayaran semula dikenakan.",
             old_button(cid, uid))
        try:
            send(uid, "🏆 <b>Rakan Pembangun anda sudah AKTIF</b>\n"
                 "Akses sepanjang CikguLaju AI beroperasi telah diaktifkan. "
                 "Tiada bayaran tambahan diperlukan.",
                 [[{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        except Exception as exc:
            print("PIONEER RECOVERY USER NOTICE FAILED:", type(exc).__name__, flush=True)
        return True

    def webhook():
        # Never bypass the existing Telegram webhook-secret protection.
        token = str(request.headers.get("X-Telegram-Bot-Api-Secret-Token", "") or "")
        if not hmac.compare_digest(token, secret):
            return previous_webhook()
        update = request.get_json(silent=True) or {}
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        sender = message.get("from") or {}
        chat_id = chat.get("id")
        if (str(chat.get("type")) != "private" or str(chat_id) != str(sender.get("id"))
                or not str(chat_id).isdigit() or not is_admin(chat_id)):
            return previous_webhook()
        raw = str(message.get("text") or "").strip()
        match = _INPUT.fullmatch(raw)
        if not match:
            return previous_webhook()
        admin_state = states.get(int(chat_id), {})
        pending = admin_state.get("pioneer_paid_recovery")
        if (not isinstance(pending, dict) or pending.get("stage") != "await_ref"
                or time.time() - float(pending.get("started", 0)) > _TTL_SECONDS):
            admin_state.pop("pioneer_paid_recovery", None)
            send(chat_id, "⚠️ Tiada pemulihan aktif atau tempoh sudah tamat. "
                 "Buka semula profil pengguna di Panel Admin.")
            return jsonify({"ok": True})
        key = _merchant_key(match.group(1))
        if not key:
            send(chat_id, "⚠️ Nombor rujukan TNG tidak sah. Gunakan nombor sebenar "
                 "daripada TNG Merchant, bukan nombor Payment ID bot.")
            return jsonify({"ok": True})
        uid = pending["uid"]
        nonce = secrets.token_hex(8)
        normalized = re.sub(r"[^A-Z0-9]", "", match.group(1).strip().upper())
        pending.update({"merchant_key": key, "reference_suffix": normalized[-4:],
                        "token": nonce, "stage": "confirm"})
        send(chat_id, "⚠️ <b>PENGESAHAN AKHIR PEMULIHAN</b>\n"
             f"ID pelanggan: <code>{uid}</code>\n"
             "Pakej: Rakan Pembangun RM10\n"
             f"Rujukan TNG: diterima (4 aksara akhir: <code>{normalized[-4:]}</code>)\n\n"
             "Tekan SAHKAN hanya selepas anda sendiri mengesahkan transaksi "
             "RM10 BERJAYA dalam TNG Merchant, tidak digunakan sebelum ini, "
             "dan ID pelanggan betul. Tiada bayaran semula diperlukan.",
             [[{"text": "✅ Saya Sahkan Transaksi TNG RM10",
                "callback_data": f"{_PREFIX}_confirm|{uid}|{nonce}"}],
              [{"text": "❌ Batal",
                "callback_data": f"{_PREFIX}_cancel|{uid}"}]])
        return jsonify({"ok": True})

    # The existing private-referral wrapper is installed afterward and performs
    # its own webhook verification before forwarding to this inner view.
    ns["_admin_user_card"] = admin_user_card
    ns["callback"] = callback
    app.view_functions["webhook"] = webhook
    ns["CIKGULAJU_PIONEER_RECOVERY_INSTALLED"] = True
    return True
