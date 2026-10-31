"""Read-only Supabase admin payment history helper for CikguLaju.

Caller must check admin authorization before calling. Never use this helper
with client-exposed credentials. Entitlements are approvals, not receipts.
"""
def fetch_admin_payment_history(request, limit=100):
    try:
        limit = int(limit)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Invalid limit") from exc
    if not 1 <= limit <= 1000:
        raise ValueError("Invalid limit")
    sources = (
        ("subscription_payments", "subscription", "created_at"),
        ("payments", "credit", "created_at"),
        ("pioneer_entitlements", "rakan_pembangun_approval", "approved_at"),
        ("pioneer_payment_requests", "rakan_pembangun_request", "created_at"),
    )
    fields = {
        "subscription_payments": "telegram_user_id,payment_reference,amount_rm,status,created_at",
        "payments": "telegram_user_id,payment_reference,amount_rm,status,created_at",
        "pioneer_entitlements": "telegram_user_id,payment_reference,approved_at,revoked_at",
        "pioneer_payment_requests": "telegram_user_id,amount_rm,status,created_at",
    }
    results = []
    for table, kind, date_col in sources:
        rows = request("GET", f"{table}?select={fields[table]}&order={date_col}.desc&limit={int(limit)}")
        if not isinstance(rows, list):
            raise RuntimeError("Supabase history unavailable: " + table)
        for item in rows:
            if not isinstance(item, dict):
                raise RuntimeError("Malformed Supabase history row: " + table)
            results.append({
                "telegram_user_id": item.get("telegram_user_id"),
                "kind": kind,
                "amount_rm": item.get("amount_rm"),
                "payment_reference": item.get("payment_reference"),
                "status": ("revoked" if item.get("revoked_at") else "approved") if table == "pioneer_entitlements" else (item.get("status") or "unknown"),
                "event_at": item.get(date_col) or "",
                "is_receipt": (table in ("subscription_payments", "payments") and str(item.get("status") or "").lower() in ("paid", "completed", "success")),
            })
    return sorted(results, key=lambda r: str(r["event_at"]), reverse=True)
