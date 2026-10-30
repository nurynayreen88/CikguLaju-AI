"""Opt-in Telegram keyboard presenter for RPT Pendidikan Jasmani 2027.

Does not register callbacks or mutate app.py. Telegram handler should call
build_year_keyboard, then build_state_keyboard, then handle_download with
fresh server-side authorization. Locked teaser remains visible to free users.
"""
from __future__ import annotations

from rpt_pj_2027_delivery import STATES, YEARS
from rpt_pj_2027_menu_adapter import menu_years
from rpt_pj_2027_telegram_bridge import encode_callback

YEAR_PREFIX = "rptpj27year"


def build_year_keyboard(root, keyboard_factory):
    """Return a Telegram InlineKeyboardMarkup with Tahun 4, 5 and 6."""
    keyboard = keyboard_factory()
    for year in YEARS:
        if any(year in menu_years(root, state) for state in STATES):
            keyboard.add_button(f"Tahun {year}", f"{YEAR_PREFIX}:{year}")
    return keyboard


def decode_year_callback(payload):
    if not isinstance(payload, str) or payload not in {f"{YEAR_PREFIX}:{y}" for y in YEARS}:
        raise ValueError("Pilihan tahun RPT PJ tidak sah")
    return int(payload.rsplit(":", 1)[1])


def build_state_keyboard(root, year, keyboard_factory):
    """List only states with installed Word documents for the selected year."""
    if type(year) is not int or year not in YEARS:
        raise ValueError("Tahun tidak sah")
    keyboard = keyboard_factory()
    for state in STATES:
        if year in menu_years(root, state):
            keyboard.add_button(state.replace("_", " "), encode_callback(state, year))
    return keyboard


def menu_message(*, authorized):
    if authorized is True:
        return "RPT Pendidikan Jasmani 2027 — pilih Tahun 4, 5 atau 6."
    return ("RPT Pendidikan Jasmani 2027 tersedia untuk Rakan Pembangun "
            "dan pelanggan dengan langganan aktif. Pengguna percuma boleh "
            "melihat menu, tetapi muat turun memerlukan akses berbayar.")
