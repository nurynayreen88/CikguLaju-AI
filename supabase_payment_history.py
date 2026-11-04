"""Read-only, non-destructive payment history aggregation for CikguLaju.

Does not modify entitlements, payment rows, or user records. Integrate into
Telegram handlers only after verifying the application's existing Supabase
client and authorization flow. Use only server-side credentials.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable, Any


def _timestamp(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def get_payment_history(telegram_user_id: int, fetch_rows: Callable[[str, int], list[dict]]) -> list[dict]:
    """Combine verified transaction sources for ONE Telegram user.

    fetch_rows(table, user_id) must enforce telegram_user_id=eq.<user_id>
    server-side. Do not expose this function through an unauthenticated API.
    Entitlements are not payment receipts: they are shown as approvals only.
    """
    user_id = int(telegram_user_id)
    if user_id <= 0:
        raise ValueError("Invalid Telegram user ID")
    output = []
    sources = (
        ("subscription_payments", "subscription"),
        ("payments", "credits"),
        ("pioneer_entitlements", "rakan_pembangun_approval"),
    )
    for table, kind in sources:
        for row in fetch_rows(table, user_id):
            if int(row.get("telegram_user_id", -1)) != user_id:
                raise ValueError("Unscoped payment history query")
            status = row.get("status") or ("revoked" if row.get("revoked_at") else "approved")
            output.append({
                "source": table,
                "kind": kind,
                "reference": row.get("payment_reference"),
                "amount_rm": str(Decimal(str(row["amount_rm"]))) if row.get("amount_rm") is not None else None,
                "status": status,
                "date": _timestamp(row.get("created_at") or row.get("approved_at") or row.get("paid_at")),
                "is_payment_receipt": table != "pioneer_entitlements",
            })
    return sorted(output, key=lambda x: x["date"], reverse=True)
