"""Telegram-neutral menu handlers for staged RPT PJ 2027.

Wire these functions to the existing RPT 2027 callback router only after
checking the existing app's paid-access and feature flag. This module does
not register handlers or modify the running application.
"""
from rpt_pj_2027_delivery import STATES, YEARS, list_available, send_rpt_docx


def menu_states(root):
    available = list_available(root)
    states = {item["negeri"].replace(" ", "_") for item in available}
    return [state.replace("_", " ") for state in STATES if state in states]


def menu_years(root, negeri):
    state = str(negeri).strip().replace(" ", "_")
    if state not in STATES:
        return []
    available = list_available(root)
    return [year for year in YEARS if any(
        item["negeri"].replace(" ", "_") == state and item["tahun"] == year
        for item in available)]


def deliver_selected_rpt(bot, chat_id, root, *, negeri, tahun, paid_access):
    """Caller supplies paid_access from an authoritative existing DB check."""
    return send_rpt_docx(bot, chat_id, root, negeri=negeri,
                         tahun=tahun, authorized=paid_access)
