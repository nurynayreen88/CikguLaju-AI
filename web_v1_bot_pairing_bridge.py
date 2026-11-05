"""Staging-only Telegram /start bridge for Web V1 phone pairing.

Call ONLY from an authenticated Telegram bot update handler. Never trust an
HTTP-supplied Telegram user ID, forwarded text, or a browser callback.
This module neither modifies the production bot nor registers a webhook.
"""
import re

from web_v1_pairing_challenges import challenge_storage_key
from web_v1_pairing_store import confirm_pairing

_PAYLOAD = re.compile(r"^/start(?:@[A-Za-z0-9_]{5,32})? web_([A-Za-z0-9_-]{40,64})$")


def confirm_web_pairing_from_bot_update(connection, message, *, expected_bot_username=None, now=None):
    """Return True only for an authenticated Telegram update's private /start.

    Caller MUST authenticate the Telegram update before calling this function.
    'message' must be the message object from that trusted update, not user input.
    """
    if not isinstance(message, dict):
        return False
    sender = message.get("from")
    chat = message.get("chat")
    text = message.get("text")
    if not isinstance(sender, dict) or not isinstance(chat, dict) or not isinstance(text, str):
        return False
    if chat.get("type") != "private":
        return False
    uid = sender.get("id")
    if type(uid) is not int or uid <= 0 or chat.get("id") != uid:
        return False
    if sender.get("is_bot") is True:
        return False
    if len(text) > 128:
        return False
    match = _PAYLOAD.fullmatch(text)
    if not match:
        return False
    if "@" in text.split(" ", 1)[0]:
        if not isinstance(expected_bot_username, str) or not expected_bot_username:
            return False
        addressed = text.split(" ", 1)[0].split("@", 1)[1]
        if addressed.lower() != expected_bot_username.lstrip("@").lower():
            return False
    token = match.group(1)
    if challenge_storage_key(token) is None:
        return False
    return confirm_pairing(connection, token, uid, now=now)
