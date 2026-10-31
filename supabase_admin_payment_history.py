"""Read-only Supabase admin payment history helper for CikguLaju.

Caller must check admin authorization before calling. Never use this helper
with client-exposed credentials. Entitlements are approvals, not receipts.
"""
def fetch_admin_payment_history(request, limit=100):
    if not 1 <= int(limit) <= 1000:
        raise ValueError("Invalid limit")
    sources = (
        ("subscription_payments", "subscription", "created_at"),
        ("payments", "credit", "created_at"),
        ("pioneer_entitlements", "rakan_pembangun_approval", "approved_at"),
    )
    results = []
    for table, kind, date_col in sources:
        rows = request("GET", f"{table}?select=*&order={date_col}.desc&limit={int(limit)}")
        if not isinstance(rows, list):
            raise RuntimeError("Supabase history unavailable: " + table)
        for item in rows:
            results.append({
                "telegram_user_id": item.get("telegram_user_id"),
                "kind": kind,
                "amount_rm": item.get("amount_rm"),
                "payment_reference": item.get("payment_reference"),
                "status": item.get("status") or ("revoked" if item.get("revoked_at") else "approved"),
                "event_at": item.get(date_col) or "",
                "is_receipt": table != "pioneer_entitlements",
            })
    return sorted(results, key=lambda r: r["event_at"], reverse=True)
