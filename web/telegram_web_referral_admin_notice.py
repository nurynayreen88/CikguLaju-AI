"""Authenticated Web referral signup -> Telegram admin notification.

Only a recently registered user with a real, verified Supabase referral_signup
may trigger the notice. This does not create a user, award points, or change
payment status. The source request is authenticated with the shared backend
API token, never a browser token.
"""
from datetime import datetime, timezone, timedelta
from html import escape
import hmac
import os
import re
from flask import Blueprint, request, jsonify

PATH = "/internal/referral/v1/new-web-signup-notify"


def create_web_referral_signup_notice(runtime):
    bp = Blueprint("web_referral_admin_signup_notice", __name__)

    @bp.post(PATH)
    def notify():
        secret = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
        authorization = request.headers.get("Authorization", "")
        if len(secret) < 32 or not hmac.compare_digest(authorization, "Bearer " + secret):
            return jsonify({"error": "unauthorized"}), 401
        if (not request.is_json or request.content_length is None
                or request.content_length > 1024):
            return jsonify({"error": "invalid request"}), 400
        payload = request.get_json(silent=True)
        if (not isinstance(payload, dict)
                or set(payload) != {"telegram_user_id"}
                or type(payload["telegram_user_id"]) is not int
                or not 0 < payload["telegram_user_id"] < 10**18):
            return jsonify({"error": "invalid identity"}), 400

        uid = payload["telegram_user_id"]
        admin = str(getattr(runtime, "ADMIN_CHAT_ID", "") or "")
        if (not re.fullmatch(r"[1-9][0-9]{4,17}", admin)
                or not callable(getattr(runtime, "_is_admin", None))
                or not runtime._is_admin(admin)
                or not callable(getattr(runtime, "send", None))):
            return jsonify({"error": "Telegram admin not available"}), 503
        try:
            sb = runtime._sb_request
            users = sb("GET", f"cikgulaju_users?telegram_user_id=eq.{uid}"
                       "&select=telegram_user_id,first_name,last_name,username,created_at,trial_remaining&limit=1") or []
            signups = sb("GET", f"referral_signups?referred_user_id=eq.{uid}"
                         "&select=referrer_user_id,captured_at&limit=1") or []
            if len(users) != 1 or len(signups) != 1:
                return jsonify({"error": "no verified new referral"}), 409
            user, signup = users[0], signups[0]
            registered = datetime.fromisoformat(str(user["created_at"]).replace("Z", "+00:00"))
            captured = datetime.fromisoformat(str(signup["captured_at"]).replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if (registered.tzinfo is None or captured.tzinfo is None
                    or now - registered > timedelta(minutes=15)
                    or captured < registered - timedelta(seconds=15)
                    or now - captured > timedelta(minutes=15)
                    or int(signup["referrer_user_id"]) == uid):
                return jsonify({"error": "referral is not a new registration"}), 409
            name = " ".join(filter(None, (str(user.get("first_name") or "").strip(),
                                          str(user.get("last_name") or "").strip()))) or "Pengguna Telegram"
            username = str(user.get("username") or "").strip()
            when = registered.astimezone(timezone(timedelta(hours=8))).strftime("%d/%m/%Y %H:%M")
            remaining = user.get("trial_remaining")
            status = (f"{remaining} janaan percuma berbaki"
                      if type(remaining) is int and 0 <= remaining <= 10 else
                      "Status akses: semak profil pengguna")
            message = (
                "🆕 <b>REFERRAL BAHARU CIKGULAJU — WEB</b>\n\n"
                f"👤 Nama: <b>{escape(name[:150])}</b>\n"
                f"🆔 ID Telegram: <code>{uid}</code>\n"
                f"🔗 Username: <b>{escape('@'+username if username else '—')}</b>\n"
                "🌐 Platform: <b>Web (login Telegram)</b>\n"
                f"🎁 Perujuk: <code>{int(signup['referrer_user_id'])}</code>\n"
                f"📅 Daftar: <b>{when}</b>\n"
                f"📋 Status: <b>{escape(status)}</b>\n\n"
                "Mata referral hanya diberikan selepas bayaran pertama diluluskan."
            )
            result = runtime.send(admin, message, [
                [{"text": "👤 LIHAT PENGGUNA", "callback_data": f"admin_user|{uid}"}],
                [{"text": "🛠️ ADMIN PANEL", "callback_data": "admin_panel"}],
            ])
            if result is None or not result.ok or not (result.json() or {}).get("ok"):
                return jsonify({"error": "Telegram notification failed"}), 503
            return jsonify({"notified": True})
        except Exception as exc:
            print("WEB REFERRAL ADMIN notification error:", type(exc).__name__, flush=True)
            return jsonify({"error": "signup notification unavailable"}), 503

    return bp
