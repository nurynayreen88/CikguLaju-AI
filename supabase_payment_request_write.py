"""Staged Supabase request persistence. Not wired into production handlers.

This module never treats a legacy SQLite ID as a Supabase ID.
All writes require server-side credentials and caller authorization.
"""
from decimal import Decimal, InvalidOperation


def create_payment_request(request, telegram_user_id, amount_rm, telegram_message_id):
    """Create a pending request; return Supabase identity ID.

    A Telegram message ID is mandatory for tracing duplicate submissions.
    The caller must enforce idempotency; this table currently has no unique
    constraint on (telegram_user_id, telegram_message_id).
    """
    if isinstance(telegram_user_id, bool) or not str(telegram_user_id).isascii() or not str(telegram_user_id).isdigit():
        raise ValueError("Invalid Telegram user ID")
    if isinstance(telegram_message_id, bool) or not str(telegram_message_id).isascii() or not str(telegram_message_id).isdigit():
        raise ValueError("Invalid Telegram message ID")
    try:
        amount = Decimal(str(amount_rm))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid amount") from exc
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        raise ValueError("Invalid amount")
    payload = {
        "telegram_user_id": int(telegram_user_id),
        "telegram_message_id": int(telegram_message_id),
        "amount_rm": str(amount),
        "status": "pending",
        "proof_received": True,
    }
    # Read first for retries; a database uniqueness constraint is still required\n    # before this helper can safely handle concurrent duplicate submissions.\n    existing = request("GET", f"pioneer_payment_requests?select=id,telegram_user_id,telegram_message_id,status,amount_rm&telegram_user_id=eq.{int(telegram_user_id)}&telegram_message_id=eq.{int(telegram_message_id)}&limit=2")\n    if not isinstance(existing, list):\n        raise RuntimeError("Cannot verify prior payment requests")\n    if len(existing) > 1:\n        raise RuntimeError("Duplicate payment requests require manual reconciliation")\n    if existing:\n        row = existing[0]\n        if (not isinstance(row, dict) or not isinstance(row.get("id"), int)\n                or row.get("telegram_user_id") != payload["telegram_user_id"]\n                or row.get("telegram_message_id") != payload["telegram_message_id"]\n                or Decimal(str(row.get("amount_rm"))) != amount):\n            raise RuntimeError("Existing payment request does not match")\n        return row["id"]\n    rows = request("POST", "pioneer_payment_requests", json=payload, prefer="return=representation")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise RuntimeError("Payment request was not confirmed by Supabase")
    saved = rows[0]
    if (saved.get("telegram_user_id") != payload["telegram_user_id"]
            or saved.get("telegram_message_id") != payload["telegram_message_id"]
            or saved.get("status") != "pending"
            or not isinstance(saved.get("id"), int)):
        raise RuntimeError("Supabase returned inconsistent payment request")
    return saved["id"]
