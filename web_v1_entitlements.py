"""Read-only presentation of CikguLaju account entitlements.

All flags and dates must come from a trusted authenticated backend, never browser input.
This module does not change credits or payment records.
"""
from datetime import date


def display_access(*, rakan_pembangun=False, vip_until=None, free_remaining=None, today=None):
    """Prioritize lifetime access, then active VIP, then remaining free credits."""
    today = today or date.today()
    if rakan_pembangun:
        return {"status": "Rakan Pembangun", "access": "Tanpa had seumur hidup"}
    if vip_until is not None:
        if not isinstance(vip_until, date):
            raise ValueError("vip_until must be a date")
        if vip_until >= today:
            return {"status": "VIP", "access": "Tanpa had sehingga " + vip_until.strftime("%d/%m/%Y")}
    if free_remaining is None:\n        return {"status": "Percuma", "access": "Baki janaan belum tersedia"}\n    if type(free_remaining) is not int or free_remaining < 0 or free_remaining > 10:
        raise ValueError("invalid free remaining credits")
    return {"status": "Percuma", "access": str(free_remaining) + "/10 janaan percuma berbaki"}


def display_trusted_account(account, *, today=None):
    """Convert a server-authenticated entitlement snapshot into display fields.

    Caller must obtain account from its own authenticated backend, not query params.
    No credit mutation occurs here.
    """
    if not isinstance(account, dict):
        raise ValueError("trusted account snapshot required")
    if account.get("authenticated") is not True:
        return {"status": "Belum disambungkan", "access": "Sambungkan akaun Telegram"}
    if "rakan_pembangun" in account and type(account["rakan_pembangun"]) is not bool:\n        raise ValueError("invalid lifetime entitlement flag")\n    lifetime = account.get("rakan_pembangun") is True
    expiry = account.get("vip_until")
    if isinstance(expiry, str):
        try:
            expiry = date.fromisoformat(expiry)
        except ValueError:
            raise ValueError("invalid VIP expiry date")
    if expiry is not None and type(expiry) is not date:\n        raise ValueError("invalid VIP expiry type")\n    remaining = account.get("free_remaining")
    return display_access(rakan_pembangun=lifetime, vip_until=expiry,
                          free_remaining=remaining, today=today)
