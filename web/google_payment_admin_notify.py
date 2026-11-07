"""Opt-in, best-effort Telegram admin notification for Google-only Web receipts.

Only configured staging bot/chat can receive the teacher's receipt; no teacher
Telegram ID is used. Failure NEVER cancels the durably pending payment row.
"""
import json
import os
import re
import secrets
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from web.provider_neutral_payment import validate_payment_plan


def notify_google_payment_admin(config, request_id, account_id, plan_code, mime, raw):
    token = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ADMIN_BOT_TOKEN", "")
    chat = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ADMIN_CHAT_ID", "")
    if (not re.fullmatch(r"[0-9]{5,15}:[A-Za-z0-9_-]{20,}", token)
            or not re.fullmatch(r"-?[0-9]{5,20}", chat)
            or not isinstance(raw, bytes) or len(raw) > 4 * 1024 * 1024):
        return False
    catalog_raw = os.environ.get("CIKGULAJU_GOOGLE_STAGING_PAYMENT_CATALOG_JSON", "")
    if not catalog_raw:
        return False
    try:
        _, amount = validate_payment_plan(plan_code, json.loads(catalog_raw))
    except (ValueError, TypeError):
        return False

    host = config["origin"]
    link = host + "/admin/google-staging-payments?payment=" + request_id
    ext = {"application/pdf": ".pdf", "image/jpeg": ".jpg",
           "image/png": ".png", "image/webp": ".webp"}.get(mime)
    if not ext or not link.startswith("https://"):
        return False
    caption = (
        "Resit baharu CikguLaju Web (staging)\n"
        "Guru: Akaun Web " + account_id[:8] + "\n"
        "Pakej: " + plan_code + "\n"
        "Bayaran: RM" + format(amount / 100, ".2f") + "\n"
        "Status: MENUNGGU SEMAKAN\n"
        "Permohonan: " + request_id
    )
    keyboard = json.dumps({"inline_keyboard": [[{
        "text": "Lihat resit & Sahkan/Tolak di Web", "url": link
    }]]}, separators=(",", ":"))
    boundary = "cg" + secrets.token_hex(16)
    def field(name, value):
        return ("--" + boundary + "\r\nContent-Disposition: form-data; name=\""
                + name + "\"\r\n\r\n" + value + "\r\n").encode()
    head = ("--" + boundary + "\r\n"
            "Content-Disposition: form-data; name=\"document\"; filename=\"resit"
            + ext + "\"\r\nContent-Type: " + mime + "\r\n\r\n").encode()
    body = (field("chat_id", chat) + field("caption", caption)
            + field("reply_markup", keyboard) + head + raw + b"\r\n"
            + ("--" + boundary + "--\r\n").encode())
    req = Request("https://api.telegram.org/bot" + token + "/sendDocument",
                  method="POST", data=body, headers={
                      "Content-Type": "multipart/form-data; boundary=" + boundary,
                      "Accept": "application/json"})
    try:
        with urlopen(req, timeout=28) as result:
            if result.status != 200:
                return False
            reply = json.loads(result.read(8193))
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        # Do not expose bot token in logs or browser response.
        return False
    return isinstance(reply, dict) and reply.get("ok") is True
