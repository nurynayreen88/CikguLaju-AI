"""Read-only presentation of CikguLaju account entitlements.

All flags and dates must come from a trusted authenticated backend, never browser input.
This module does not change credits or payment records.
"""
from datetime import date


def display_access(*, rakan_pembangun=False, vip_until=None, free_remaining=10, today=None):
    """Prioritize lifetime access, then active VIP, then remaining free credits."""
    today = today or date.today()
    if rakan_pembangun:
        return {"status": "Rakan Pembangun", "access": "Tanpa had seumur hidup"}
    if vip_until is not None:
        if not isinstance(vip_until, date):
            raise ValueError("vip_until must be a date")
        if vip_until >= today:
            return {"status": "VIP", "access": "Tanpa had sehingga " + vip_until.strftime("%d/%m/%Y")}
    if type(free_remaining) is not int or free_remaining < 0 or free_remaining > 10:
        raise ValueError("invalid free remaining credits")
    return {"status": "Percuma", "access": str(free_remaining) + "/10 janaan percuma berbaki"}
