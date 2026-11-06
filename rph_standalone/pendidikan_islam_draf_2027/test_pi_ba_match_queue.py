"""Book exercise recommendations stay editor-only until page and activity are verified."""
import unittest

from pi_ba_match_queue import (
    match_queue, NEEDS_PAGE, ORAL_PRIMARY, SOURCE_VIEWERS
)


class BookCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = match_queue()
        cls.rows = {r["id"]: r for r in cls.a["rows"]}

    def test_priority_is_not_fabricated_page_mapping(self):
        a = self.a
        self.assertEqual(a["screened_active_lessons"], 258)
        self.assertEqual(a["historic_broad_workbook_review_candidates"], 191)
        self.assertEqual(a["refined_page_review_candidates"], 174)
        self.assertEqual(a["oral_and_tasmi_no_forced_book"], 84)
        self.assertEqual(a["jawi_priority"], 73)
        self.assertEqual(a["confirmed_exercise_pages"], 0)
        self.assertEqual(a["approved_teacher_sentences"], 0)
        self.assertEqual(a["release"], "NO_GO")
        for row in self.rows.values():
            self.assertIn(row["book_viewer_reference"], SOURCE_VIEWERS.values())
            self.assertIsNone(row["book_printed_page"])
            self.assertIsNone(row["book_exercise_id"])
            self.assertIsNone(row["teacher_sentence"])
            self.assertIs(row["exercise_instruction_verified"], False)
            self.assertIs(row["match_to_sp_verified"], False)
            self.assertIs(row["teacher_material_approved"], False)
            self.assertIs(row["permission_to_mirror_pdf"], False)

    def test_jawi_priority_and_correct_learning_focus(self):
        jawi = [r for r in self.rows.values() if r["domain"] == "جاوي"]
        self.assertEqual(len(jawi), 73)
        self.assertTrue(all(r["disposition"] == NEEDS_PAGE for r in jawi))
        self.assertTrue(all(r["priority"] == "P1_JAWI" for r in jawi))
        self.assertIn("JAWI", self.rows["T2-L003"]["learning_focus"])
        self.assertIn("JAWI", self.rows["T3-L004"]["learning_focus"])

    def test_recitation_hafazan_tasmi_not_replaced_by_worksheet(self):
        self.assertEqual(self.rows["T2-L001"]["disposition"], ORAL_PRIMARY)
        self.assertEqual(self.rows["T2-L026"]["disposition"], ORAL_PRIMARY)
        self.assertEqual(self.rows["T3-L001"]["disposition"], ORAL_PRIMARY)
        self.assertEqual(self.rows["T3-L009"]["disposition"], ORAL_PRIMARY)
        self.assertEqual(self.rows["T2-L080"]["disposition"], NEEDS_PAGE)
        self.assertEqual(self.rows["T3-L017"]["disposition"], NEEDS_PAGE)

    def test_preserve_year_and_active_only(self):
        self.assertNotIn("T2-L035", self.rows)
        self.assertTrue(all(r["year"] in (2,3) for r in self.rows.values()))
        self.assertEqual(len(self.rows), 258)


if __name__ == "__main__":
    unittest.main()
