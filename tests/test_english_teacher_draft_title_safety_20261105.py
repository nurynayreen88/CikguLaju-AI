"""Teacher-facing draft titles stay transparent without exposing internal review metadata."""
import unittest

from web.english_y4_pending_draft_preview_runtime import (
    PENDING, CHOICES, adapt_rows as year4_pending,
)
from web.english_y5_fixed_draft_preview_runtime import preview_rows as year5_fixed
from web.english_y5_standalone_runtime import CHOICE_LESSONS

BASE={
    "TAJUK":"legacy", "SET INDUKSI":"legacy", "AKTIVITI UTAMA":"legacy",
    "PENTAKSIRAN":"legacy", "PENUTUP":"legacy",
    "TARIKH":"05/11/2026", "KELAS":"5 Amanah", "REFLEKSI":"Teacher value",
}

class EnglishDraftTeacherFacingTitles(unittest.TestCase):
    def test_all_year4_pending_still_draft_no_internal_review_label(self):
        self.assertEqual(len(PENDING),11)
        for n in sorted(PENDING):
            with self.subTest(lesson=n):
                output=year4_pending(
                    {"subject":"English","year":"Year 4","lesson_no":n,"task":"rph"}, BASE)
                self.assertIsNot(output,BASE)
                self.assertIn("DRAF",output["TAJUK"])
                self.assertNotIn("SEMAKAN GURU",output["TAJUK"])
                self.assertNotIn("FINAL READY",output["TAJUK"])
                self.assertEqual(output["TARIKH"],BASE["TARIKH"])
                self.assertEqual(output["REFLEKSI"],BASE["REFLEKSI"])
                if n in CHOICES:
                    self.assertIn("Teacher to select",output["MAIN LEARNING STANDARD"])
                else:
                    self.assertEqual(n,30)
                    self.assertIn("AUDIO REFERENCE CONFLICT",output["BAHAN BANTU MENGAJAR"])
                    self.assertEqual(output["MAIN LEARNING STANDARD"],"4.3.2")

    def test_year5_all_151_fixed_titles_draft_no_internal_review_label(self):
        seen=0
        for n in range(1,161):
            if n in CHOICE_LESSONS:
                continue
            with self.subTest(lesson=n):
                output=year5_fixed(
                    {"subject":"English","year":"Year 5","lesson_no":n,"task":"rph"},BASE)
                self.assertIsNot(output,BASE)
                self.assertIn("DRAF",output["TAJUK"])
                self.assertNotIn("SEMAKAN GURU",output["TAJUK"])
                self.assertNotIn("FINAL READY",output["TAJUK"])
                self.assertEqual(output["TARIKH"],BASE["TARIKH"])
                self.assertEqual(output["REFLEKSI"],BASE["REFLEKSI"])
                seen+=1
        self.assertEqual(seen,151)

if __name__=="__main__":
    unittest.main()
