"""Optional RPT PJ 2027 Telegram callback bridge.

Integration must be explicitly registered by app.py after code review.
Callbacks encode only state/year, never payment status or filesystem paths.
The caller supplies a trusted authorization resolver on EVERY download.
"""
from __future__ import annotations

from rpt_pj_2027_calendar import can_download_rpt
from rpt_pj_2027_delivery import STATES, YEARS, RPTAccessDenied, RPTDocumentUnavailable
from rpt_pj_2027_menu_adapter import menu_states, menu_years, deliver_selected_rpt

PREFIX = "rptpj27"
MAX_CALLBACK_LENGTH = 64


def encode_callback(state, year):
    state = str(state).strip().replace(" ", "_")
    if state not in STATES or type(year) is not int or year not in YEARS:
        raise ValueError("Invalid RPT PJ 2027 selection")
    return f"{PREFIX}:{state}:{year}"


def decode_callback(payload):
    if not isinstance(payload, str) or len(payload) > MAX_CALLBACK_LENGTH:
        raise ValueError("Invalid callback")
    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != PREFIX or parts[1] not in STATES:
        raise ValueError("Invalid RPT PJ 2027 callback")
    if parts[2] not in {"4", "5", "6"}:
        raise ValueError("Invalid RPT year")
    return parts[1], int(parts[2])


def visible_catalogue(root):
    """Use only provisioned Word assets, never advertise unavailable downloads."""
    return {state: menu_years(root, state) for state in menu_states(root)}


def handle_download(bot, chat_id, root, callback_data, *, user_id, access_resolver):
    """Return Telegram send_document result after fresh server-side access check.

    access_resolver must be a callable that queries the EXISTING account
    authorization source for the Telegram USER ID, not the chat ID. Do not cache this result
    or accept user-supplied authorization flags.
    """
    state, year = decode_callback(callback_data)
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise RPTAccessDenied("Identiti pengguna tidak sah")
    if not callable(access_resolver):
        raise RPTAccessDenied("Pengesahan akses tidak tersedia")
    flags = access_resolver(user_id)
    if not isinstance(flags, dict):
        raise RPTAccessDenied("Status akses tidak dapat disahkan")
    authorized = can_download_rpt(
        is_developer=flags.get("is_developer") is True,
        subscription_active=flags.get("subscription_active") is True,
        rakan_pembangun_active=flags.get("rakan_pembangun_active") is True,
    )
    if not authorized:
        raise RPTAccessDenied("RPT 2027 memerlukan akses berbayar yang aktif")
    return deliver_selected_rpt(bot, chat_id, root, negeri=state, tahun=year,
                                paid_access=True)
