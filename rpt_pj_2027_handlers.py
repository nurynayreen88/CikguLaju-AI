"""Explicit opt-in handlers for RPT PJ 2027 Telegram callbacks.

Register these handlers in app.py only after a reviewed server-side access
resolver is supplied. No database mutations or callback registration here.
"""
from rpt_pj_2027_telegram_bridge import handle_download, RPTAccessDenied, RPTDocumentUnavailable
from rpt_pj_2027_telegram_menu import decode_year_callback, menu_message
from rpt_pj_2027_telebot_adapter import year_markup, state_markup


def show_years(bot, chat_id, root, *, authorized):
    return bot.send_message(chat_id, menu_message(authorized=authorized),
                            reply_markup=year_markup(root))


def handle_year(bot, chat_id, root, callback_data):
    year = decode_year_callback(callback_data)
    return bot.send_message(chat_id, "Pilih negeri untuk RPT PJ Tahun " + str(year),
                            reply_markup=state_markup(root, year))


def handle_document(bot, chat_id, root, callback_data, *, user_id, access_resolver):
    try:
        return handle_download(bot, chat_id, root, callback_data,
                               user_id=user_id, access_resolver=access_resolver)
    except RPTAccessDenied:
        return bot.send_message(chat_id, "RPT 2027 memerlukan Rakan Pembangun atau langganan aktif.")
    except RPTDocumentUnavailable:
        return bot.send_message(chat_id, "Fail RPT belum tersedia. Sila cuba kemudian.")
    except ValueError:
        return bot.send_message(chat_id, "Pilihan RPT tidak sah. Sila pilih semula daripada menu.")
