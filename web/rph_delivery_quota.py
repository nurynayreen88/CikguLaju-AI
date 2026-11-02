"""Server-owned generation reference and shared-trial charging boundary.

Never accept an idempotency reference from the HTTP request body. Rendering
must complete before this function is called. It does not itself send files.
"""
from uuid import uuid4

from web.shared_trial_rpc import consume_successful_generation


def charge_rendered_rph(telegram_user_id, document_bytes, supabase_url, secret_key,
                        *, debit=None):
    if type(telegram_user_id) is not int or telegram_user_id <= 0:
        raise ValueError("Invalid Telegram user")
    if not isinstance(document_bytes, bytes) or not document_bytes:
        raise ValueError("Document must be fully rendered before charging")
    if debit is None:
        debit = consume_successful_generation
    reference = "web-rph:" + str(uuid4())
    result = debit(supabase_url, secret_key, telegram_user_id, reference)
    if not result["ok"]:
        return {"allowed": False, "remaining": result["remaining"], "reference": None}
    return {"allowed": True, "remaining": result["remaining"], "reference": reference}

def has_active_paid_access(account, today=None):
    """Check a trusted account snapshot for lifetime or unexpired VIP access."""
    from datetime import date
    if not isinstance(account, dict) or account.get("authenticated") is not True:
        return False
    if type(account.get("rakan_pembangun", False)) is not bool:
        return False
    if account.get("rakan_pembangun") is True:
        return True
    expiry = account.get("vip_until")
    if not isinstance(expiry, str):
        return False
    try:
        expiry_date = date.fromisoformat(expiry)
    except ValueError:
        return False
    if today is not None and type(today) is not date:
        return False
    return expiry_date >= (today or date.today())

def authorize_rendered_document(account, telegram_user_id, document_bytes,
                                supabase_url, secret_key, *, debit=None):
    """Use trusted account access; debit trial only for a completed document."""
    if not isinstance(account, dict) or account.get("authenticated") is not True:
        raise ValueError("Authenticated account required")
    if type(telegram_user_id) is not int or telegram_user_id <= 0:
        raise ValueError("Invalid Telegram user")
    if account.get("telegram_user_id") != telegram_user_id:
        raise ValueError("Account identity mismatch")
    if not isinstance(document_bytes, bytes) or not document_bytes:
        raise ValueError("Document must be fully rendered")
    if type(account.get("rakan_pembangun", False)) is not bool:
        raise ValueError("Invalid paid entitlement")
    if account.get("vip_until") is not None:
        from datetime import date
        expiry = account["vip_until"]
        if not isinstance(expiry, str):
            raise ValueError("Invalid subscription expiry")
        try:
            date.fromisoformat(expiry)
        except ValueError:
            raise ValueError("Invalid subscription expiry") from None
    if has_active_paid_access(account):
        return {"allowed": True, "remaining": None, "reference": None}
    credits = account.get("free_remaining")
    if type(credits) is not int or credits < 0:
        raise ValueError("Invalid trial balance")
    if credits == 0:
        return {"allowed": False, "remaining": 0, "reference": None}
    return charge_rendered_rph(
        telegram_user_id, document_bytes, supabase_url, secret_key, debit=debit)
