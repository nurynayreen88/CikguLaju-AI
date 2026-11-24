"""Regression controls for second set of editorial Jawi closing proposals."""
import hashlib
import unittest
from pi_closing_jawi_candidates_batch2 import generate, ADDITIONAL
from pi_closing_jawi_candidates import CANDIDATES
from pi_closing_jawi_review_queue import build


class PIClosingJawiBatch2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate()

    def test_exact_source_text_mapping_and_coverage(self):
        r = self.data
        self.assertEqual(r["candidate_groups"], 23)
        self.assertEqual(len(ADDITIONAL), 13)
        self.assertEqual(len(CANDIDATES), 10)
        self.assertEqual(r["candidate_covered_lesson_occurrences"], 635)
        self.assertEqual(r["remaining_without_candidate"], 55)
        self.assertEqual(r["all_draft_closings"], 690)
        self.assertEqual(r["unique_source_closings"], 78)
        self.assertEqual([x["original_closing_rumi"] for x in r["records"]],
                         [x["original_closing_rumi"] for x in build()["groups"][:23]])
        self.assertEqual(len(set(x["group_id"] for x in r["records"])), 23)

    def test_all_originals_preserved_zero_approvals(self):
        self.assertEqual(self.data["approved"], 0)
        self.assertIs(self.data["can_publish"], False)
        self.assertIsNone(self.data["academic_quality_percent"])
        self.assertEqual(self.data["release"], "NO_GO")
        for x in self.data["records"]:
            self.assertEqual(x["original_text_sha256"],
                             hashlib.sha256(x["original_closing_rumi"].encode("utf-8")).hexdigest())
            self.assertTrue(x["candidate_jawi_text"].strip())
            self.assertIsNone(x["jawi_reviewer"])
            self.assertIsNone(x["content_reviewer"])
            for status in ("jawi_spelling_verified", "source_sp_verified",
                           "word_pdf_verified", "approved", "can_publish"):
                self.assertIs(x[status], False)
            self.assertEqual(x["release"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
