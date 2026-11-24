"""Direct Year3 book unit references never become unverified exercise links."""
import unittest
from pi_t3_awalan_book_review import audit,READING,WRITING


class PIYear3AwalanSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()

    def test_source_book_pages_and_wrong_pdf34_page(self):
        v=self.r
        self.assertEqual(v["year3_awalan_lessons_with_direct_book_unit_reference"],12)
        self.assertEqual(v["year3_awalan_reading_lessons"],6)
        self.assertEqual(v["year3_awalan_writing_lessons"],6)
        self.assertEqual(v["book_pdf_spreads_inspected"],[31,32,33,34])
        self.assertEqual(v["book_printed_awalan_pages"],[46,47,48,49,50,51])
        self.assertEqual(v["legacy_pdf_page34_hints_wrong_next_unit"],6)
        self.assertEqual(len(READING|WRITING),12)
        self.assertEqual({r["id"] for r in v["rows"]},READING|WRITING)

    def test_review_only_no_false_confirmation(self):
        v=self.r
        self.assertEqual(v["specific_lesson_prefix_examples_approved"],0)
        self.assertEqual(v["dskp_full_text_verified"],0)
        self.assertEqual(v["expert_approved"],0)
        self.assertIs(v["can_publish"],False)
        self.assertEqual(v["release"],"NO_GO")
        for row in v["rows"]:
            self.assertIs(row["original_materials_preserved"],True)
            self.assertIs(row["exact_sk_sp_unchanged"],True)
            self.assertIs(row["source_footer_sp_code_observed"],True)
            self.assertIs(row["legacy_pdf_page34_wrong_unit"],row["id"] in READING)
            for key in ("specific_rph_prefix_examples_verified",
                        "textbook_exercise_or_pbd_approved","dskp_full_text_verified",
                        "jawi_orthography_approved","content_expert_approved",
                        "can_publish"):
                self.assertIs(row[key],False)
            self.assertEqual(row["release"],"NO_GO")


if __name__=="__main__":unittest.main()
