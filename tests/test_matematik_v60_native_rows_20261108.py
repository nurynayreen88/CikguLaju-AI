"""Native Telegram+Web Mathematics v60: no RPT/database/credit writes."""
import os
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from web import matematik_v60_native_rows as m
from rph_standalone.matematik.v60_source_loader import get_lesson, verify_all

ENV = {"CIKGULAJU_ENV":"staging", "CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED":"1"}


def state(year=4, lesson=14, sk="1.7", sp="1.7.2"):
    return {
        "task":"rph", "quick_material_flow":True,
        "subject":"Matematik","year":f"Tahun {year}",
        "pdp_sequence_code":f"MATH-{year}-{lesson:03d}",
        "source_sequence_no":lesson, "pdp_no":lesson,
        "sk_code":sk,"sp_code":sp,"selected_sp_codes":[sp],
        "rph_class":"4 Cemerlang","rph_date":"08/11/2026"
    }


class MathNativeV60(unittest.TestCase):
    def test_all_585_exact_full_source_parses(self):
        self.assertEqual(verify_all(),585)
        for year in range(2,7):
            for lesson in range(1,118):
                with self.subTest(year=year,lesson=lesson):
                    x=m.parse_lesson(get_lesson(year,lesson),year,lesson)
                    self.assertIn("_sp_code",x)
                    self.assertTrue(x["_pbd"])
                    self.assertTrue(x["BBM"])
                    self.assertTrue(x["Rujukan"])
                    self.assertTrue(x["Objektif"])

    def test_feature_flag_never_enabled_outside_staging(self):
        with patch.dict(os.environ,{"CIKGULAJU_ENV":"production","CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED":"1"}):
            self.assertFalse(m.is_enabled())
        with patch.dict(os.environ,{"CIKGULAJU_ENV":"staging","CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED":"0"}):
            self.assertFalse(m.is_enabled())

    def test_teacher_metadata_preserved_and_stable_sp(self):
        base={"KELAS":"4 Cemerlang","TARIKH":"08/11/2026",
              "MASA":"08:00 - 09:00","HARI":"Ahad","BILANGAN MURID":"30",
              "REFLEKSI":"Penilaian guru sebenar", "TAJUK":"Tajuk lama"}
        with patch.dict(os.environ,ENV):
            r=m.adapt_rows(state(),base)
        self.assertEqual(r["STANDARD PEMBELAJARAN"].split(" — ")[0],"1.7.2")
        self.assertIn("24 × 15 ÷ 6",r["SET INDUKSI"])
        self.assertIn("Aktiviti 1",r["AKTIVITI UTAMA"])
        self.assertIn("Aktiviti 2",r["AKTIVITI UTAMA"])
        self.assertIn("pentaksiran",r["AKTIVITI UTAMA"].lower())
        self.assertIn("Buku Teks Matematik Tahun 4",r["BAHAN BANTU MENGAJAR"])
        self.assertEqual(r["REFLEKSI"],"Penilaian guru sebenar")
        for key in ("KELAS","TARIKH","MASA","HARI","BILANGAN MURID"):
            self.assertEqual(r[key],base[key])
        self.assertEqual(base["TAJUK"],"Tajuk lama")

    def test_wrong_SP_never_falls_back_or_generates(self):
        with patch.dict(os.environ,ENV):
            with self.assertRaises(m.MathematicsRPHUnavailable):
                m.verify_state(state(sp="1.7.1"))
            with self.assertRaises(m.MathematicsRPHUnavailable):
                m.verify_state(state(lesson=118))
            with self.assertRaises(m.MathematicsRPHUnavailable):
                m.verify_state(dict(state(),source_sequence_no=15))
            with self.assertRaises(m.MathematicsRPHUnavailable):
                m.verify_state(dict(state(),selected_sp_codes=["1.7.2","1.7.3"]))
            with self.assertRaises(m.MathematicsRPHUnavailable):
                m.verify_state(dict(state(),pdp_sequence_code=""))

    def test_staging_install_only_and_other_subject_is_unchanged(self):
        calls=[]
        def previous(s,*a,**kw):
            calls.append(s)
            return {"KELAS":"4 Cemerlang","TARIKH":"08/11/2026","TAJUK":"Legacy"}
        runtime=SimpleNamespace(_rph_rows=previous)
        with patch.dict(os.environ,{"CIKGULAJU_ENV":"production","CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED":"1"}):
            self.assertFalse(m.install(runtime))
            self.assertIs(runtime._rph_rows,previous)
        with patch.dict(os.environ,ENV):
            self.assertTrue(m.install(runtime))
            self.assertTrue(m.install(runtime))
            normal={"task":"rph","year":"Tahun 4","subject":"Sains"}
            self.assertEqual(runtime._rph_rows(normal)["TAJUK"],"Legacy")
            self.assertEqual(runtime._rph_rows(state())["TAJUK"],"Operasi bergabung darab dan bahagi")
            with self.assertRaises(m.MathematicsRPHUnavailable):
                runtime._rph_rows(state(sp="1.7.1"))
        self.assertEqual(len(calls),2)

    def test_source_without_valid_heading_rejected(self):
        t=get_lesson(2,1)
        with self.assertRaises(m.MathematicsRPHUnavailable):
            m.parse_lesson(t.replace("Lesson 001","Lesson 011",1),2,1)
        with self.assertRaises(m.MathematicsRPHUnavailable):
            m.parse_lesson(t.replace("**SP:** 1.1.1", "**SP:** 2.1.1", 1),2,1)

if __name__ == "__main__":
    unittest.main()
