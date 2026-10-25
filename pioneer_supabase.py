"""Pioneer lifetime entitlement adapter for CikguLaju's server-side Supabase client.

The caller MUST enforce admin identity and verify the actual bank transaction.
This module never accepts a receipt upload as proof of payment on its own.
"""
PIONEER_PLAN = "PIONEER_LIFETIME"


def has_pioneer(sb_request, telegram_user_id):
    uid = int(telegram_user_id)
    rows = sb_request(
        "GET",
        f"pioneer_entitlements?telegram_user_id=eq.{uid}&select=entitlement",
    ) or []
    return any(row.get("entitlement") == PIONEER_PLAN for row in rows)


def grant_pioneer(sb_request, telegram_user_id, payment_reference,
                  approved_by, verified=False):
    """Grant only after independent payment verification by authenticated admin.

    Database constraints reject reuse of a payment reference and duplicate user grants.
    """
    if verified is not True:
        raise ValueError("Admin verification required")
    reference = str(payment_reference).strip()
    if not reference:
        raise ValueError("Verified bank transaction reference required")
    uid = int(telegram_user_id)
    admin = int(approved_by)
    if uid <= 0 or admin <= 0:
        raise ValueError("Valid user and admin IDs required")
    if has_pioneer(sb_request, uid):
        raise ValueError("Pioneer entitlement already exists")
    return sb_request("POST", "pioneer_entitlements", json={
        "telegram_user_id": uid,
        "entitlement": PIONEER_PLAN,
        "payment_reference": reference,
        "approved_by": admin,
    }, prefer="return=representation")


def effective_access(sb_request, telegram_user_id, subscription_access):
    """Keep the original subscription unchanged; override access only."""
    if not has_pioneer(sb_request, telegram_user_id):
        return subscription_access
    return dict(subscription_access, active=True, status="pioneer",
                access_until=None, days_left=None, plan_code=PIONEER_PLAN)
