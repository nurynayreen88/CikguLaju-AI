"""Regression: English Y4 Lesson030 MUST NOT send stale CD2 Track29.

Exercise the actual opt-in guard without importing app.py, opening a user DB,
calling Telegram APIs or changing credits. The guard must leave other lessons,
Year 1 and all non-media RPH Word/PDF choices unchanged.
"""
from pathlib import Path
from types import SimpleNamespace
import unittest

from web.english_y4_l030_audio_guard import install, _is_y4_l030


class AudioConflictGuardTests(unittest.TestCase):
    def fake_runtime(self):
        calls = []
        notices = []

        def available(ss):
            if _is_y4_l030(ss):
                # Simulate a stale state mutated by the old v25.259 media layer.
                ss["audio_status"] = "VERIFIED_AUDIO"
                ss["audio_storage_file_id"] = "1jndYaX3ysrgEERRYQFFojPLxHuwN35Ob"
            return ["rph", "rph_word", "textbook", "media", "activity"]

        def send_media(cid, ss, key):
            calls.append(("selector", cid, key))
            return True

        def direct_media(cid, ss, key):
            calls.append(("legacy", cid, key))
            return True

        def verified_send(cid, rows):
            calls.append(("approved", cid, [dict(row) for row in rows]))
            return True

        rt = SimpleNamespace(
            _available_materials_v2528=available,
            _send_reference_material_v2528=send_media,
            _send_reference_material=direct_media,
            _send_verified_media_rows_v2594=verified_send,
            send=lambda cid, text: notices.append((cid, text)),
            _EN4_AUDIO_ALL_V25257={30: [{"audio_reference": "CD2 Track 29"}], 31: ["other"]},
            _EN4_AUDIO_ALL_V25258={
                30: [{"audio_reference": "CD2 Track 29"}], 31: ["other"],
                103: [{"audio_reference": "CD2 Track 26", "storage_file_id": "1vpNkB4OWao5iPQvHzEpemQrlNiNhkX4H"},
                      {"audio_reference": "CD2 Track 27", "storage_file_id": "wrong103-27"},
                      {"audio_reference": "CD2 Track 28", "storage_file_id": "wrong103-28"}],
            },
            _EN4_AUDIO_ALL_V25259={
                30: [{"audio_reference": "CD2 Track 29"}], 31: ["other"],
                103: [{"audio_reference": "CD2 Track 26", "storage_file_id": "1vpNkB4OWao5iPQvHzEpemQrlNiNhkX4H"},
                      {"audio_reference": "CD2 Track 27", "storage_file_id": "wrong103-27"},
                      {"audio_reference": "CD2 Track 28", "storage_file_id": "wrong103-28"}],
            },
        )
        return rt, calls, notices

    def test_all_old_cd2_entries_removed_only_for_lesson30(self):
        rt, _, _ = self.fake_runtime()
        self.assertTrue(install(rt))
        for name in ("_EN4_AUDIO_ALL_V25257", "_EN4_AUDIO_ALL_V25258",
                     "_EN4_AUDIO_ALL_V25259"):
            mapping = getattr(rt, name)
            self.assertNotIn(30, mapping)
            self.assertEqual(mapping[31], ["other"])
        self.assertTrue(install(rt))  # idempotent

    def test_confirmed_cd1_only_for_both_selectors_and_stale_state(self):
        rt, calls, notices = self.fake_runtime()
        self.assertTrue(install(rt))
        ss = {"subject": "English", "year": "Year 4", "lesson_no": "030",
              "audio_status": "VERIFIED_AUDIO",
              "audio_storage_file_id": "1jndYaX3ysrgEERRYQFFojPLxHuwN35Ob"}
        menu = rt._available_materials_v2528(ss)
        self.assertEqual(menu, ["rph", "rph_word", "textbook", "media", "activity"])
        self.assertEqual(ss["audio_status"], "CD1_SOURCE_CONFIRMED_DELIVERY_UNTESTED")
        self.assertEqual(ss["audio_reference"], "CD1 Track 29")
        self.assertEqual(ss["audio_storage_file_id"], "15tyBPsUwd5z9AknoOOUIiaTN6QT-Xrct")
        self.assertTrue(rt._send_reference_material_v2528(55, ss, "media"))
        self.assertTrue(rt._send_reference_material(55, ss, "media"))
        self.assertEqual(len(calls), 2)
        for route, cid, rows in calls:
            self.assertEqual(route, "approved")
            self.assertEqual(cid, 55)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["audio_reference"], "CD1 Track 29")
            self.assertEqual(rows[0]["storage_file_id"], "15tyBPsUwd5z9AknoOOUIiaTN6QT-Xrct")
            self.assertNotEqual(rows[0]["storage_file_id"], "1jndYaX3ysrgEERRYQFFojPLxHuwN35Ob")
        self.assertEqual(notices, [])
        self.assertTrue(rt._send_reference_material_v2528(55, ss, "textbook"))
        self.assertEqual(calls[-1][0], "selector")

    def test_no_approved_sender_fails_closed_without_old_cd2_fallback(self):
        rt, calls, notices = self.fake_runtime()
        delattr(rt, "_send_verified_media_rows_v2594")
        self.assertTrue(install(rt))
        ss = {"subject": "English", "year": "Year 4", "lesson_no": 30}
        self.assertNotIn("media", rt._available_materials_v2528(ss))
        self.assertNotIn("audio_storage_file_id", ss)
        self.assertFalse(rt._send_reference_material_v2528(55, ss, "media"))
        self.assertFalse(rt._send_reference_material(55, ss, "media"))
        self.assertEqual(calls, [])
        self.assertEqual(len(notices), 2)

    def test_l103_only_source_correct_cd2_track26_remains(self):
        rt, calls, notices = self.fake_runtime()
        self.assertTrue(install(rt))
        for name in ("_EN4_AUDIO_ALL_V25258", "_EN4_AUDIO_ALL_V25259"):
            rows = getattr(rt, name)[103]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["audio_reference"], "CD2 Track 26")
            self.assertEqual(rows[0]["storage_file_id"],
                             "1vpNkB4OWao5iPQvHzEpemQrlNiNhkX4H")
            self.assertNotIn(104, getattr(rt, name))
        # Only historical mapping is cleaned; real Telegram dispatch is not
        # simulated by this test and is not claimed as completed.
        self.assertTrue(rt._send_reference_material_v2528(
            55, {"subject": "English", "year": "Year 4", "lesson_no": 103}, "media"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(notices, [])

    def test_other_lessons_years_and_subjects_unchanged(self):
        rt, calls, notices = self.fake_runtime()
        install(rt)
        for ss in (
            {"subject": "English", "year": "Year 4", "lesson_no": 29},
            {"subject": "English", "year": "Year 4", "lesson_no": 31},
            {"subject": "English", "year": "Year 5", "lesson_no": 30},
            {"subject": "English", "year": "Year 1", "lesson_no": 30},
            {"subject": "Sains", "year": "Year 4", "lesson_no": 30},
        ):
            self.assertIn("media", rt._available_materials_v2528(dict(ss)))
            self.assertTrue(rt._send_reference_material_v2528(55, ss, "media"))
            self.assertTrue(rt._send_reference_material(55, ss, "media"))
        self.assertEqual(len(calls), 10)
        self.assertEqual(notices, [])

    def test_accepted_year_formats_and_failed_install(self):
        for year in (4, "4", "Year 4", "Tahun 4", "YEAR 04"):
            self.assertTrue(_is_y4_l030({"subject": "Bahasa Inggeris",
                                        "year": year, "lesson_no": 30}), year)
        self.assertFalse(_is_y4_l030({"subject": "English", "year": "Year 6",
                                      "lesson_no": 30}))
        self.assertFalse(install(SimpleNamespace()))

    def test_entrypoint_installs_last_without_changing_billing(self):
        src = (Path(__file__).resolve().parents[1] /
               "tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        self.assertIn("ENGLISH_Y4_L030_AUDIO_GUARD_ACTIVE", src)
        self.assertIn("install_y4_l030_audio_guard(telegram_runtime)", src)
        self.assertGreater(src.rfind("install_y4_l030_audio_guard"),
                           src.rfind("install_private_referral_admin"))
        guard_code = (Path(__file__).resolve().parents[1] /
                      "web/english_y4_l030_audio_guard.py").read_text(encoding="utf-8")
        self.assertNotIn("supabase", guard_code.lower())
        self.assertNotIn("UPDATE ", guard_code)
        self.assertNotIn("sendAudio", guard_code)


if __name__ == "__main__":
    unittest.main()
