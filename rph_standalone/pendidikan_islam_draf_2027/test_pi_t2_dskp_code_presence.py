"""Regression: full Year 2 DSKP SP code inventory, without claiming text verification."""
import unittest
from pi_t2_dskp_code_presence import audit,indexed_codes


class PIYear2CodePresenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()

    def test_83_dskp_codes_and_81_coded_lessons(self):
        self.assertEqual(len(indexed_codes()),83)
        self.assertEqual(self.r["indexed_dskp_sp_codes"],83)
        self.assertEqual(self.r["draft_lessons"],111)
        self.assertEqual(self.r["coded_lessons_with_all_codes_present"],81)
        self.assertEqual(self.r["coded_lessons_with_unknown_code"],0)
        self.assertEqual(self.r["distinct_codes_used"],76)
        self.assertEqual(self.r["total_sp_code_occurrences"],192)
        self.assertEqual(indexed_codes()["5.4.3"],55)

    def test_tasmi_no_fabricated_three_level_sp(self):
        self.assertEqual(self.r["tasmi_verse_range_lessons_without_official_3_level_sp"],30)
        self.assertEqual(self.r["invented_official_sp_codes"],0)
        self.assertEqual(self.r["full_sp_wording_verified_lessons"],0)
        self.assertEqual(self.r["expert_approved_lessons"],0)
        self.assertIsNone(self.r["academic_quality_percent"])
        self.assertIs(self.r["ready"],False)
        self.assertEqual(self.r["release"],"NO_GO")
        tasmi=[r for r in self.r["rows"]
               if r["category"]=="QURAN_TASMI_VERSE_RANGE_NO_THREE_LEVEL_SP"]
        self.assertEqual(len(tasmi),30)
        for x in tasmi:
            self.assertEqual(x["sp_codes"],"")
            self.assertEqual(x["sp_pdf_pages"],"{}")
            self.assertIs(x["all_codes_present_in_original_dskp"],False)

    def test_all_lesson_source_claims_are_limited_to_code_presence(self):
        for row in self.r["rows"]:
            for key in ("source_sp_text_wording_verified","quran_verse_bounds_verified",
                        "curriculum_expert_approved","activity_book_pages_verified",
                        "ready"):
                self.assertIs(row[key],False)
            self.assertEqual(row["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
