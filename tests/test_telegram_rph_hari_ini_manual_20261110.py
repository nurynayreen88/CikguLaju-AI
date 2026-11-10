"""Isolated regression tests; never contact Telegram, Supabase or Render."""
import unittest
from types import SimpleNamespace
from web.telegram_rph_hari_ini_manual_20261110 import install


class ManualDailyTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.generated = []
        self.progress = 0
        self.entries = [
            dict(day="Isnin", start="08:00", end="09:00",
                 class_name="3 Amanah", subject="Matematik")]
        rt = self.rt = SimpleNamespace()
        rt.state = {}
        rt.menu = lambda cid, show_persistent=False: "old menu"
        rt.callback = lambda cid, data: ("old callback", data)
        rt.send = lambda cid, text, kb: self.messages.append((text, kb)) or "sent"
        rt._timetable_entries = lambda cid: self.entries
        rt._today_rows_v25272 = lambda cid: ("Isnin", list(enumerate(self.entries)))
        def preview(cid):
            rt.state.setdefault(cid, {})["_daily_suggestions_v25292"] = [
                {"entry": dict(e)} for e in self.entries]
            return "preview"
        rt._today_rpt_suggestions_v25292 = preview
        rt._entry_with_subject_v25294 = lambda e, subj: dict(e, subject=subj)
        def candidate(cid, e):
            return {"_sequence_no": self.progress + 1,
                    "_resolved_subject_v25294": "Matematik"}, (
                        "checkpoint" if self.progress else "calendar")
        rt._daily_candidate_v25292 = candidate
        def generate(cid, e, row=None):
            self.progress += 1
            self.generated.append(self.progress)
            return {"ok": True, "reason": "success"}
        rt._generate_calendar_row_v25293 = generate
        rt._generate_one_quick_rph_v25278 = lambda cid, e: generate(cid, e)
        rt._telegram_delivery_ok_v25279 = lambda result: result == "OK"
        rt._send_document_before_v25277 = lambda cid, path, caption="": "OK"
        rt._handle_timetable_upload_v25281 = lambda cid, m: "reader"
        self.assertTrue(install(rt))

    def test_manual_timetable_no_upload(self):
        self.assertEqual(self.rt.callback(1, "timetable"), "sent")
        text, kb = self.messages[-1]
        self.assertIn("3 Amanah", text)
        self.assertIn("08:00", text)
        callbacks = [b["callback_data"] for row in kb for b in row]
        self.assertIn("tt_add", callbacks)
        self.assertNotIn("ttupload281_start", callbacks)
        self.assertFalse(self.rt.TT_READER_ALLOW_GEMINI)

    def test_reader_old_buttons_disabled(self):
        self.assertEqual(self.rt.callback(1, "ttupload281_start"), "sent")
        self.assertIn("dimatikan", self.messages[-1][0])
        self.assertEqual(self.rt._handle_timetable_upload_v25281(1, {}), "sent")
        self.assertIn("manual", self.messages[-1][0].lower())

    def test_generate_only_after_preview_and_once(self):
        self.assertEqual(self.rt.callback(1, "daily292_generate"), "preview")
        self.assertEqual(self.rt.callback(1, "daily292_generate"), "sent")
        self.assertEqual(self.generated, [1])
        self.assertEqual(self.rt.callback(1, "daily292_generate"), "preview")
        self.assertEqual(self.generated, [1])

    def test_two_slots_advance_two_distinct_lessons(self):
        self.entries.append(dict(day="Isnin", start="10:00", end="11:00",
                                 class_name="3 Amanah", subject="Matematik"))
        self.rt.callback(1, "todayrph272")
        self.rt.callback(1, "daily292_generate")
        self.assertEqual(self.generated, [1, 2])

    def test_exact_duplicate_slot_never_double_generates(self):
        self.entries.append(dict(self.entries[0]))
        self.rt.callback(1, "todayrph272")
        self.rt.callback(1, "daily292_generate")
        self.assertEqual(self.generated, [1])

    def test_legacy_recorder_rejects_unconfirmed_delivery(self):
        self.rt._telegram_delivery_ok_v25279 = lambda result: False
        self.rt.state.setdefault(1, {})["_rph_hari_ini_delivery_guard_20261110"] = True
        with self.assertRaisesRegex(RuntimeError, "not confirmed"):
            self.rt._send_document_before_v25277(1, "/tmp/a.pdf", "RPH")
        self.rt.state[1].pop("_rph_hari_ini_delivery_guard_20261110")
        self.assertEqual(self.rt._send_document_before_v25277(1, "/tmp/a.pdf", "RPH"), "OK")

    def test_failed_delivery_does_not_count_success(self):
        self.rt._telegram_delivery_ok_v25279 = lambda result: False
        def send_rph(cid, entry, row):
            self.rt._send_document_before_v25277(cid, "/tmp/rph.pdf", "RPH")
            self.progress += 1
            return {"ok": True}
        self.rt._generate_calendar_row_v25293 = send_rph
        self.rt.callback(1, "todayrph272")
        self.assertEqual(self.rt.callback(1, "daily292_generate"), "sent")
        self.assertEqual(self.progress, 0)
        self.assertIn("Berjaya: <b>0/1</b>", self.messages[-1][0])

    def test_menu_is_additive_and_old_callbacks_unchanged(self):
        self.assertEqual(self.rt.menu(1), "old menu")
        self.assertEqual(self.messages, [])  # no second main-menu message
        self.assertEqual(self.rt.callback(1, "ak26:home"), ("old callback", "ak26:home"))
        self.assertEqual(self.rt.callback(1, "tt_add"), ("old callback", "tt_add"))
        self.assertTrue(install(self.rt))


if __name__ == "__main__":
    unittest.main()
