"""Year 4 (11 gaps) + Year 5 (151 fixed) draft source-to-Word/PDF audit.

Proves no invented SOW codes, user state/credit mutation, other-year
overlay or FINAL READY status. All sources are already in GitHub.
No app.py import, external network, teacher records or DB writes.
"""
import json
from pathlib import Path
import types
import unittest

from web.english_y4_standalone_runtime import load_release_candidate, adapt_rows as y4_verified
from web.english_y4_pending_draft_preview_runtime import (
    PENDING, CHOICES, AUDIO_CONFLICT, PROJECTS,
    adapt_rows as y4_preview, install as install_y4,
)
from web.english_y5_standalone_runtime import (
    CHOICE_LESSONS, LESSON_ROOT, load_lesson, approved_for_telegram,
    adapt_rows as y5_existing,
)
from web.english_y5_fixed_draft_preview_runtime import (
    preview_rows as y5_preview, install as install_y5,
)
from web.english_y5_teacher_choice_runtime import adapt_rows as y5_choices

ROOT = Path(__file__).resolve().parents[1]
BASE = {"TARIKH":"04/11/2026", "HARI":"Wednesday",
        "MASA":"08:00", "KELAS":"5 Cemerlang","BILANGAN MURID":"32",
        "REFLEKSI":"Original teacher notes", "KUOTA":10,
        "MAIN LEARNING STANDARD":"Old generic code",
        "COMPLEMENTARY LEARNING STANDARD":"Old generic complementary",
        "OBJEKTIF PEMBELAJARAN":"Generic objective",
        "AKTIVITI UTAMA":"Generic activities"}
SOW=json.loads((ROOT/"rph_standalone/english/year5/sow_standard_gate_2027.json").read_text(encoding="utf-8"))


