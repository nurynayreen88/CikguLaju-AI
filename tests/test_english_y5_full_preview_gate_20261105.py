"""Year5 complete runtime safety inventory; no bot/DB/external calls.

This checks the currently installed 151 fixed-SOW preview RPH and nine
teacher-choice suggestions, NOT pedagogical approval or live Telegram delivery.
"""
import unittest

from web.english_y5_fixed_draft_preview_runtime import preview_rows
from web.english_y5_teacher_choice_runtime import adapt_rows as choice_rows
from web.english_y5_standalone_runtime import (
    CHOICE_LESSONS, _gate, LESSON_ROOT, approved_for_telegram,
)

STANDARD_KEYS = (
    "MAIN CONTENT STANDARD", "MAIN LEARNING STANDARD",
    "COMPLEMENTARY CONTENT STANDARD", "COMPLEMENTARY LEARNING STANDARD",
)
PRESERVE = ("TARIKH", "HARI", "MASA", "KELAS", "BILANGAN MURID", "REFLEKSI")
START = {
    "TAJUK": "GENERIC OLD", "SET INDUKSI": "GENERIC OLD",
    "AKTIVITI UTAMA": "GENERIC OLD", "PENTAKSIRAN": "GENERIC OLD",
    "PENUTUP": "GENERIC OLD", "OBJEKTIF PEMBELAJARAN": "GENERIC OLD",
    "BAHAN BANTU MENGAJAR": "GENERIC OLD", 
    "TARIKH": "05/11/2026", "HARI": "Thursday", "MASA": "08:00–09:00",
    "KELAS": "5 Amanah", "BILANGAN MURID": "30", "REFLEKSI": "Teacher's text",
}

def state(n, **overrides):
    result={"subject":"English","year":"Year 5","lesson_no":n,"task":"rph"}
    result.update(overrides)
    return result

class Year5FinalisationGate(unittest.TestCase):
    def test_all_160_source_lesson_previews_151_fixed_and_9_teacher_choice(self):
        sow = _gate(LESSON_ROOT)
        self.assertIsInstance(sow, dict)
        self.assertEqual(set(sow), {str(x) for x in range(1,161)})
        self.assertEqual(len(CHOICE_LESSONS),9)
        fixed,selected=set(),set()
        for number in range(1,161):
            with self.subTest(lesson=number):
                original=dict(START)
                rec=sow[str(number)]
                self.assertFalse(approved_for_telegram(number))
                if number in CHOICE_LESSONS:
                    self.assertTrue(rec["teacher_choice"])
                    self.assertIsNone(rec["main_ls"])
                    self.assertIsNone(rec["complementary_ls"])
                    self.assertIs(preview_rows(state(number), original), original)
                    output=choice_rows(state(number),original)
                    self.assertIsNot(output,original)
                    self.assertIn("DRAF",output["TAJUK"])
                    for key in STANDARD_KEYS:
                        self.assertIn("Teacher to choose",output[key])
                    selected.add(number)
                else:
                    self.assertIs(rec["teacher_choice"], False)
                    self.assertIs(choice_rows(state(number),original),original)
                    output=preview_rows(state(number),original)
                    self.assertIsNot(output,original)
                    self.assertEqual(output["MAIN LEARNING STANDARD"],rec["main_ls"])
                    self.assertEqual(output["COMPLEMENTARY LEARNING STANDARD"],rec["complementary_ls"])
                    self.assertIn("DRAF",output["TAJUK"])
                    fixed.add(number)
                self.assertEqual(original, START)
                for key in PRESERVE:
                    self.assertEqual(output[key], START[key])
                for key in ("TAJUK","AKTIVITI UTAMA","SET INDUKSI","PENTAKSIRAN","PENUTUP","OBJEKTIF PEMBELAJARAN"):
                    self.assertTrue(str(output.get(key) or "").strip(), (number,key))
                self.assertNotIn("GENERIC OLD", output["AKTIVITI UTAMA"])
                self.assertNotIn("QA status", output["AKTIVITI UTAMA"] + output["PENUTUP"])
        self.assertEqual(len(fixed),151)
        self.assertEqual(selected,set(CHOICE_LESSONS))

    def test_no_cross_subject_or_stale_lesson_code_override(self):
        for n in (14,88):
            original=dict(START)
            cases=(
                state(n,year="Year 4"),state(n,subject="Mathematics"),
                state(n,task="worksheet"),state(n,lesson_no=True),
                state(n,lesson_no="999"),
            )
            for value in cases:
                with self.subTest(state=value):
                    self.assertIs(preview_rows(value,original),original)
                    self.assertIs(choice_rows(value,original),original)

        # A teacher-choice Lesson has no official fixed SOW code. The
        # proposal adapter is deliberately allowed to replace *stale*
        # upstream skill fields with a pending-teacher-selection notice,
        # but must never print the stale numeric value as official.
        invalid=state(88,sp_code="9.9.9")
        self.assertIs(preview_rows(invalid,START), START)
        safe=choice_rows(invalid,START)
        self.assertIsNot(safe,START)
        self.assertIn("DRAF",safe["TAJUK"])
        for key in STANDARD_KEYS:
            self.assertIn("Teacher to choose",safe[key])
            self.assertNotIn("9.9.9",safe[key])


if __name__ == "__main__":
    unittest.main()
