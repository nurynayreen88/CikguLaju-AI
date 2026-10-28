"""Pioneer Early Bird percentage display. No public quota/count disclosure.

Only pass the count of distinct, confirmed and active Pioneer members.
The 500-place denominator is internal and must never appear in UI strings.
"""
from decimal import Decimal, ROUND_HALF_UP

_PIONEER_CAPACITY = 500

def pioneer_percentage(active_confirmed_count: int) -> str:
    """Return a one-decimal percentage with safe bounds."""
    count = max(0, min(int(active_confirmed_count), _PIONEER_CAPACITY))
    value = (Decimal(count) * 100 / Decimal(_PIONEER_CAPACITY)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    return f"{value:.1f}%"

def pioneer_menu_line(active_confirmed_count: int) -> str:
    return f"🏆 Pioneer Early Bird — {pioneer_percentage(active_confirmed_count)} telah menyertai"

def pioneer_details(active_confirmed_count: int) -> str:
    return (
        f"🏆 PIONEER EARLY BIRD\n"
        f"{pioneer_percentage(active_confirmed_count)} telah menyertai\n\n"
        "💰 RM10 sekali bayar\n"
        "Akses sepanjang CikguLaju AI beroperasi tanpa yuran bulanan atau tahunan."
    )
