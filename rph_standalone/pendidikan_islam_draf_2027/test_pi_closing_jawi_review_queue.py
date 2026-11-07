"""Non-destructive Jawi closing review grouping."""
import unittest
from pi_closing_jawi_review_queue import build


class PIClosingJawiReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = build()

    def test_all_690_closings_grouped_without_loss(self):
        r = self.result
        self.assertEqual(r["lesson_count"], 690)
        self.assertEqual(r["unique_closings"], 78)
        self.assertEqual(len(r["groups"]), 78)
        self.assertEqual(sum(x["lesson_count"] for x in r["groups"]), 690)
        self.assertEqual(len(set(
            x for g in r["groups"] for x in g["lesson_ids"].split("|")
        )), 690)

    def test_no_auto_jawi_and_no_false_approval(self):
        self.assertIs(self.result["can_publish"], False)
        self.assertIs(self.result["academic_quality_certified"], False)
        self.assertEqual(self.result["jawi_replacements_approved"], 0)
        for group in self.result["groups"]:
            self.assertIsNone(group["approved_jawi_text"])
            self.assertIsNone(group["academic_reviewer"])
            self.assertIsNone(group["jawi_reviewer"])
            self.assertIs(group["source_checked"], False)
            self.assertIs(group["word_pdf_verified"], False)
            self.assertIs(group["can_publish"], False)
            self.assertEqual(group["release"], "NO_GO")
            self.assertEqual(len(group["original_text_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
