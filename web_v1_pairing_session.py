"""Fail-closed pairing-to-session bridge for an isolated test backend.

The caller must authenticate the browser challenge, verify the Telegram bot update
and look up an existing account. No HTTP endpoints are enabled by this module.
"""
from web_v1_pairing_store import consume_pairing
from web_v1_sessions import issue_session_ticket


def finish_verified_pairing(connection, challenge_hash, browser_challenge_hash,
                            account_lookup, session_secret, *, now=None):
    """Consume once and issue a signed session only for a verified existing account.

    The browser must prove possession of the original pairing challenge through
    a trusted server-side binding. Do not accept a hash supplied by an arbitrary
    browser as proof of ownership.
    """
    if not isinstance(challenge_hash, str) or not isinstance(browser_challenge_hash, str):
        return None
    if challenge_hash != browser_challenge_hash or len(challenge_hash) != 64:
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
