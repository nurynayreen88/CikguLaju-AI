"""Server-owned generation reference and shared-trial charging boundary.

Never accept an idempotency reference from the HTTP request body. Rendering
must complete before this function is called. It does not itself send files.
"""
from uuid import uuid4

from web.shared_trial_rpc import consume_successful_generation


def charge_rendered_rph(telegram_user_id, document_bytes, supabase_url, secret_key,
                        *, debit=consume_successful_generation):
    if type(telegram_user_id) is not int or telegram_user_id <= 0:
        raise ValueError("Invalid Telegram user")
    if not isinstance(document_bytes, bytes) or not document_bytes:
        raise ValueError("Document must be fully rendered before charging")
    reference = "web-rph:" + str(uuid4())
    result = debit(supabase_url, secret_key, telegram_user_id, reference)
    if not result["ok"]:
        return {"allowed": False, "remaining": result["remaining"], "reference": None}
    return {"allowed": True, "remaining": result["remaining"], "reference": reference}
