"""Fail-closed pairing-to-session bridge for an isolated test backend.

The caller must authenticate the browser challenge, verify the Telegram bot update
and look up an existing account. No HTTP endpoints are enabled by this module.
"""
from web_v1_browser_binding import verify_browser_binding
from web_v1_pairing_store import consume_pairing
from web_v1_sessions import issue_session_ticket


def finish_verified_pairing(connection, challenge_hash, browser_secret, browser_signature,
                            browser_signing_secret, account_lookup, session_secret, *, now=None):
    """Consume once and issue a signed session only for a verified existing account.

    The browser must present a valid independent browser secret and signed binding.
    Never accept a matching challenge hash alone as proof of browser ownership.
    """
    if not verify_browser_binding(challenge_hash, browser_secret, browser_signature,
                                  browser_signing_secret):
        return None
    if not callable(account_lookup):
        return None
    if not isinstance(session_secret, str) or len(session_secret) < 32:
        return None
    # Consumption is deliberately irreversible even if the account lookup fails.
    telegram_user_id = consume_pairing(connection, challenge_hash, now=now)
    if telegram_user_id is None:
        return None
    try:
        account = account_lookup(telegram_user_id)
    except Exception:
        # The challenge has already been consumed: never allow a replay on lookup failure.
        return None
    if not isinstance(account, dict) or type(account.get("telegram_user_id")) is not int or account["telegram_user_id"] != telegram_user_id:
        return None
    return issue_session_ticket(telegram_user_id, session_secret, now=now)
