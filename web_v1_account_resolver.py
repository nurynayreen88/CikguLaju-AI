"""Read-only shared-account resolver for Web V1.

The lookup callback must be a trusted server-side function reading the existing
Telegram account store. It must never auto-register unknown identities.
"""
from web_v1_entitlements import display_trusted_account
from web_v1_access_policy import can_use_feature
from web_v1_sessions import verify_session_ticket


def resolve_account(ticket, signing_secret, lookup_existing_account, *, now=None):
    """Return trusted account snapshot or None; never create or mutate accounts."""
    if not callable(lookup_existing_account):
        return None
    telegram_id = verify_session_ticket(ticket, signing_secret, now=now)
    if telegram_id is None:
        return None
    try:
        account = lookup_existing_account(telegram_id)
    except Exception:
        return None
    if not isinstance(account, dict):
        return None
    if account.get("authenticated") is not True:
        return None
    if type(account.get("telegram_user_id")) is not int:
        return None
    if account["telegram_user_id"] != telegram_id:
        return None
    try:
        display_trusted_account(account)
    except (TypeError, ValueError):
        return None
    return account


def resolve_feature_access(ticket, signing_secret, lookup_existing_account, feature, *, now=None, today=None):
    account = resolve_account(ticket, signing_secret, lookup_existing_account, now=now)
    return can_use_feature(account, feature, today=today)
