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

    def test_quick_material_telegram_lesson_resolved_from_native_db_reader(self):
        native = [{"pdp_sequence_code":"X-014","source_sequence_no":14,
                   "sk_code":"1.7","sp_code":"1.7.2"}]
        calls=[]
        def reader(year,subject):
            calls.append((year,subject))
            return native
        runtime=SimpleNamespace(_sm2542_rows=reader,
                                _rph_rows=lambda ss,*a,**k:{"KELAS":"4 Jaya"})
        telegram = dict(state(),task="quick_material",pdp_sequence_code="X-014")
        telegram.pop("source_sequence_no")
        telegram.pop("pdp_no")
        with patch.dict(os.environ,ENV):
            self.assertTrue(m.install(runtime))
            rows=runtime._rph_rows(telegram)
            self.assertEqual(rows["TAJUK"],"Operasi bergabung darab dan bahagi")
            self.assertEqual(rows["STANDARD PEMBELAJARAN"].split(" — ")[0],"1.7.2")
            self.assertEqual(calls,[("Tahun 4","Matematik")])
            self.assertNotIn("source_sequence_no",telegram)
            # Renderer may change task to rph while keeping the same PdP
            # identity; it must resolve the missing sequence number too.
            as_rph=dict(telegram,task="rph")
            again=runtime._rph_rows(as_rph)
            self.assertEqual(again["STANDARD PEMBELAJARAN"].split(" — ")[0],"1.7.2")
            self.assertEqual(len(calls),2)

    def test_quick_material_renders_with_resolved_native_pdp_identity(self):
        # The previous Word/PDF row engine must receive the *verified* Lesson
        # number, not the original Telegram callback with only an opaque code.
        seen=[]
        def previous(s,*args,**kwargs):
            seen.append(dict(s))
            if s.get("source_sequence_no") != 14 or s.get("pdp_no") != 14:
                raise AssertionError("Native Word/PDF engine received an unresolved lesson")
            return {"KELAS":"4 Amanah","TARIKH":"08/11/2026"}
        runtime=SimpleNamespace(
            _sm2542_rows=lambda year, subject:[{
                "pdp_sequence_code":"verified-T4-L014",
                "source_sequence_no":14,"sk_code":"1.7","sp_code":"1.7.2"
            }],
            _rph_rows=previous)
        callback=dict(state(),task="quick_material",
                      pdp_sequence_code="verified-T4-L014")
        callback.pop("source_sequence_no")
        callback.pop("pdp_no")
        with patch.dict(os.environ,ENV):
            self.assertTrue(m.install(runtime))
            result=runtime._rph_rows(callback)
        self.assertEqual(result["STANDARD PEMBELAJARAN"].split(" — ")[0],"1.7.2")
        self.assertEqual(seen[0]["source_sequence_no"],14)
        self.assertEqual(seen[0]["pdp_no"],14)
        self.assertNotIn("source_sequence_no",callback)

    def test_telegram_quick_material_ambiguous_or_wrong_source_fails_closed(self):
        telegram=dict(state(),task="quick_material",pdp_sequence_code="X-014")
        telegram.pop("source_sequence_no");telegram.pop("pdp_no")
        options=[
            [{"pdp_sequence_code":"X-014","source_sequence_no":14,"sk_code":"1.7","sp_code":"1.7.2"},
             {"pdp_sequence_code":"X-014","source_sequence_no":15,"sk_code":"1.7","sp_code":"1.7.2"}],
            [{"pdp_sequence_code":"X-014","source_sequence_no":14,"sk_code":"1.7","sp_code":"1.7.2"},
             {"pdp_sequence_code":"X-014","source_sequence_no":14,"sk_code":"1.7","sp_code":"1.7.3"}],
            [],
        ]
        with patch.dict(os.environ,ENV):
            for rows in options:
                runtime=SimpleNamespace(_sm2542_rows=lambda y,s:rows)
                with self.subTest(rows=rows), self.assertRaises(m.MathematicsRPHUnavailable):
                    m.resolve_native_state(runtime,telegram)

    def test_source_without_valid_heading_rejected(self):
        t=get_lesson(2,1)
        with self.assertRaises(m.MathematicsRPHUnavailable):
            m.parse_lesson(t.replace("Lesson 001","Lesson 011",1),2,1)
        with self.assertRaises(m.MathematicsRPHUnavailable):
            m.parse_lesson(t.replace("**SP:** 1.1.1", "**SP:** 2.1.1", 1),2,1)

if __name__ == "__main__":
    unittest.main()
