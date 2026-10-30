import sys
import types
import unittest
from unittest.mock import patch
from rpt_pj_2027_telebot_adapter import keyboard_factory

class FakeButton:
    def __init__(self, text, callback_data):
        self.text = text
        self.callback_data = callback_data

class FakeMarkup:
    def __init__(self, row_width=1):
        self.row_width = row_width
        self.buttons = []
    def add(self, button):
        self.buttons.append(button)

class TestTelegramKeyboard(unittest.TestCase):
    def test_keyboard_uses_real_telebot_method(self):
        fake = types.ModuleType("telebot")
        fake.types = types.SimpleNamespace(
            InlineKeyboardButton=FakeButton, InlineKeyboardMarkup=FakeMarkup)
        with patch.dict(sys.modules, {"telebot": fake, "telebot.types": fake.types}):
            kb = keyboard_factory()
            kb.add_button("Tahun 4", "rptpj27year:4")
            self.assertEqual(kb.buttons[0].callback_data, "rptpj27year:4")

if __name__ == "__main__":
    unittest.main()
