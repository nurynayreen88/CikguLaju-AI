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

_START = re.compile(r"^/start(?:@\\w+)?\\s+rp_([A-Za-z0-9_-]{16,48})$")
_OLD = re.compile(r"^/start(?:@\\w+)?\\s+ref_-?\\d+$")
_ADD = re.compile(r"^/refadd\\s+(\\d+)$")
_DEL = re.compile(r"^/refdel\\s+(\\d+)$")


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
    if len(secret) < 16:
        raise RuntimeError("Private referral requires a Telegram webhook secret")
    app = ns["app"]
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

    def show_referral(uid):
        row = member(uid)
        if not row or not row.get("enabled"):
            return send(uid, "🔒 Program referral tertutup tidak tersedia untuk akaun ini.")
        link = link_for(uid, row["referral_code"])
        if not link:
            return send(uid, "⚠️ Pautan belum dapat dijana. Sila cuba lagi.")
        total, paid, points = summary(uid)
        return send(uid,
            "🔒 <b>REFERRAL PERIBADI CIKGULAJU</b>\\n\\n"
            f"🔗 <code>{link}</code>\\n\\n"
            f"👥 Pendaftaran melalui pautan: <b>{total}</b>\\n"
            f"✅ Bayaran layak disahkan: <b>{paid}</b>\\n"
            f"⭐ Jumlah mata: <b>{format_points(points)}</b>\\n\\n"
            "Mata hanya diberikan selepas bayaran disahkan admin. "
            "Mata bukan kredit RPH dan tidak boleh ditebus sehingga program dibuka.")

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
            if float(after.get("amount", 0)) == 10.0:
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
                             "Taip /mata untuk semak jumlah terkini.")
                except Exception:
                    print("PRIVATE REFERRAL notification deferred", flush=True)
        except Exception as exc:
            # Payment has already succeeded. Never roll it back on referral failure.
            print("PRIVATE REFERRAL award error:", type(exc).__name__, flush=True)

    def callback(cid, d):
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
            ns["_upsert_user"](msg.get("from") or {}, uid)
            try:
                sb("POST", "rpc/referral_capture_signup", json={
                    "p_referred_user_id": uid, "p_referral_code": m.group(1)
                })
            except Exception as exc:
                print("PRIVATE REFERRAL capture error:", type(exc).__name__, flush=True)
                send(uid, "⚠️ Pautan referral belum dapat direkodkan. "
                          "Akaun CikguLaju masih boleh digunakan.")
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

    ns["callback"] = callback
    app.view_functions["webhook"] = webhook
    return True
