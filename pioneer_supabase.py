"""Pioneer entitlement adapter for existing Supabase REST client."""
PIONEER_PLAN = "PIONEER_LIFETIME"

def has_pioneer(sb_request, telegram_user_id):
    rows = sb_request("GET", "pioneer_entitlements?telegram_user_id=eq.%d&select=entitlement" % int(telegram_user_id)) or []
    return any(row.get("entitlement") == PIONEER_PLAN for row in rows)

def grant_pioneer(sb_request, telegram_user_id, payment_reference, approved_by, verified=False):
    if not verified:
        raise ValueError("Admin verification required")
    ref = str(payment_reference).strip()
    if not ref:
        raise ValueError("Payment reference required")
    return sb_request("POST", "pioneer_entitlements", json={
        "telegram_user_id": int(telegram_user_id),
        "entitlement": PIONEER_PLAN,
        "payment_reference": ref,
        "approved_by": int(approved_by),
    }, prefer="return=representation")

def effective_access(sb_request, telegram_user_id, subscription_access):
    if not has_pioneer(sb_request, telegram_user_id):
        return subscription_access
    return dict(subscription_access, active=True, status="pioneer",
                access_until=None, days_left=None, plan_code=PIONEER_PLAN)
