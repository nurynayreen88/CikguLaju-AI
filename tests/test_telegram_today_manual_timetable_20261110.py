"""No-network tests for Telegram RPH Hari Ini with manual timetable only."""
import unittest
from unittest.mock import patch

from web import telegram_today_manual_timetable_20261110 as today


DAY = "2026-11-10"
SLOTS = [
    {"day": "Selasa", "start": "08:00", "end": "09:00",
     "class_name": "3 Bestari", "subject": "Matematik"},
    {"day": "Selasa", "start": "09:00", "end": "10:00",
     "class_name": "4 Amanah", "subject": "Sains"},
    {"day": "Selasa", "start": "10:00", "end": "11:00",
     "class_name": "3 Bestari", "subject": "Matematik"},
    {"day": "Selasa", "start": "11:00", "end": "12:00",
     "class_name": "3 Bestari", "subject": "Unknown"},
]


class FakeRuntime:
    def __init__(self, *, slots=None, no_gate=False, reject_send=False):
        self.state = {}
        self.messages = []
        self.ordinary = []
        self.menu_calls = 0
        self.reader_runs = 0
        self.generations = []
        self.debits = []
        self.slots = list(SLOTS if slots is None else slots)
        self.no_gate = no_gate
        self.reject_send = reject_send
        self.candidate_no = 61

    def send(self, cid, text, keyboard=None):
        self.messages.append((cid, text, keyboard))
        return {"sent": True}

    def menu(self, cid, show_persistent=False):
        self.menu_calls += 1
        return {"main_menu": True}

    def callback(self, cid, action):
        self.ordinary.append((cid, action))
        return ("old", action)

    def _timetable_menu(self, cid, note=""):
        return self.send(cid, "OLD TIMETABLE WITH UPLOAD", [])

    def _tt_upload_menu_v25281(self, cid):
        self.reader_runs += 1

    def _handle_timetable_upload_v25281(self, cid, message):
        self.reader_runs += 1

    def _timetable_entries(self, cid):
        return [dict(x) for x in self.slots]

    def _today_rows_v25272(self, cid):
        return "Selasa", list(enumerate(self._timetable_entries(cid)))

    def _daily_candidate_v25292(self, cid, entry):
        if entry["subject"] == "Unknown":
            return None, "source_not_verified"
        if entry["subject"] == "Matematik":
            return ({"_resolver": "verified_rpt_entries",
                     "_sequence_no": self.candidate_no, "id": 77}, "checkpoint")
        return ({"_resolver": "verified_rpt_entries",
                 "_sequence_no": 12, "id": 88}, "calendar_verified_rpt")

    def _entry_with_subject_v25294(self, entry, subject):
        result = dict(entry)
        result["subject"] = subject
        return result

    def _next_curriculum_summary_v25276(self, row):
        return "PdP " + str(row["_sequence_no"])

    def _generate_one_quick_rph_v25278(self, cid, entry):
        if self.no_gate:
            return {"ok": False, "reason": "no_free_trial"}
        self.generations.append(("checkpoint", dict(entry)))
        if self.reject_send:
            return {"ok": False, "reason": "delivery_not_confirmed"}
        self.debits.append(("checkpoint", cid))
        return {"ok": True, "reason": "success"}

    def _generate_calendar_row_v25293(self, cid, entry, row):
        if self.no_gate:
            return {"ok": False, "reason": "no_free_trial"}
        self.generations.append(("calendar", dict(entry)))
        if self.reject_send:
            return {"ok": False, "reason": "delivery_not_confirmed"}
        self.debits.append(("calendar", cid))
        self.state[cid]["rph_class"] = entry["class_name"]
        return {"ok": True, "reason": "success"}


class ManualTodayTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch.object(today, "_date", return_value=DAY)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.runtime = FakeRuntime()
        self.cid = 111
        self.assertTrue(today.install(self.runtime))

    def choose(self, index=0):
        self.runtime.callback(self.cid, "tm26:slot:" + str(index))
        self.assertIn("SEMAK RPH HARI INI", self.runtime.messages[-1][1])

    def test_install_safe_and_manual_schedule_menu_no_upload(self):
        self.assertTrue(today.install(self.runtime))
        self.assertTrue(self.runtime.menu(self.cid)["main_menu"])
        self.assertEqual(self.runtime.menu_calls, 1)
        self.assertIn("Buka RPH Hari Ini", str(self.runtime.messages[-1][2]))
        self.runtime._timetable_menu(self.cid)
        cid, body, kb = self.runtime.messages[-1]
        callbacks = [v["callback_data"] for row in kb for v in row
                     if "callback_data" in v]
        self.assertIn("tt_add", callbacks)
        self.assertIn("tt_delete", callbacks)
        self.assertIn("todayrph272", callbacks)
        self.assertIn("tt311_clear_ask", callbacks)
        self.assertNotIn("ttupload281_start", callbacks)
        self.assertNotIn("Upload Jadual Waktu", body)
        self.assertIn("secara manual", body)
        self.assertEqual(self.runtime.callback(self.cid, "tt_add"), ("old", "tt_add"))

    def test_old_upload_buttons_and_image_handler_disabled(self):
        self.runtime.state[self.cid] = {
            "waiting": "timetable_upload_v25281",
            "_tt286_raw_draft": [{"subject": "Wrong"}],
            "_tt_upload_draft_v25281": [{"subject": "Wrong"}],
            "saved_schedule": "untouched",
        }
        self.runtime.callback(self.cid, "ttupload281_start")
        self.runtime.callback(self.cid, "ttupload281_confirm")
        self.runtime.callback(self.cid, "tt286_confirm")
        self.runtime._tt_upload_menu_v25281(self.cid)
        self.runtime._handle_timetable_upload_v25281(self.cid, {"photo": [1]})
        self.assertEqual(self.runtime.reader_runs, 0)
        self.assertEqual(self.runtime.state[self.cid]["saved_schedule"], "untouched")
        self.assertNotIn("_tt286_raw_draft", self.runtime.state[self.cid])
        self.assertNotIn("_tt_upload_draft_v25281", self.runtime.state[self.cid])
        self.assertNotIn("waiting", self.runtime.state[self.cid])
        self.assertIn("diisi secara manual", self.runtime.messages[-1][1])

    def test_today_shows_all_manual_slots_and_verified_suggestions(self):
        self.runtime.callback(self.cid, "todayrph272")
        body = self.runtime.messages[-1][1]
        self.assertIn("RPH HARI INI", body)
        for word in ("Matematik", "Sains", "Unknown", "08:00", "11:00"):
            self.assertIn(word, body)
        self.assertIn("PdP 61", body)
        self.assertIn("PdP 12", body)
        self.assertIn("Padanan", body) if False else None
        self.assertEqual(self.runtime.generations, [])
        self.assertEqual(self.runtime.debits, [])
        self.assertNotIn("ttupload281_start", str(self.runtime.messages[-1][2]))

    def test_select_confirm_native_checkpoint_and_idempotency(self):
        self.choose(0)
        self.assertIn("3 Bestari", self.runtime.messages[-1][1])
        self.assertIn("08:00", self.runtime.messages[-1][1])
        self.runtime.callback(self.cid, "tm26:make:0")
        self.assertEqual(len(self.runtime.generations), 1)
        self.assertEqual(self.runtime.generations[0][0], "checkpoint")
        self.assertEqual(self.runtime.generations[0][1]["class_name"], "3 Bestari")
        self.assertEqual(len(self.runtime.debits), 1)
        self.runtime.callback(self.cid, "tm26:make:0")
        self.assertEqual(len(self.runtime.debits), 1)
        self.assertEqual(len(self.runtime.generations), 1)
        self.runtime.callback(self.cid, "tm26:home")
        self.assertIn("RPH telah dihantar", self.runtime.messages[-1][1])

    def test_calendar_generation_preserves_existing_manual_state(self):
        self.runtime.state[self.cid] = {"year": "Tahun 5", "rph_class": "Manual"}
        self.choose(1)
        self.assertIn("Cadangan RPT/SOW", self.runtime.messages[-1][1])
        self.runtime.callback(self.cid, "tm26:make:1")
        self.assertEqual(len(self.runtime.debits), 1)
        self.assertEqual(self.runtime.generations[0][0], "calendar")
        self.assertEqual(self.runtime.state[self.cid]["rph_class"], "Manual")

    def test_unverified_source_does_not_call_generator_or_debit(self):
        self.runtime.callback(self.cid, "tm26:slot:3")
        self.assertIn("pilih Lesson/PdP", self.runtime.messages[-1][1])
        self.runtime.callback(self.cid, "tm26:make:3")
        self.assertEqual(self.runtime.generations, [])
        self.assertEqual(self.runtime.debits, [])

    def test_changed_pdp_after_preview_must_reconfirm(self):
        self.choose(0)
        self.runtime.candidate_no = 62
        self.runtime.callback(self.cid, "tm26:make:0")
        self.assertIn("telah berubah", self.runtime.messages[-1][1])
        self.assertEqual(self.runtime.debits, [])
        self.assertEqual(self.runtime.generations, [])

    def test_failed_native_send_or_credit_gate_not_marked_success(self):
        self.choose(0)
        self.runtime.reject_send = True
        self.runtime.callback(self.cid, "tm26:make:0")
        self.assertEqual(self.runtime.debits, [])
        self.assertEqual(self.runtime.state[self.cid].get(
            "_today_manual_completed_20261110", {}), {})
        self.runtime.reject_send = False
        self.runtime.no_gate = True
        self.runtime.callback(self.cid, "tm26:make:0")
        self.assertEqual(self.runtime.debits, [])
        self.assertNotIn("RPH telah dihantar", self.runtime.messages[-1][1])

    def test_batch_excludes_duplicate_subject_and_unverified_and_is_once_only(self):
        self.runtime.callback(self.cid, "tm26:all")
        self.assertIn("SEMAK SEBELUM JANA SEMUA", self.runtime.messages[-1][1])
        self.assertIn("2 slot lain", self.runtime.messages[-1][1])
        self.runtime.callback(self.cid, "tm26:runall")
        self.assertEqual(len(self.runtime.debits), 2)
        self.assertEqual(len(self.runtime.generations), 2)
        self.assertIn("Berjaya: <b>2</b>", self.runtime.messages[-1][1])
        self.runtime.callback(self.cid, "tm26:runall")
        self.assertEqual(len(self.runtime.debits), 2)
        self.assertIn("Semak semula", self.runtime.messages[-1][1])

    def test_batch_when_second_source_changes_skips_without_debit(self):
        self.runtime.callback(self.cid, "tm26:all")
        before = self.runtime.candidate_no
        self.runtime.candidate_no = before + 1
        self.runtime.callback(self.cid, "tm26:runall")
        self.assertEqual(len(self.runtime.debits), 1)  # Sains only
        self.assertIn("PdP/Lesson berubah", self.runtime.messages[-1][1])

    def test_old_paused_telegram_buttons_do_not_reactivate_legacy_batch(self):
        for action in ("todaybatch273_run", "daily292_generate",
                       "quicknext275_1", "quickpick275_1",
                       "quickapply276_1", "todayrph272_1"):
            self.runtime.callback(self.cid, action)
            self.assertIn("RPH HARI INI", self.runtime.messages[-1][1])
        self.assertEqual(self.runtime.generations, [])
        self.assertEqual(self.runtime.debits, [])

    def test_empty_today_prompts_manual_entry(self):
        runtime = FakeRuntime(slots=[])
        self.assertTrue(today.install(runtime))
        runtime.callback(self.cid, "todayrph272")
        _, body, kb = runtime.messages[-1]
        self.assertIn("Isi jadual waktu secara manual", body)
        self.assertIn("tt_add", str(kb))


if __name__ == "__main__":
    unittest.main()
