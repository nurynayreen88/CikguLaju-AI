import tempfile
import unittest
from pathlib import Path

from rpt_pj_2027_delivery import FILE_PATTERN
from rpt_pj_2027_telegram_menu import (
    build_year_keyboard, build_state_keyboard, decode_year_callback, menu_message,
)


class Keyboard:
    def __init__(self):
        self.buttons = []

    def add_button(self, label, callback_data):
        self.buttons.append((label, callback_data))


class TestRPTPJYearFirstMenu(unittest.TestCase):
    def test_year_first_menu_and_free_user_teaser(self):
        with tempfile.TemporaryDirectory() as temp:
            years = build_year_keyboard(temp, Keyboard)
            self.assertEqual(years.buttons, [])
            self.assertIn("Pengguna percuma", menu_message(authorized=False))
            self.assertIn("Rakan Pembangun", menu_message(authorized=False))
            self.assertEqual(decode_year_callback("rptpj27year:5"), 5)
            for payload in ("rptpj27year:7", "rptpj27year:5:paid", ""):
                with self.assertRaises(ValueError):
                    decode_year_callback(payload)

    def test_state_buttons_only_for_existing_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "RPT_PJ_2027_DOCX"
            folder.mkdir()
            (folder / FILE_PATTERN.format(state="Johor", year=4)).write_bytes(b"fixture")
            years = build_year_keyboard(root, Keyboard)
            self.assertEqual(years.buttons, [("Tahun 4", "rptpj27year:4")])
            states = build_state_keyboard(root, 4, Keyboard)
            self.assertEqual(states.buttons, [("Johor", "rptpj27:Johor:4")])
            self.assertEqual(build_state_keyboard(root, 5, Keyboard).buttons, [])
            with self.assertRaises(ValueError):
                build_state_keyboard(root, True, Keyboard)


if __name__ == "__main__":
    unittest.main()
