"""Keep T2 TOC evidence distinct from Lesson-to-page academic certification."""
import unittest
from pi_t2_textbook_toc_review import audit, bounded_end, BAD_END_IDS


class PIYear2OriginalTocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_book_endpoints_and_lesson_counts(self):
        r = self.result
        self.assertEqual(r["notes_checked"], 77)
        self.assertEqual(r["distinct_source_notes"], 18)
        self.assertEqual(r["ranges_consistent_with_toc_starts"], 74)
        self.assertEqual(r["out_of_book_end_page_claims"], 3)
        self.assertEqual(set(r["out_of_book_end_lesson_ids"]), BAD_END_IDS)
        self.assertEqual(r["source_toc_pdf_pages_observed"], [5, 6])
        self.assertEqual(r["final_visible_numbered_content_pdf_page"], 148)
        self.assertEqual(r["final_visible_printed_page"], 138)
        self.assertEqual(bounded_end(133), 138)
        self.assertEqual(bounded_end(49), 54)
        self.assertEqual(bounded_end(85), 90)

    def test_original_notes_kept_and_absent_pages_never_offered_to_teacher(self):
        r = self.result
        self.assertIs(r["source_book_read_again_in_ci"], False)
        self.assertIsNone(r["academic_quality_percent"])
        self.assertEqual(r["specific_lesson_page_verified"], 0)
        self.assertEqual(r["corrections_approved"], 0)
        self.assertIs(r["can_publish"], False)
        self.assertEqual(r["release"], "NO_GO")
        for row in r["rows"]:
            self.assertTrue(row["source_note"])
            self.assertEqual(len(row["source_note_sha256"]), 64)
            for key in ("specific_sp_and_page_verified", "direct_book_page_activity_verified",
                        "copyright_permission_to_distribute", "content_expert_approved",
                        "can_publish"):
                self.assertIs(row[key], False)
            self.assertEqual(row["release"], "NO_GO")
            if row["id"] in BAD_END_IDS:
                self.assertEqual((row["claimed_start"], row["claimed_end"]), (133, 140))
                self.assertEqual(row["toc_bounded_end"], 138)
                self.assertIs(row["requires_editor_range_fix"], True)
            else:
                self.assertIs(row["claimed_range_matches_toc_bounds"], True)


if __name__ == "__main__":
    unittest.main()
