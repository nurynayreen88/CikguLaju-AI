"""Pure access decisions for the shared CikguLaju Web/Telegram account.

Input must come from a server-authenticated, existing account lookup.
No database writes or generation side effects occur here.
"""
from datetime import date

from web_v1_entitlements import display_trusted_account


def can_use_feature(account, feature, *, today=None):
    """Fail closed for RPT, timetable AI, generation and material downloads."""
    if feature not in ("rpt", "timetable_ai", "generate", "download"):
        return False
    if not isinstance(account, dict) or account.get("authenticated") is not True:
        return False
    try:
        result = display_trusted_account(account, today=today or date.today())
    except (TypeError, ValueError):
        return False
    if result["status"] in ("Rakan Pembangun", "VIP"):
        return True
    if feature in ("rpt", "timetable_ai"):
        return False
    balance = account.get("free_remaining")
    return type(balance) is int and balance > 0
