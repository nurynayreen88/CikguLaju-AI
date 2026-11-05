"""Fail closed Year4 L29 CD3 source safety without production writes."""
import unittest
from types import SimpleNamespace
from pathlib import Path
from web.english_y4_l029_audio_guard import install,_is_english_y4_l29

ROOT=Path(__file__).resolve().parents[1]

class Lesson29ClilWrongDiscGuard(unittest.TestCase):
    def setup_runtime(self):
        calls=[];notices=[]
        def available(ss):
            if _is_english_y4_l29(ss):
                ss["audio_storage_file_id"]="1BJFfffgxHyiYohapgypE2C212W3177mt"
                ss["audio_reference"]="CD1 Track 35"
            return ["rph","rph_word","textbook","media","activity"]
        def original_send(cid,ss,key):
            calls.append(("normal",cid,key))
            return True
        def old_direct(cid,ss,key):
            calls.append(("legacy",cid,key))
            return True
        rt=SimpleNamespace(
            _available_materials_v2528=available,
            _send_reference_material_v2528=original_send,
            _send_reference_material=old_direct,
            _EN4_AUDIO_ALL_V25258={
                29:[{"audio_reference":"CD1 Track 35","storage_file_id":"1BJFfffgxHyiYohapgypE2C212W3177mt"}],
                30:[{"audio_reference":"CD2 Track 29"}],
                103:[{"audio_reference":"CD2 Track 26"}]},
            _EN4_AUDIO_ALL_V25259={
                29:[{"audio_reference":"CD1 Track 35"},{"audio_reference":"CD1 Track 36"}],
                30:[{"audio_reference":"CD2 Track 29"}],
                103:[{"audio_reference":"CD2 Track 26"}]},
            send=lambda cid,msg:notices.append((cid,msg)),
        )
        return rt,calls,notices

    def test_exact_lesson29_media_hidden_and_old_callback_blocked(self):
        rt,calls,notices=self.setup_runtime()
        self.assertTrue(install(rt))
        self.assertTrue(install(rt))
        state={"subject":"English","year":"Year 4","lesson_no":"029"}
        self.assertNotIn("media",rt._available_materials_v2528(state))
        self.assertEqual(state["audio_reference"],"TB p.193: CD3 Tracks 35/36 (delivery pending)")
        self.assertNotIn("audio_storage_file_id",state)
        self.assertFalse(rt._send_reference_material_v2528(42,state,"media"))
        self.assertFalse(rt._send_reference_material(42,state,"media"))
        self.assertEqual(calls,[])
        self.assertEqual(len(notices),2)
        self.assertTrue(all("CD3 Track 35/36" in msg for _,msg in notices))
        self.assertTrue(rt._send_reference_material_v2528(42,state,"rph_word"))
        self.assertTrue(rt._send_reference_material_v2528(42,state,"rph"))
        self.assertEqual([x[2] for x in calls],["rph_word","rph"])

    def test_old_cd1_entries_removed_l29_only(self):
        rt,_,_=self.setup_runtime()
        install(rt)
        for name in ("_EN4_AUDIO_ALL_V25258","_EN4_AUDIO_ALL_V25259"):
            data=getattr(rt,name)
            self.assertNotIn(29,data)
            self.assertIn(30,data)
            self.assertIn(103,data)

    def test_all_other_years_subjects_lessons_untouched(self):
        rt,calls,notices=self.setup_runtime();install(rt)
        for ss in (
            {"subject":"English","year":4,"lesson_no":28},
            {"subject":"English","year":"Year 4","lesson_no":30},
            {"subject":"English","year":"4","lesson_no":103},
            {"subject":"English","year":"Year 5","lesson_no":29},
            {"subject":"Maths","year":"Year 4","lesson_no":29},
        ):
            self.assertIn("media",rt._available_materials_v2528(ss))
            self.assertTrue(rt._send_reference_material_v2528(42,ss,"media"))
            self.assertTrue(rt._send_reference_material(42,ss,"media"))
        self.assertEqual(len(calls),10)
        self.assertEqual(notices,[])
        self.assertTrue(_is_english_y4_l29({"subject":"Bahasa Inggeris","year":"Tahun 4","lesson_no":29}))
        self.assertFalse(_is_english_y4_l29({"subject":"English","year":"Year 3","lesson_no":29}))
        self.assertFalse(install(SimpleNamespace()))

    def test_launcher_installs_after_l30_and_no_db_or_credit_changes(self):
        src=(ROOT/"tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        self.assertIn("ENGLISH_Y4_L029_CLIL3_AUDIO_GUARD_ACTIVE",src)
        self.assertGreater(src.rfind("install_y4_l029_audio_guard(telegram_runtime)"),
                           src.rfind("install_y4_l030_audio_guard(telegram_runtime)"))
        guard=(ROOT/"web/english_y4_l029_audio_guard.py").read_text(encoding="utf-8")
        for forbidden in ("supabase","INSERT INTO","UPDATE ","sendAudio","_rph_rows ="):
            self.assertNotIn(forbidden,guard)

if __name__=="__main__":
    unittest.main()
