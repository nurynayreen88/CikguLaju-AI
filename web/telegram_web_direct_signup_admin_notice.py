"""Notify CikguLaju Telegram admin of truly new Web-created accounts.

Only trusted backend requests, backed by the shared Supabase registration
marker, can trigger an alert. The one-time claim is atomic and survives
deploys. No Telegram message is sent to the user before they /start the bot.
"""
from datetime import datetime, timezone, timedelta
from html import escape
import hmac
import os
import re
from flask import Blueprint, jsonify, request

PATH = "/internal/web-signup/v1/admin-notify"


def create_web_direct_signup_admin_notice(runtime):
    bp = Blueprint("web_direct_signup_admin_notice", __name__)

    @bp.post(PATH)
    def notify():
        secret = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
        if (len(secret) < 32 or not hmac.compare_digest(
                request.headers.get("Authorization", ""), "Bearer " + secret)):
            return jsonify({"error": "unauthorized"}), 401
        if (not request.is_json or request.content_length is None
                or request.content_length > 1024):
            return jsonify({"error": "invalid request"}), 400
        body = request.get_json(silent=True)
        if (not isinstance(body, dict) or set(body) != {"telegram_user_id"}
                or type(body["telegram_user_id"]) is not int
                or not 0 < body["telegram_user_id"] < 10**18):
            return jsonify({"error": "invalid identity"}), 400
        uid = body["telegram_user_id"]
        admin = str(getattr(runtime, "ADMIN_CHAT_ID", "") or "")
        if (not re.fullmatch(r"[1-9][0-9]{4,17}", admin)
                or not callable(getattr(runtime, "_is_admin", None))
                or not runtime._is_admin(admin)
                or not callable(getattr(runtime, "send", None))):
            return jsonify({"error": "Telegram admin unavailable"}), 503
        try:
            sb = runtime._sb_request
            registrations = sb("GET", f"web_direct_signups?telegram_user_id=eq.{uid}"
                               "&select=telegram_user_id,created_at,notified_at&limit=1") or []
            users = sb("GET", f"cikgulaju_users?telegram_user_id=eq.{uid}"
                       "&select=telegram_user_id,first_name,last_name,username,created_at,trial_remaining&limit=1") or []
            if len(registrations) != 1 or len(users) != 1:
                return jsonify({"error": "not a Web registered account"}), 409
            registration, user = registrations[0], users[0]
            if registration.get("notified_at"):
                return jsonify({"notified": False, "reason": "already_recorded"})
            created = datetime.fromisoformat(str(user["created_at"]).replace("Z", "+00:00"))
            stamp = datetime.fromisoformat(str(registration["created_at"]).replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (created.tzinfo is None or stamp.tzinfo is None
                    or abs((created - stamp).total_seconds()) > 120
                    or not timedelta(0) <= now-created <= timedelta(minutes=15)):
                return jsonify({"error": "not a recent Web registration"}), 409

            # Single atomic notification claim. Concurrent login requests cannot
            # send duplicate notifications; fail closed on uncertain results.
            claimed = sb("PATCH", f"web_direct_signups?telegram_user_id=eq.{uid}"
                         "&notified_at=is.null", json={"notified_at": now.isoformat()},
                         prefer="return=representation") or []
            if len(claimed) != 1:
                return jsonify({"notified": False, "reason": "already_claimed"})

            signups = sb("GET", f"referral_signups?referred_user_id=eq.{uid}"
                         "&select=referrer_user_id&limit=1") or []
            referrer = ("ID " + str(int(signups[0]["referrer_user_id"]))
                        if signups else "Tiada")
            name = " ".join(s for s in (
                str(user.get("first_name") or "").strip(),
                str(user.get("last_name") or "").strip()) if s) or "Pengguna Telegram"
            username = str(user.get("username") or "").strip()
            time_myt = created.astimezone(timezone(timedelta(hours=8))).strftime("%d/%m/%Y %H:%M")
            remaining = user.get("trial_remaining")
            status = (str(remaining) + " janaan percuma berbaki"
                      if type(remaining) is int and 0 <= remaining <= 10
                      else "Semak status akaun")
            message = (
                "🆕 <b>PENGGUNA BAHARU CIKGULAJU</b>\n\n"
                f"👤 Nama: <b>{escape(name[:150])}</b>\n"
                f"🆔 Telegram ID: <code>{uid}</code>\n"
                f"🔗 Username: <b>{escape('@'+username if username else '—')}</b>\n"
                "🌐 Platform: <b>Web (Telegram Login)</b>\n"
                f"🎁 Referral: <b>{escape(referrer)}</b>\n"
                f"📅 Daftar: <b>{time_myt}</b>\n"
                f"📋 Status: <b>{escape(status)}</b>"
            )
            result = runtime.send(admin, message, [
                [{"text": "👤 LIHAT PENGGUNA", "callback_data": f"admin_user|{uid}"}],
                [{"text": "🛠️ ADMIN PANEL", "callback_data": "admin_panel"}]
            ])
            if result is None or not result.ok or not (result.json() or {}).get("ok"):
                return jsonify({"error": "Telegram delivery unavailable"}), 503
            return jsonify({"notified": True})
        except Exception as exc:
            print("WEB DIRECT SIGNUP admin notification error:",
                  type(exc).__name__, flush=True)
            return jsonify({"error": "Web signup notification unavailable"}), 503

    return bp
