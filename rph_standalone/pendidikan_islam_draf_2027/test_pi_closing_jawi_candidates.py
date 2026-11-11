"""Conservative controls: 10 high-frequency Jawi editorial drafts, zero releases."""
import unittest
import hashlib

from pi_closing_jawi_candidates import generate, CANDIDATES
from pi_closing_jawi_review_queue import build


class PIClosingJawiCandidatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = generate()

    def test_coverage_matches_exact_source_groups(self):
        r = self.value
        self.assertEqual(r["all_draft_closings"], 690)
        self.assertEqual(r["unique_source_closings"], 78)
        self.assertEqual(r["candidate_groups"], 10)
        self.assertEqual(r["candidate_covered_lesson_occurrences"], 581)
        self.assertEqual(r["remaining_without_candidate"], 109)
        self.assertEqual(len(r["records"]), len(CANDIDATES))
        all_groups = build()["groups"]
        self.assertEqual(
            [x["original_closing_rumi"] for x in r["records"]],
            [x["original_closing_rumi"] for x in all_groups[:10]],
        )

    def test_candidates_never_replace_source_or_claim_approval(self):
        r = self.value
        self.assertEqual(r["approved"], 0)
        self.assertIs(r["can_publish"], False)
        self.assertIsNone(r["academic_quality_percent"])
        self.assertEqual(r["release"], "NO_GO")
        for row in r["records"]:
            self.assertEqual(
                hashlib.sha256(row["original_closing_rumi"].encode("utf-8")).hexdigest(),
                row["original_text_sha256"],
            )
            self.assertTrue(row["candidate_jawi_text"].strip())
            self.assertIsNone(row["jawi_reviewer"])
            self.assertIsNone(row["content_reviewer"])
            for key in ("jawi_spelling_verified", "source_sp_verified",
                        "word_pdf_verified", "approved", "can_publish"):
                self.assertIs(row[key], False)
            self.assertEqual(row["release"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
