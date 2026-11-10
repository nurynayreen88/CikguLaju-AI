"""Offline regression: Telegram 'Sediakan RPH' copy changes, not its flow."""
import unittest
from types import SimpleNamespace

from web.telegram_rph_entry_choices_20261110 import install


class EntryChoiceTests(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self.old_quick_calls = []
        self.old_callback_calls = []
        self.old_menu_calls = []
        self.runtime = SimpleNamespace(
            state={},
            send=lambda cid, text, buttons: self.sent.append((cid, text, buttons)) or "sent",
            quick=lambda cid: self.old_quick_calls.append(cid) or "old quick",
            callback=lambda cid, code: self.old_callback_calls.append((cid, code)) or "original route",
            menu=lambda cid: self.old_menu_calls.append(cid) or "original menu",
            CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE=True,
        )
        self.callback = self.runtime.callback
        self.menu = self.runtime.menu

    def test_two_choices_replace_teruskan_without_route_changes(self):
        self.assertTrue(install(self.runtime))
        self.runtime.state[123] = {"old": True}
        self.assertEqual(self.runtime.quick(123), "sent")
        cid, copy, keyboard = self.sent[-1]
        self.assertEqual(cid, 123)
        self.assertIn("📚 <b>Sediakan RPH</b>", copy)
        self.assertIn("RPH Harian", copy)
        self.assertIn("RPH Aktiviti Khas", copy)
        self.assertIn("Minggu Transisi Tahun 1", copy)
        self.assertIn("selepas tamat sukatan", copy)
        self.assertIn("DRAF", copy)
        self.assertIn("SK/SP, RPT/SOW, buku teks dan buku aktiviti", copy)
        self.assertIn("✅ SUBMIT", copy)
        self.assertNotIn("Teruskan", copy)
        buttons = [b for row in keyboard for b in row]
        self.assertEqual([b["text"] for b in buttons],
                         ["📝 RPH Harian", "🌱 RPH Aktiviti Khas", "🏠 Menu Utama"])
        self.assertEqual([b["callback_data"] for b in buttons],
                         ["choose_grade", "ak26:home", "home"])
        self.assertEqual(self.runtime.state[123], {
            "task": "quick_material",
            "quick_material_flow": True,
            "_cid": 123,
        })

    def test_existing_callbacks_menu_and_submit_are_untouched(self):
        self.assertTrue(install(self.runtime))
        self.assertIs(self.runtime.callback, self.callback)
        self.assertIs(self.runtime.menu, self.menu)
        for code in ("choose_grade", "ak26:home", "matsubmit2528", "home"):
            self.assertEqual(self.runtime.callback(123, code), "original route")
        self.assertEqual([c[1] for c in self.old_callback_calls],
                         ["choose_grade", "ak26:home", "matsubmit2528", "home"])
        self.assertEqual(self.runtime.menu(123), "original menu")

    def test_idempotent_and_fails_closed_without_special_catalogue(self):
        self.assertTrue(install(self.runtime))
        selected = self.runtime.quick
        self.assertTrue(install(self.runtime))
        self.assertIs(selected, self.runtime.quick)
        no_special = SimpleNamespace(
            quick=lambda cid: None, send=lambda *a: None, state={},
            CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE=False,
        )
        self.assertFalse(install(no_special))
        self.assertFalse(hasattr(no_special, "CIKGULAJU_RPH_ENTRY_CHOICES_20261110"))


if __name__ == "__main__":
    unittest.main()
