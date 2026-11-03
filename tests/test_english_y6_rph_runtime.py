"""Year 6 2027 RPH runtime safety and rendering contract tests.

Never imports production app.py or alters any user credits.
"""
import types
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from web.english_y6_standalone_runtime import adapt_rows, install, load_lesson


def dummy_source(num, main="3.2/3.2.1", complementary="4.2/4.2.4"):
    return (f"# English Year 6 — Lesson {num:03d}: Welcome (Reading 1)\n\n"
            f"**Main CS/LS:** {main}  \n"
            f"**Complementary CS/LS:** {complementary}  \n"
            "**Learning objective:** Identify 5 facts accurately.  \n"
            "**PBD evidence:** Five independent answers.  \n"
            "**Materials:** Academy Stars Year 6 PB p.4, TB p.18.  \n"
            "**Topic:** Welcome  \n"
            "**Teacher reflection:** ___/___\n"
            "## Set induction (5 minutes)\n**Teacher:** Show cards.  \n**Pupils:** Predict.\n"
            "## Activity 1 — Prepare (10 minutes)\n**Teacher:** Activate knowledge.  \n**Pupils:** Respond.\n"
            "## Activity 2 — Core (18 minutes)\n**Teacher:** Guide reading.  \n**Pupils:** Read.\n"
            "## Activity 3 — Apply (15 minutes)\n**Teacher:** Monitor.  \n**Pupils:** Compare.\n"
            "## Reinforcement / PBD (8 minutes)\n**Teacher:** Check.  \n**Pupils:** Correct.\n"
            "## Closure (4 minutes)\n**Teacher:** Summarise.  \n**Pupils:** Share.\n"
            "## Differentiation and follow-up\nSupport with visuals.\n")


class Y6RPHReleaseTests(unittest.TestCase):
    def test_all_160_existing_sources_parse(self):
        for n in range(1, 161):
            with self.subTest(n=n):
                self.assertIsNotNone(load_lesson(n))

    def test_exact_rph_fields_from_year6(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "lesson_001.md").write_text(dummy_source(1), encoding="utf-8")
            overlay={"version":"y6-sow-20261103","fixed_standard_lessons":146,
                     "lessons":{"1":{"main_ls":"3.2.1","complementary_ls":"4.2.4",
                     "objective":"Identify the main idea of the text",
                     "pbd_evidence":"Annotated answers","sow_pupil_book_exercises":"1",
                     "induction":{"teacher":"Show visuals","pupils":"Predict"},
                     "activities":[{"teacher":"Explain the story","pupils":"Read"},
                                   {"teacher":"Guide main idea","pupils":"Identify main idea"},
                                   {"teacher":"Check answers","pupils":"Give evidence"}],
                     "closure":{"teacher":"Reflect","pupils":"Share"}}}}
            (Path(tmp) / "sow_task_overlay_2027.json").write_text(json.dumps(overlay), encoding="utf-8")
            state={"year":"Tahun 6","subject":"Bahasa Inggeris","lesson_no":1,"sp_code":"3.2.1"}
            rows=adapt_rows(state,{"OBJEKTIF PEMBELAJARAN":"generic","TARIKH":"03/11"},root=tmp)
        self.assertIn("Identify the main idea",rows["OBJEKTIF PEMBELAJARAN"])
        self.assertIn("Academy Stars",rows["BAHAN BANTU MENGAJAR"])
        self.assertIn("Guide main idea",rows["AKTIVITI UTAMA"])
        self.assertIn("Teacher:",rows["AKTIVITI UTAMA"])
        self.assertIn("Pupils:",rows["AKTIVITI UTAMA"])
        self.assertEqual(rows["TARIKH"],"03/11")
        self.assertIn("Main: 3.2.1",rows["STANDARD PEMBELAJARAN"])

    def test_other_years_and_other_subject_preserved(self):
        rows={"OBJEKTIF PEMBELAJARAN":"untouched"}
        for state in [{"year":"Tahun 5","subject":"English","lesson_no":1},
                      {"year":"Tahun 6","subject":"Matematik","lesson_no":1},
                      {"year":"Tahun 6","subject":"English","lesson_no":0},
                      {"year":"Tahun 6","subject":"English","lesson_no":161},
                      {"year":"Tahun 6","subject":"English"}]:
            self.assertIs(adapt_rows(state,rows),rows)

    def test_official_sow_overlay_covers_146_fixed_lessons_only(self):
        root = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year6"
        content = json.loads((root / "sow_task_overlay_2027.json").read_text(encoding="utf-8"))
        self.assertEqual(content["version"], "y6-sow-20261103")
        self.assertEqual(len(content["lessons"]), 146)
        choices = {16,32,48,64,80,96,112,128,144,155,156,157,158,160}
        self.assertTrue(choices.isdisjoint({int(key) for key in content["lessons"]}))
        for key, entry in content["lessons"].items():
            num = int(key)
            record = load_lesson(num)
            self.assertIsNotNone(record)
            self.assertEqual(entry["main_ls"], record[0]["main cs/ls"].split("/")[-1])
            self.assertEqual(entry["complementary_ls"], record[0]["complementary cs/ls"].split("/")[-1])
            self.assertEqual(len(entry["activities"]), 3)
            self.assertTrue(entry["objective"].startswith("By the end"))
            self.assertTrue(all("teacher" in activity and "pupils" in activity for activity in entry["activities"]))

    def test_missing_overlay_fails_closed_to_existing_rows(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "lesson_001.md").write_text(dummy_source(1), encoding="utf-8")
            old = {"OBJEKTIF PEMBELAJARAN":"prior plan"}
            state = {"year":"Tahun 6","subject":"English","lesson_no":1,"sp_code":"3.2.1"}
            self.assertIs(adapt_rows(state,old,root=tmp),old)

    def test_mismatched_learning_standard_fails_closed(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "lesson_001.md").write_text(dummy_source(1), encoding="utf-8")
            source={"year":"Tahun 6","subject":"English","lesson_no":1,"sp_code":"1.2.2"}
            previous={"PENTAKSIRAN":"preserve"}
            self.assertIs(adapt_rows(source,previous,root=tmp),previous)

    def test_no_fake_standard_for_teacher_selected(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp) / "lesson_016.md"
            path.write_text(dummy_source(16,"PILIHAN GURU (SOW)","PILIHAN GURU (SOW)"),encoding="utf-8")
            rows=adapt_rows({"year":"Tahun 6","subject":"English","lesson_no":16},{},root=tmp)
            self.assertIn("Teacher-selected",rows["STANDARD PEMBELAJARAN"])
            self.assertNotIn("3.2.1",rows["STANDARD PEMBELAJARAN"])

    def test_install_keeps_original_webhook_and_credits(self):
        original=lambda st,*a,**kw:{"OBJEKTIF PEMBELAJARAN":"original","TARIKH":"xx"}
        runtime=types.SimpleNamespace(_rph_rows=original, callback=lambda *a:"ok", _credit_gate=lambda *a:True)
        self.assertTrue(install(runtime))
        self.assertTrue(install(runtime))
        self.assertEqual(runtime.callback(1, "home"), "ok")
        self.assertTrue(runtime._credit_gate(1))
        self.assertEqual(runtime._rph_rows({"subject":"BM","year":"Tahun 6"},1)["OBJEKTIF PEMBELAJARAN"],"original")


if __name__ == "__main__":
    unittest.main()
