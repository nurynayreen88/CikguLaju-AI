"""Isolated tests for teacher-entered timetable and RPH Hari Ini Telegram."""
import unittest
from types import SimpleNamespace
from web.telegram_rph_hari_ini_manual_20261110 import install

class ManualDailyTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.generated = []
        self.rt = SimpleNamespace()
        self.rt.state = {}
        self.rt.menu = lambda cid, show_persistent=False: "old menu"
        self.rt.callback = lambda cid, data: ("old callback", data)
        self.rt.send = lambda cid, text, kb: self.messages.append((text, kb)) or "sent"
        self.rt._timetable_entries = lambda cid: [
            dict(day="Isnin", start="08:00", end="09:00", class_name="3 Amanah",
                 subject="Matematik")]
        def preview(cid):
            self.rt.state.setdefault(cid, {})["_daily_suggestions_v25292"] = [{"entry": {}}]
            return "preview"
        def generate(cid):
            self.generated.append(list(self.rt.state[cid]["_daily_suggestions_v25292"]))
            return "generated"
        self.rt._today_rpt_suggestions_v25292 = preview
        self.rt._generate_daily_suggestions_v25292 = generate
        self.rt._handle_timetable_upload_v25281 = lambda cid, m: "reader"
        self.assertTrue(install(self.rt))

    def test_manual_timetable_no_upload(self):
        self.assertEqual(self.rt.callback(1, "timetable"), "sent")
        text, kb = self.messages[-1]
        self.assertIn("3 Amanah", text)
        self.assertIn("08:00", text)
        buttons = [b["callback_data"] for row in kb for b in row]
        self.assertIn("tt_add", buttons)
        self.assertNotIn("ttupload281_start", buttons)
        self.assertNotIn("tt310_start", buttons)

    def test_old_reader_callbacks_blocked(self):
        self.assertEqual(self.rt.callback(1, "ttupload281_start"), "sent")
        self.assertIn("dimatikan", self.messages[-1][0])
        self.assertEqual(self.rt._handle_timetable_upload_v25281(1, {}), "sent")
        self.assertIn("manual", self.messages[-1][0].lower())

    def test_daily_generation_requires_preview_and_single_use(self):
        self.assertEqual(self.rt.callback(1, "daily292_generate"), "preview")
        self.assertEqual(self.rt.callback(1, "daily292_generate"), "generated")
        self.assertEqual(len(self.generated), 1)
        self.assertEqual(self.rt.callback(1, "daily292_generate"), "preview")
        self.assertEqual(len(self.generated), 1)

    def test_menu_keeps_old_menu_and_special_activity(self):
        self.assertEqual(self.rt.menu(1), "old menu")
        self.assertIn("RPH Hari Ini", self.messages[-1][0])
        self.assertEqual(self.rt.callback(1, "ak26:home"), ("old callback", "ak26:home"))
        self.assertEqual(self.rt.callback(1, "tt_add"), ("old callback", "tt_add"))
        self.assertTrue(install(self.rt))

if __name__ == "__main__":
    unittest.main()
