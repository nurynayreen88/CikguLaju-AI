"""Remove obsolete Telegram subscription advertising without changing billing.

The original menu still embeds RM8/month and RM50/year. Until a single
authoritative subscription catalog is deployed, omit prices in Telegram and
direct teachers to the Web. Do not alter callback routing or payment amounts.
"""
import re

_OLD_PLAN = re.compile(
    r"💳 <b>LANGGANAN</b>\\nBulanan: <b>RM8/sebulan</b>\\n"
    r"Tahunan: <b>RM50/setahun</b>\\n"
    r"Akan datang\\. Langganan belum dibuka\\.",
    re.IGNORECASE,
)
_NEW_PLAN = (
    "💳 <b>LANGGANAN</b>\\n"
    "Maklumat pakej dan harga semasa: sila rujuk Web CikguLaju.\\n"
    "Langganan belum dibuka."
)


def sanitize(text):
    if not isinstance(text, str):
        return text
    return _OLD_PLAN.sub(_NEW_PLAN, text)


def install(runtime):
    original = runtime.send
    if getattr(original, "_cikgulaju_subscription_price_guard", False):
        return True

    def guarded_send(cid, text, *args, **kwargs):
        return original(cid, sanitize(text), *args, **kwargs)

    guarded_send._cikgulaju_subscription_price_guard = True
    runtime.send = guarded_send
    return True
