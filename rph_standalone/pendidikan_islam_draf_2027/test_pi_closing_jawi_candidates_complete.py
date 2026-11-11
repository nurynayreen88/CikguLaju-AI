"""Complete 690/690 editor-only Jawi closure candidates, never auto-publish."""
import hashlib
import unittest
from pi_closing_jawi_candidates_complete import generate, REMAINING
from pi_closing_jawi_review_queue import build


class PIClosingJawiCompleteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = generate()

    def test_every_original_closing_has_exact_candidate(self):
        q = build()
        r = self.result
        self.assertEqual(r["candidate_groups"], 78)
        self.assertEqual(r["unique_source_closings"], 78)
        self.assertEqual(r["all_draft_closings"], 690)
        self.assertEqual(r["candidate_covered_lesson_occurrences"], 690)
        self.assertEqual(r["remaining_without_candidate"], 0)
        self.assertEqual(len(REMAINING), 55)
        self.assertEqual(
            [x["original_closing_rumi"] for x in r["records"]],
            [x["original_closing_rumi"] for x in q["groups"]],
        )
        self.assertEqual(len(set(x for y in r["records"] for x in y["lesson_ids"].split("|"))), 690)

    def test_candidate_does_not_replace_rumi_or_claim_approval(self):
        r = self.result
        self.assertEqual(r["approved"], 0)
        self.assertEqual(r["jawi_spelling_verified"], 0)
        self.assertIs(r["can_publish"], False)
        self.assertIsNone(r["academic_quality_percent"])
        self.assertEqual(r["release"], "NO_GO")
        for x in r["records"]:
            self.assertEqual(x["original_text_sha256"],
                             hashlib.sha256(x["original_closing_rumi"].encode("utf-8")).hexdigest())
            self.assertTrue(x["candidate_jawi_text"].strip())
            self.assertIsNone(x["jawi_reviewer"])
            self.assertIsNone(x["content_reviewer"])
            for k in ("jawi_spelling_verified", "source_sp_verified",
                      "word_pdf_verified", "approved", "can_publish"):
                self.assertIs(x[k], False)
            self.assertEqual(x["release"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