class EnglishY4Y5ReleaseCoverage(unittest.TestCase):
    def test_all_y4_11_gaps_are_explicitly_source_backed_drafts(self):
        self.assertEqual(PENDING, {16,30,32,48,64,80,96,112,128,144,160})
        passed=[]
        for number in sorted(PENDING):
            state={"subject":"English","year":"Tahun 4","lesson_no":number,"task":"rph"}
            old=dict(BASE)
            rows=y4_preview(state,old)
            with self.subTest(number=number):
                self.assertIsNot(rows,old)
                self.assertEqual(old, BASE)
                self.assertIn("DRAF",rows["TAJUK"])
                self.assertNotIn("Generic activities",rows["AKTIVITI UTAMA"])
                for k in ("SET INDUKSI","AKTIVITI UTAMA","PENTAKSIRAN",
                          "PENUTUP","OBJEKTIF PEMBELAJARAN","BAHAN BANTU MENGAJAR"):
                    self.assertTrue(rows.get(k), (number,k))
                self.assertIn("Teacher:", rows["AKTIVITI UTAMA"])
                self.assertIn("Pupils:", rows["AKTIVITI UTAMA"])
                self.assertIn("Teacher:", rows["PENTAKSIRAN"])
                self.assertIn("Pupils:", rows["PENTAKSIRAN"])
                for k in ("TARIKH","HARI","MASA","KELAS","BILANGAN MURID","REFLEKSI","KUOTA"):
                    self.assertEqual(rows[k],BASE[k])
                if number in CHOICES:
                    self.assertIn("not fixed by SOW",rows["MAIN LEARNING STANDARD"])
                    self.assertIn("not fixed by SOW",rows["COMPLEMENTARY LEARNING STANDARD"])
                    self.assertNotRegex(rows["MAIN LEARNING STANDARD"],r"\d\.\d\.\d")
                else:
                    self.assertIn("AUDIO REFERENCE CONFLICT", rows["BAHAN BANTU MENGAJAR"])
                    self.assertIn("CD1",rows["BAHAN BANTU MENGAJAR"])
                    self.assertIn("CD2",rows["BAHAN BANTU MENGAJAR"])
                    self.assertEqual(rows["MAIN LEARNING STANDARD"],"4.3.2")
                    self.assertEqual(rows["COMPLEMENTARY LEARNING STANDARD"],"1.2.5")
                passed.append(number)
        self.assertEqual(len(passed),11)
        print("Y4_DRAFT_GAPS",len(passed),sorted(passed),flush=True)

    def test_all_y4_149_reviewed_lessons_preserved_without_preview(self):
        kept=[]
        for number in range(1,161):
            if number in PENDING:
                continue
            with self.subTest(number=number):
                self.assertIsNotNone(load_release_candidate(number))
                st={"subject":"English","year":"Year 4","lesson_no":number}
                self.assertIs(y4_preview(st,BASE),BASE)
                rendered=y4_verified(st,BASE)
                self.assertIsNot(rendered,BASE)
                kept.append(number)
        self.assertEqual(len(kept),149)
        print("Y4_FIXED_PROVISIONAL",len(kept),flush=True)

    def test_year5_all_151_fixed_standard_drafts_cover_native_rph_fields(self):
        mapped=[]
        for number in range(1,161):
            rec=SOW["lessons"][str(number)]
            if number in CHOICE_LESSONS:
                continue
            with self.subTest(number=number):
                self.assertFalse(rec["teacher_choice"])
                self.assertIsNotNone(load_lesson(number))
                state={"subject":"English","year":"Year 5","lesson_no":number,
                       "task":"rph","sp_code":rec["main_ls"],
                       "comp_sp_code":rec["complementary_ls"]}
                previous=dict(BASE)
                rendered=y5_preview(state,previous)
                self.assertIsNot(rendered,previous)
                self.assertEqual(previous,BASE)
                self.assertIn("DRAF",rendered["TAJUK"])
                self.assertEqual(rendered["MAIN LEARNING STANDARD"],rec["main_ls"])
                self.assertEqual(rendered["COMPLEMENTARY LEARNING STANDARD"],
                                 rec["complementary_ls"])
                for k in ("SET INDUKSI","AKTIVITI UTAMA","PENTAKSIRAN",
                          "PENUTUP","OBJEKTIF PEMBELAJARAN","BAHAN BANTU MENGAJAR"):
                    self.assertTrue(rendered.get(k),(number,k))
                    self.assertNotRegex(rendered[k],r"(?i)QA status:|NOT READY|internal audit")
                for k in ("TARIKH","HARI","MASA","KELAS","BILANGAN MURID","REFLEKSI","KUOTA"):
                    self.assertEqual(rendered[k],BASE[k])
                self.assertFalse(approved_for_telegram(number))
                mapped.append(number)
        self.assertEqual(len(mapped),151)
        print("Y5_151_FIXED_PREVIEW",len(mapped),flush=True)

    def test_y5_nine_teacher_choice_proposals_unchanged(self):
        for number in CHOICE_LESSONS:
            st={"subject":"English","year":"Tahun 5","lesson_no":number,"task":"rph"}
            self.assertIs(y5_preview(st,BASE),BASE)
            choice=y5_choices(st,BASE)
            self.assertIsNot(choice,BASE)
            self.assertIn("CADANGAN CIKGULAJU (DRAF)",choice["TAJUK"])
            self.assertIn("not fixed by SOW",choice["MAIN LEARNING STANDARD"])

    def test_mismatch_fail_closed_and_no_cross_year(self):
        for target in (y4_preview,y5_preview):
            for st in (
                {"subject":"Sains","year":"Tahun 5","lesson_no":1},
                {"subject":"English","year":"Tahun 1","lesson_no":30},
                {"subject":"English","year":"Tahun 2","lesson_no":30},
                {"subject":"English","year":"Tahun 3","lesson_no":30},
                {"subject":"English","year":"Tahun 6","lesson_no":30},
                {"subject":"English","year":"Tahun 5","lesson_no":0},
                {"subject":"English","year":"Tahun 4","lesson_no":"../../30"},
                {"subject":"English","year":"Tahun 5","lesson_no":True},
            ):
                self.assertIs(target(st,BASE),BASE)
        for year,n,fn,main,comp in (
            (4,30,y4_preview,"4.3.2","1.2.5"),
            (5,1,y5_preview,"1.2.1","3.2.1")):
            valid={"subject":"English","year":f"Year {year}","lesson_no":n,
                   "sp_code":main,"comp_sp_code":comp}
            self.assertIsNot(fn(valid,BASE),BASE)
            self.assertIs(fn({**valid,"sp_code":"9.9.9"},BASE),BASE)
            self.assertIs(fn({**valid,"comp_sp_code":"9.9.9"},BASE),BASE)
        self.assertIs(y4_preview({"subject":"English","year":"Year 4",
                                  "lesson_no":80,"task":"worksheet"},BASE),BASE)
        self.assertIs(y5_preview({"subject":"English","year":"Year 5",
                                  "lesson_no":1,"task":"worksheet"},BASE),BASE)

    def test_installs_are_idempotent_and_preserve_side_effects(self):
        calls=[]
        def previous(state,*args,**kwargs):
            calls.append((state["year"],state["lesson_no"]))
            return dict(BASE)
        runtime=types.SimpleNamespace(_rph_rows=previous,
                    callback=lambda *_:"unchanged",_debit=lambda *_:"none")
        self.assertTrue(install_y4(runtime))
        self.assertTrue(install_y5(runtime))
        self.assertTrue(install_y4(runtime))
        self.assertTrue(install_y5(runtime))
        for year,n in ((4,30),(4,80),(5,1),(5,88),(6,1)):
            out=runtime._rph_rows({"subject":"English","year":f"Year {year}",
                                   "lesson_no":n,"task":"rph"})
            if (year,n) in ((4,30),(4,80),(5,1)):
                self.assertIn("DRAF",out["TAJUK"])
        self.assertEqual(len(calls),5)
        self.assertEqual(runtime.callback(),"unchanged")
        self.assertEqual(runtime._debit(1),"none")

    def test_telegram_wsgi_and_native_word_pdf_share_row_contract(self):
        app=(ROOT/"app.py").read_text(encoding="utf-8")
        i=app.rfind("def _create_rph_word(")
        self.assertGreater(i,0)
        self.assertIn("rph = _rph_rows(s, ai_text)",app[i:i+250])
        for k in ("MAIN CONTENT STANDARD","MAIN LEARNING STANDARD",
                  "COMPLEMENTARY CONTENT STANDARD","COMPLEMENTARY LEARNING STANDARD"):
            self.assertIn(k,app[i:i+2700])
        self.assertIn("_rph_rows(s, ai_text)",app)
        wsgi=(ROOT/"tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        self.assertIn("install_y4_pending_drafts(telegram_runtime)",wsgi)
        self.assertIn("install_y5_fixed_preview(telegram_runtime)",wsgi)
        self.assertIn("install_english_y5_choices(telegram_runtime)",wsgi)


if __name__=="__main__":
    unittest.main()
