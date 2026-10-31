"""Telegram inline keyboard adapter for RPT PJ 2027."""


def keyboard_factory():
    from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

    class Keyboard(InlineKeyboardMarkup):
        def add_button(self, label, callback_data):
            self.add(InlineKeyboardButton(text=label, callback_data=callback_data))

    return Keyboard(row_width=1)


def year_markup(root):
    from rpt_pj_2027_telegram_menu import build_year_keyboard
    return build_year_keyboard(root, keyboard_factory)


def state_markup(root, year):
    from rpt_pj_2027_telegram_menu import build_state_keyboard
    return build_state_keyboard(root, year, keyboard_factory)
