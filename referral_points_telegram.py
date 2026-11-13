"""Opt-in PRIVATE referral points for CikguLaju Telegram (no public menu).

Only install after the existing pioneer callback has been installed. This
feature is OFF by default; it requires an applied DB migration and configured
reward rules before being enabled. Existing payment/entitlement flows win.
"""
import os
import re
import hmac
import secrets
from urllib.parse import quote
from decimal import Decimal

_START = re.compile(r"^/start(?:@\w+)?\s+rp_([A-Za-z0-9_-]{16,48})$")
_OLD = re.compile(r"^/start(?:@\w+)?\s+ref_-?\d+$")
_ADD = re.compile(r"^/refadd\s+(\d+)$")
_DEL = re.compile(r"^/refdel\s+(\d+)$")


def format_points(value):
    return format(Decimal(str(value)).quantize(Decimal('0.01')).normalize(), 'f')


def enabled():
    return os.getenv("CIKGULAJU_REFERRAL_POINTS_ENABLED", "0").lower() in ("1", "true", "yes")


def is_private_message(message):
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    return (str(chat.get("type")) == "private"
            and str(chat.get("id")) == str(sender.get("id"))
            and str(chat.get("id", "")).isdigit())


def install(ns):
    """Install transparent, fail-closed wrappers; never change production unless opt-in."""
    if not enabled():
        return False
    secret = os.getenv("CIKGULAJU_TELEGRAM_WEBHOOK_SECRET", "")
    if len(secret) < 16 or len(secret) > 256 or re.fullmatch(r"[A-Za-z0-9_-]+", secret) is None:
        raise RuntimeError("Private referral requires a valid Telegram webhook secret")
    app = ns["app"]
    # Configure Telegram to transmit the header BEFORE installing the strict verifier.
    # When Telegram API is down, leave the existing webhook untouched and fail closed.
    api = str(ns.get("API") or "")
    callback_base = str(ns.get("WEBHOOK_URL") or "")
    if not api.startswith("https://") or not callback_base.startswith("https://"):
        raise RuntimeError("Bot API and WEBHOOK_URL must be configured for private referrals")
    import requests
    response = requests.post(api + "/setWebhook", json={
        "url": callback_base.rstrip("/") + "/webhook",
        "secret_token": secret
    }, timeout=15)
    status = response.json() if response.ok else {}
    if not response.ok or status.get("ok") is not True:
        raise RuntimeError("Telegram refused secure webhook registration")
    print("PRIVATE REFERRAL SECURE WEBHOOK CONFIGURED", flush=True)
    # Disable the old public /setup-webhook route while the private secret is in use.
    # Calling it would otherwise silently reset the webhook secret.
    if "setup_webhook" in app.view_functions:
        def _block_legacy_webhook_setup():
            return ns["jsonify"]({"ok": False, "error": "secure webhook managed at startup"}), 403
        app.view_functions["setup_webhook"] = _block_legacy_webhook_setup
    previous_webhook = app.view_functions["webhook"]
    previous_callback = ns["callback"]
    sb = ns["_sb_request"]
    send = ns["send"]

    def member(uid):
        rows = sb("GET", f"referral_members?referrer_user_id=eq.{int(uid)}"
                   "&select=referrer_user_id,referral_code,enabled") or []
        return rows[0] if rows else None

    def summary(uid):
        signups = sb("GET", f"referral_signups?referrer_user_id=eq.{int(uid)}"
                     "&select=referred_user_id") or []
        events = sb("GET", f"referral_point_events?referrer_user_id=eq.{int(uid)}"
                     "&select=points_delta") or []
        return len(signups), len(events), sum((Decimal(str(e["points_delta"])) for e in events), Decimal("0"))

    def link_for(uid, code):
        username = str(ns["_bot_username_v25267"]() or "").strip().lstrip("@")
        return f"https://t.me/{username}?start=rp_{code}" if username else ""

    def affiliate_open(uid):
        try:
            result = sb("POST", "rpc/affiliate_overview", json={"p_user": int(uid)})
            return isinstance(result, dict) and result.get("open") is True
        except Exception:
            return False

    def show_referral(uid):
        row = member(uid)
        open_program = affiliate_open(uid)
        web = "https://cikgulaju-web.onrender.com/?affiliate=1"
        if not row or row.get("enabled") is not True:
            if row is None and open_program:
                return send(uid, "🎁 Daftar affiliate dengan nombor telefon berdaftar TNG eWallet.",
                            [[{"text": "Sertai Affiliate", "url": web}]])
            return send(uid, "🔒 Program affiliate tidak tersedia untuk akaun ini.")
        link = link_for(uid, row["referral_code"])
        if not link:
            return send(uid, "⚠️ Pautan belum dapat dijana. Sila cuba lagi.")
        total, paid, points = summary(uid)
        share = ("https://t.me/share/url?url=" + quote(link, safe="")
                 + "&text=" + quote(
                     "Saya sedang menggunakan CikguLaju AI untuk membantu penyediaan RPH. Cuba pautan ini:",
                     safe=""
                 ))
        buttons = [
            [{"text": "📤 Kongsi Pautan", "url": share}],
            [{"text": "📋 Salin Pautan", "copy_text": {"text": link}}],
            [{"text": "🏠 Menu Utama", "callback_data": "home"}],
        ]
        if open_program:
            buttons.insert(2, [{"text": "💸 Claim Ganjaran", "url": web}])
        return send(uid,
            "🎁 <b>AFFILIATE SAYA</b>\n\n"
            f"🔗 <code>{link}</code>\n\n"
            f"👥 Rakan mendaftar: <b>{total}</b>\n"
            f"✅ Pembayaran layak: <b>{paid}</b>\n"
            f"⭐ Mata terkumpul: <b>{format_points(points)}</b>\n\n"
            "Ganjaran dikira selepas bayaran pertama disahkan. "
            + ("Tuntutan minimum 10 mata (RM10) melalui TNG eWallet." if open_program
               else "Mata dikumpul dahulu dan belum boleh ditebus."),
            buttons)

    def manage_member(admin, uid, allow):
        if not ns["_is_admin"](admin):
            return send(admin, "⛔ Admin sahaja.")
        if uid <= 0:
            return send(admin, "⚠️ ID pengguna tidak sah.")
        if not allow:
            current = member(uid)
            if not current:
                return send(admin, "ℹ️ Pengguna tiada dalam senarai referral.")
            sb("PATCH", f"referral_members?referrer_user_id=eq.{uid}",
               json={"enabled": False}, prefer="return=minimal")
            return send(admin, f"🔒 Referral untuk ID {uid} telah dinyahaktifkan.")
        users = sb("GET", f"cikgulaju_users?telegram_user_id=eq.{uid}"
                   "&select=telegram_user_id") or []
        if not users:
            return send(admin, "⚠️ ID ini belum berdaftar dalam akaun CikguLaju.")
        current = member(uid)
        if current:
            sb("PATCH", f"referral_members?referrer_user_id=eq.{uid}",
               json={"enabled": True}, prefer="return=minimal")
        else:
            sb("POST", "referral_members",
               json={"referrer_user_id":uid,
                     "referral_code":secrets.token_urlsafe(18),
                     "enabled":True}, prefer="return=minimal")
        send(admin, f"✅ Referral peribadi dibuka untuk ID {uid}.")
        try:
            return show_referral(uid)
        except Exception:
            return None

    def after_verified_approval(admin, d, before):
        """Observe only: never influence an existing successful payment."""
        if not before or before.get("status") != "pending":
            return
        after = ns["_payment_request"](before["id"])
        if not after or after.get("status") != "approved":
            return
        payer = int(after["chat_id"])
        try:
            if Decimal(str(after.get("amount", 0))) in (Decimal("10"), Decimal("20")):
                rows = sb("GET", f"pioneer_entitlements?telegram_user_id=eq.{payer}"
                          "&revoked_at=is.null"
                          "&select=payment_reference,entitlement") or []
                verified = next((x for x in rows
                                 if x.get("entitlement") == "PIONEER_LIFETIME"), None)
                kind = "pioneer"
                reference = verified.get("payment_reference") if verified else None
            else:
                reference = f"payment-request:{int(after['id'])}"
                qref = quote(reference, safe="")
                rows = sb("GET", f"subscription_payments?telegram_user_id=eq.{payer}"
                          f"&payment_reference=eq.{qref}&select=payment_reference,status") or []
                if not any(r.get("status") in ("paid", "approved") for r in rows):
                    return
                kind = "subscription"
            if not reference:
                return
            result = sb("POST", "rpc/referral_award_verified_payment", json={
                "p_payer_user_id": payer, "p_payment_kind": kind,
                "p_payment_reference": reference
            })
            award = result[0] if isinstance(result, list) and result else result or {}
            if award.get("awarded"):
                points = format_points(award["points"])
                send(admin, f"⭐ Referral: +{points} mata direkodkan "
                            f"untuk bayaran pengguna {payer}.")
                try:
                    refs = sb("GET", f"referral_signups?referred_user_id=eq.{payer}"
                              "&select=referrer_user_id") or []
                    if refs:
                        send(int(refs[0]["referrer_user_id"]),
                             f"🎉 Tahniah! +{points} mata referral telah direkodkan "
                             "selepas pembayaran rakan disahkan. "
                             "Tekan 🎁 Referral Saya pada menu untuk semak mata.")
                except Exception:
                    print("PRIVATE REFERRAL notification deferred", flush=True)
        except Exception as exc:
            # Payment has already succeeded. Never roll it back on referral failure.
            print("PRIVATE REFERRAL award error:", type(exc).__name__, flush=True)

    def callback(cid, d):
        if str(d) == "private_referral_home":
            try:
                return show_referral(cid)
            except Exception as exc:
                print("PRIVATE REFERRAL menu callback error:", type(exc).__name__, flush=True)
                return send(cid, "⚠️ Referral belum dapat dibuka. Cuba semula.")
        if str(d) == "referral_vip":
            # Close the old public registration-for-VIP rewards while this private
            # replacement is active. Historical awards are preserved.
            return send(cid, "ℹ️ Program referral VIP lama telah ditutup.")
        before = None
        if str(d).startswith("admin_approve|") and ns["_is_admin"](cid):
            try:
                rid = int(str(d).split("|")[1])
                before = ns["_payment_request"](rid)
            except (IndexError, ValueError):
                pass
        result = previous_callback(cid, d)
        if before:
            after_verified_approval(cid, d, before)
        return result

    def webhook():
        token = str(ns["request"].headers.get("X-Telegram-Bot-Api-Secret-Token", "") or "")
        if not hmac.compare_digest(token, secret):
            return ns["jsonify"]({"ok":False,"error":"unauthorized"}), 403
        update = ns["request"].get_json(silent=True) or {}
        msg = update.get("message") or {}
        if not is_private_message(msg):
            return previous_webhook()
        uid = int(msg["chat"]["id"])
        text = str(msg.get("text") or "").strip()
        if _OLD.fullmatch(text):
            # Do not enter the legacy 3-day VIP enrollment path.
            ns["_upsert_user"](msg.get("from") or {}, uid)
            send(uid, "ℹ️ Pautan referral VIP lama telah tamat. "
                      "Gunakan pautan jemputan program baharu.")
            ns["menu"](uid, show_persistent=True)
            return ns["jsonify"]({"ok":True,"legacy_referral_closed":True})
        m = _START.fullmatch(text)
        if m:
            # _upsert_user persists the Telegram profile first, but does NOT
            # create cikgulaju_users. The referral FK and new-user timestamp
            # require the existing trial-user initialization to run before the RPC.
            ns["_upsert_user"](msg.get("from") or {}, uid)
            try:
                ns["_ensure_trial_user"](uid)
                result = sb("POST", "rpc/referral_capture_signup", json={
                    "p_referred_user_id": uid, "p_referral_code": m.group(1)
                })
                capture = result[0] if isinstance(result, list) and result else result or {}
                if capture.get("captured") is True:
                    send(uid, "✅ Pendaftaran melalui pautan referral berjaya direkodkan. "
                              "Ganjaran untuk pemilik pautan hanya diberikan selepas "
                              "bayaran yang layak disahkan.")
                else:
                    reason = str(capture.get("reason") or "already_recorded")
                    # Never claim a successful referral for an existing account
                    # or a stale/invalid code. Report only a safe reason string.
                    print("PRIVATE REFERRAL signup not captured:",
                          reason[:48], flush=True)
                    send(uid, "ℹ️ Akaun ini tidak direkodkan sebagai pendaftaran "
                              "referral baharu. Pautan hanya layak untuk akaun "
                              "yang baru didaftarkan dan belum menggunakan pautan lain.")
            except Exception as exc:
                print("PRIVATE REFERRAL capture error:",
                      type(exc).__name__, flush=True)
                send(uid, "⚠️ Pendaftaran referral belum berjaya direkodkan. "
                          "Cuba buka semula pautan jemputan; "
                          "akaun CikguLaju masih boleh digunakan.")
            ns["menu"](uid, show_persistent=True)
            return ns["jsonify"]({"ok":True,"private_referral":True})
        if text == "/mata":
            try:
                show_referral(uid)
            except Exception as exc:
                print("PRIVATE REFERRAL summary error:", type(exc).__name__, flush=True)
                send(uid, "⚠️ Mata referral belum dapat disemak.")
            return ns["jsonify"]({"ok":True})
        m = _ADD.fullmatch(text)
        if m and ns["_is_admin"](uid):
            try:
                manage_member(uid, int(m.group(1)), True)
            except Exception as exc:
                print("PRIVATE REFERRAL enable error:", type(exc).__name__, flush=True)
                send(uid, "⚠️ Tidak dapat mengaktifkan referral. Semak database.")
            return ns["jsonify"]({"ok":True})
        m = _DEL.fullmatch(text)
        if m and ns["_is_admin"](uid):
            try:
                manage_member(uid, int(m.group(1)), False)
            except Exception as exc:
                print("PRIVATE REFERRAL disable error:", type(exc).__name__, flush=True)
                send(uid, "⚠️ Tidak dapat menyahaktifkan referral.")
            return ns["jsonify"]({"ok":True})
        return previous_webhook()

    ns["_private_referral_member"] = member
    ns["_affiliate_open"] = affiliate_open
    ns["callback"] = callback
    app.view_functions["webhook"] = webhook
    return True
