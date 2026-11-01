"""Build Telegram phone deep links without exposing browser session secrets.

The URL contains only the short-lived QR challenge. It is not a login ticket.
"""
import re
from urllib.parse import quote

_USERNAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")


def phone_pairing_link(bot_username, challenge):
    from web_v1_pairing_challenges import challenge_storage_key
    if not isinstance(bot_username, str):
        raise ValueError("invalid bot username")
    username = bot_username.lstrip("@")
    if not _USERNAME.fullmatch(username):
        raise ValueError("invalid bot username")
    if challenge_storage_key(challenge) is None:
        raise ValueError("invalid pairing challenge")
    payload = "web_" + challenge
    if len(payload) > 64:
        raise ValueError("Telegram deep-link payload exceeds 64 characters")
    return "https://t.me/" + username + "?start=" + quote(payload, safe="")
