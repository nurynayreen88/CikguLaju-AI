"""Staged Supabase request persistence. Not wired into production handlers.

This module never treats a legacy SQLite ID as a Supabase ID.
All writes require server-side credentials and caller authorization.
"""
from decimal import Decimal, InvalidOperation


def _same_amount(raw, expected):
    try:
        actual = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        return False
    return actual.is_finite() and actual == expected


def _exact_cents(amount):
    digits = amount.as_tuple().digits
    places = -amount.as_tuple().exponent
    return places <= 2 or all(d == 0 for d in digits[-(places - 2):]) if places - 2 <= len(digits) else all(d == 0 for d in digits)


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
    if len(str(telegram_user_id)) > 19 or len(str(telegram_message_id)) > 19:
        raise ValueError("Telegram identifiers must fit positive bigint")
    if not 0 < int(telegram_user_id) <= 9223372036854775807 or not 0 < int(telegram_message_id) <= 9223372036854775807:
        raise ValueError("Telegram identifiers must fit positive bigint")
    try:
        amount = Decimal(str(amount_rm))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid amount") from exc
    if not amount.is_finite() or amount <= 0 or amount > Decimal("99999999.99") or not _exact_cents(amount):
        raise ValueError("Invalid amount")
    payload = {
        "telegram_user_id": int(telegram_user_id),
        "telegram_message_id": int(telegram_message_id),
        "amount_rm": str(amount),
        "status": "pending",
        "proof_received": True,
    }
    # Read first for retries; the existing database partial unique index
    # prevents concurrent pending requests for the same user.
    existing = request("GET", f"pioneer_payment_requests?select=id,telegram_user_id,telegram_message_id,status,amount_rm&telegram_user_id=eq.{int(telegram_user_id)}&telegram_message_id=eq.{int(telegram_message_id)}&limit=2")
    if not isinstance(existing, list):
        raise RuntimeError("Cannot verify prior payment requests")
    if len(existing) > 1:
        raise RuntimeError("Duplicate payment requests require manual reconciliation")
    if existing:
        row = existing[0]
        if (not isinstance(row, dict) or not isinstance(row.get("id"), int)
                or row.get("telegram_user_id") != payload["telegram_user_id"]
                or row.get("telegram_message_id") != payload["telegram_message_id"]
                or not _same_amount(row.get("amount_rm"), amount)
                or row.get("status") != "pending"):
            raise RuntimeError("Existing payment request does not match")
        # An approved/rejected request must never masquerade as a new pending one.
        return row["id"]
    pending = request("GET", f"pioneer_payment_requests?select=id,telegram_user_id,telegram_message_id,amount_rm,status&telegram_user_id=eq.{int(telegram_user_id)}&status=eq.pending&limit=2")
    if not isinstance(pending, list):
        raise RuntimeError("Cannot verify pending payment requests")
    if pending:
        raise RuntimeError("A pending payment request already exists; reconcile before creating another")
    # The database partial unique index remains authoritative under concurrency.
    rows = request("POST", "pioneer_payment_requests", json=payload, prefer="return=representation")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise RuntimeError("Payment request was not confirmed by Supabase")
    saved = rows[0]
    if (saved.get("telegram_user_id") != payload["telegram_user_id"]
            or saved.get("telegram_message_id") != payload["telegram_message_id"]
            or saved.get("status") != "pending"
            or not isinstance(saved.get("id"), int)):
        raise RuntimeError("Supabase returned inconsistent payment request")
    return saved["id"]
