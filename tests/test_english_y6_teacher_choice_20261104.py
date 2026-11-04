"""Regression for Year6 146 fixed + 14 teacher-choice SOW-native Word/PDF cells."""
import json
from pathlib import Path
import types
import unittest
from unittest.mock import patch

from web.english_y6_standalone_runtime import (
    adapt_rows, Y6_TEACHER_CHOICES, TEACHER_SELECTED_STANDARD,
    _official_y6_sow, _teacher_choice_sow, install,
)

ROOT = Path(__file__).resolve().parents[1]
SOW = json.loads((ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))["lessons"]
SAMPLE = {
    "TARIKH":"04/11/2026","KELAS":"6 Cekap","MASA":"08:00",
    "BILANGAN MURID":"31","REFLEKSI":"Notes entered by the teacher",
    "KUOTA":10,"TAJUK":"OLD GENERIC TITLE",
    "MAIN CONTENT STANDARD":"OLD CS",
    "MAIN LEARNING STANDARD":"OLD LS",
    "COMPLEMENTARY CONTENT STANDARD":"OLD COMP CS",
    "COMPLEMENTARY LEARNING STANDARD":"OLD COMP LS",
    "OBJEKTIF PEMBELAJARAN":"OLD OBJECTIVE",
    "PENTAKSIRAN":"OLD PBD",
}


class Year6OfficialSOWRows(unittest.TestCase):
    def test_all_14_teacher_choice_drafts_have_no_invented_standards(self):
        official = {n for n in range(1,161) if SOW[f"6/{n}"]["teacher_selected"]}
        self.assertEqual(official, Y6_TEACHER_CHOICES)
        for number in sorted(official):
            with self.subTest(lesson=number):
                sow = _teacher_choice_sow(number)
                self.assertIsNotNone(sow)
                previous = dict(SAMPLE)
                result = adapt_rows({"subject":"English","year":"Year 6",
                                     "lesson_no":number,"task":"rph"}, previous)
                self.assertIsNot(result, previous)
                self.assertEqual(previous,SAMPLE)
                self.assertIn("CADANGAN CIKGULAJU (DRAF)",result["TAJUK"])
                self.assertNotIn("OLD GENERIC TITLE",result["TAJUK"])
                for key in ("MAIN CONTENT STANDARD","MAIN LEARNING STANDARD",
                            "COMPLEMENTARY CONTENT STANDARD","COMPLEMENTARY LEARNING STANDARD",
                            "STANDARD KANDUNGAN","STANDARD PEMBELAJARAN"):
                    self.assertEqual(result[key],TEACHER_SELECTED_STANDARD)
                for key in ("SET INDUKSI","AKTIVITI UTAMA","PENTAKSIRAN","PENUTUP",
                            "OBJEKTIF PEMBELAJARAN","BAHAN BANTU MENGAJAR"):
                    self.assertTrue(result[key],(number,key))
                self.assertIn("Teacher:",result["AKTIVITI UTAMA"])
                self.assertIn("Pupils:",result["AKTIVITI UTAMA"])
                self.assertIn("Teacher:",result["PENTAKSIRAN"])
                self.assertIn("Pupils:",result["PENTAKSIRAN"])
                for key in ("TARIKH","KELAS","MASA","BILANGAN MURID","REFLEKSI","KUOTA"):
                    self.assertEqual(result[key],SAMPLE[key])

    def test_all_146_fixed_source_codes_and_sow_titles(self):
        passed = 0
        for number in range(1,161):
            sow = SOW[f"6/{number}"]
            if sow["teacher_selected"]:
                continue
            with self.subTest(lesson=number):
                state={"subject":"English","year":"Year 6","lesson_no":number,
                       "sp_code":sow["main_ls"],"comp_sp_code":sow["complementary_ls"]}
                original=dict(SAMPLE)
                result=adapt_rows(state,original)
                self.assertIsNot(result,original)
                self.assertEqual(result["MAIN LEARNING STANDARD"],sow["main_ls"])
                self.assertEqual(result["COMPLEMENTARY LEARNING STANDARD"],
                                 sow["complementary_ls"])
                self.assertIn(sow["topic"],result["TAJUK"])
                self.assertNotIn("OLD GENERIC TITLE",result["TAJUK"])
                self.assertEqual(result["REFLEKSI"],SAMPLE["REFLEKSI"])
                self.assertEqual(result["TARIKH"],SAMPLE["TARIKH"])
                passed += 1
        self.assertEqual(passed,146)
        print("Y6_FIXED_OFFICIAL_ROWS",passed,"Y6_TEACHER_CHOICE",len(Y6_TEACHER_CHOICES),flush=True)

    def test_fail_closed_if_sow_unavailable_or_changed(self):
        source={"subject":"English","year":"Year 6","lesson_no":16}
        with patch("web.english_y6_standalone_runtime._teacher_choice_sow",return_value=None):
            self.assertIs(adapt_rows(source,SAMPLE),SAMPLE)
        with patch("web.english_y6_standalone_runtime._official_y6_sow",return_value=None):
            self.assertIs(adapt_rows(source,SAMPLE),SAMPLE)
        with patch("web.english_y6_standalone_runtime._official_y6_sow",
                   return_value={"n":1,"topic":"Welcome","teacher_selected":False,
                                 "main_ls":"1.2.1","complementary_ls":"1.1.1"}):
            self.assertIs(adapt_rows({"subject":"English","year":"Year 6",
                                      "lesson_no":1},SAMPLE),SAMPLE)

    def test_cross_year_and_subject_isolation(self):
        for state in ({"subject":"English","year":"Year 1","lesson_no":16},
                      {"subject":"English","year":"Year 2","lesson_no":16},
                      {"subject":"English","year":"Year 3","lesson_no":16},
                      {"subject":"English","year":"Year 4","lesson_no":16},
                      {"subject":"English","year":"Year 5","lesson_no":16},
                      {"subject":"PJPK","year":"Year 6","lesson_no":16},
                      {"subject":"English","year":"Year 6","lesson_no":0},
                      {"subject":"English","year":"Year 6","lesson_no":161},
                      {"subject":"English","year":"Year 6","lesson_no":"../../16"},
                      {"subject":"English","year":"Year 6","lesson_no":True}):
            with self.subTest(state=state):
                self.assertIs(adapt_rows(state,SAMPLE),SAMPLE)

    def test_actual_teacher_reflection_is_never_overwritten(self):
        for number in (1,16,80,155,160):
            result=adapt_rows({"subject":"English","year":"Year 6",
                               "lesson_no":number},SAMPLE)
            self.assertEqual(result["REFLEKSI"],SAMPLE["REFLEKSI"])

    def test_installer_idempotent_preserves_credits(self):
        invocations=[]
        def old(state,*args,**kwargs):
            invocations.append(state.get("year"))
            return dict(SAMPLE)
        rt=types.SimpleNamespace(_rph_rows=old,_credit_gate=lambda *_:True,
                                  callback=lambda *_:"unchanged")
        self.assertTrue(install(rt))
        self.assertTrue(install(rt))
        r=rt._rph_rows({"subject":"English","year":"Year 6","lesson_no":160})
        self.assertIn("DRAF",r["TAJUK"])
        self.assertEqual(len(invocations),1)
        self.assertEqual(rt.callback(),"unchanged")
        self.assertTrue(rt._credit_gate())


if __name__=="__main__":
    unittest.main()
