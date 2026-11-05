"""Year4 Super Minds1 wrong-book audio must never leak via stale callbacks."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from web.english_y4_wrong_book_audio_hold_20261105 import install,HOLD_LESSONS,_risk

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"audits/english_y4_wrong_book_audio_hold_manifest_20261105.json").read_text(encoding="utf-8"))

class WrongBookEnglishYear4AudioHold(unittest.TestCase):
    def _runtime(self):
        calls=[];notices=[]
        def avail(state):
            state["audio_storage_file_id"]="STALE_SUPER_MINDS1_AUDIO"
            return ["rph","rph_word","textbook","media","activity"]
        def selection(cid,ss,key):
            calls.append(("selection",cid,key))
            return True
        def direct(cid,ss,key):
            calls.append(("direct",cid,key))
            return True
        def mapping():
            return {
               29:[{"audio_reference":"CD1 Track 35"}],
               30:[{"audio_reference":"CD2 Track 29"}],
               103:[{"audio_reference":"CD2 Track 26"}],
               104:[{"audio_reference":"CD2 Track 27"}],
               2:[{"audio_reference":"CD1 Track 3"}]}
        rt=SimpleNamespace(
          _available_materials_v2528=avail,
          _send_reference_material_v2528=selection,
          _send_reference_material=direct,
          _EN4_AUDIO_ALL_V25257=mapping(),
          _EN4_AUDIO_ALL_V25258=mapping(),
          _EN4_AUDIO_ALL_V25259=mapping(),
          send=lambda cid,msg:notices.append((cid,msg)),
        )
        return rt,calls,notices

    def test_manifest_has_exactly_24_wrong_book_paths_in_19_year4_lessons(self):
        self.assertEqual(MANIFEST["lesson_count"],19)
        self.assertEqual(MANIFEST["route_count"],24)
        self.assertEqual({r["lesson"] for r in MANIFEST["rows"]},HOLD_LESSONS)
        self.assertEqual(len(MANIFEST["rows"]),24)
        self.assertEqual({r["parent_folder"] for r in MANIFEST["rows"]},
                         {"1tbbr7hbvZfbF3ZhxpIIdMAnLBR_MZS50",
                          "1EQxVxNqvyg-dKi_pLTtEomOFwuUTC-cv"})
        self.assertEqual(MANIFEST["expected_textbook"],"Get Smart Plus 4")
        self.assertEqual(MANIFEST["observed_source_textbook"],"Super Minds 1")

    def test_all_19_wrong_book_lessons_hide_media_but_preserve_rph_word_pdf(self):
        rt,calls,notices=self._runtime()
        self.assertTrue(install(rt))
        self.assertTrue(install(rt))
        for n in HOLD_LESSONS:
            with self.subTest(lesson=n):
                ss={"subject":"English","year":"Year 4","lesson_no":f"{n:03d}"}
                self.assertNotIn("media",rt._available_materials_v2528(ss))
                self.assertNotIn("audio_storage_file_id",ss)
                self.assertEqual(ss["audio_status"],"WRONG_BOOK_SUPER_MINDS1_YEAR4_MEDIA_HOLD")
                self.assertFalse(rt._send_reference_material_v2528(100,ss,"media"))
                self.assertFalse(rt._send_reference_material(100,ss,"media"))
                self.assertTrue(rt._send_reference_material_v2528(100,ss,"rph_word"))
                self.assertTrue(rt._send_reference_material_v2528(100,ss,"rph"))
                self.assertTrue(rt._send_reference_material_v2528(100,ss,"textbook"))
        self.assertEqual(len(notices),38)
        self.assertTrue(all("buku teks yang berbeza" in msg for _,msg in notices))
        self.assertEqual(len(calls),57)
        self.assertFalse(any(x[2]=="media" for x in calls))

    def test_all_maps_preserve_unaffected_year4_lessons(self):
        rt,calls,notices=self._runtime()
        before={key:dict(getattr(rt,key)) for key in
                ("_EN4_AUDIO_ALL_V25257","_EN4_AUDIO_ALL_V25258",
                 "_EN4_AUDIO_ALL_V25259")}
        self.assertTrue(install(rt))
        for name,old in before.items():
            now=getattr(rt,name)
            self.assertNotIn(29,now)
            self.assertNotIn(103,now)
            for n in (2,30,104):
                self.assertEqual(now[n],old[n])
        for year,subject,lesson in [
            ("Year 1","English",29),("Year 2","English",29),
            ("Year 3","English",29),("Year 5","English",29),
            ("Year 6","English",29),("Year 4","Mathematics",29),
            ("Year 4","English",30),("Year 4","English",104),
            ("Year 4","English",160),
        ]:
            ss={"subject":subject,"year":year,"lesson_no":lesson}
            self.assertIn("media",rt._available_materials_v2528(ss))
            self.assertTrue(rt._send_reference_material_v2528(100,ss,"media"))
            self.assertTrue(rt._send_reference_material(100,ss,"media"))
        self.assertEqual(len(calls),18)
        self.assertEqual(notices,[])
        self.assertTrue(_risk({"subject":"Bahasa Inggeris","year":"Tahun 4","lesson_no":97}))
        self.assertFalse(_risk({"subject":"Bahasa Inggeris","year":"Tahun 2","lesson_no":97}))

    def test_correct_book_wma_for_other_year_is_preserved_unchanged(self):
        """WMA is not forbidden: a correct-book Year2 file survives the Y4 source guard."""
        forwarded=[]
        def available(ss):
            return ["rph", "media", "textbook"]
        def sender(cid,ss,key):
            forwarded.append((cid,key,dict(ss)))
            return True
        runtime=SimpleNamespace(
            _available_materials_v2528=available,
            _send_reference_material_v2528=sender,
            _send_reference_material=sender,
            send=lambda cid,msg: None,
        )
        self.assertTrue(install(runtime))
        state={
            "subject":"English",
            "year":"Year 2",
            "lesson_no":26,
            "audio_filename":"CD2-35.wma",
            "audio_storage_file_id":"CORRECT_BOOK_ORIGINAL_WMA",
            "audio_mime_type":"audio/x-ms-wma",
        }
        before=dict(state)
        self.assertIn("media",runtime._available_materials_v2528(state))
        self.assertTrue(runtime._send_reference_material_v2528(100,state,"media"))
        self.assertTrue(runtime._send_reference_material(100,state,"media"))
        self.assertEqual(state,before)
        self.assertEqual([entry[1] for entry in forwarded],["media","media"])
        self.assertTrue(all(entry[2]==before for entry in forwarded))

    def test_guard_installed_only_after_existing_y4_l30_guard(self):
        launcher=(ROOT/"tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        self.assertIn("ENGLISH_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE",launcher)
        self.assertGreater(launcher.index("install_y4_wrong_book_audio_hold(telegram_runtime)"),
                           launcher.index("install_y4_l030_audio_guard(telegram_runtime)"))
        self.assertFalse(install(SimpleNamespace()))
        source=(ROOT/"web/english_y4_wrong_book_audio_hold_20261105.py").read_text(encoding="utf-8")
        for bad in ("supabase","sqlite3","INSERT INTO","UPDATE users","_use_credit","_debit_credit"):
            self.assertNotIn(bad,source)

if __name__=="__main__":
    unittest.main()
